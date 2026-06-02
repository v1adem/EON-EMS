import logging
import asyncio
from pymodbus.client import AsyncModbusSerialClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from register_maps.RegisterMaps import RegisterMap

logger = logging.getLogger(__name__)


def decode_data(data, property_specifications):
    decoded_data = 0
    if not data:
        return decoded_data

    if property_specifications["format"] == "float":
        decoded_data = BinaryPayloadDecoder.fromRegisters(data, byteorder=Endian.BIG,
                                                          wordorder=Endian.BIG).decode_32bit_float()
    elif property_specifications["format"] == "U_WORD":
        decoded_data = data[0]
    elif property_specifications["format"] == "UD_WORD":
        decoded_data = (data[0] << 16) + data[1]
    elif property_specifications["format"] == "S_WORD":
        decoded_data = BinaryPayloadDecoder.fromRegisters(data, byteorder=Endian.BIG,
                                                          wordorder=Endian.BIG).decode_16bit_int()
    elif property_specifications["format"] == "SD_WORD":
        decoded_data = BinaryPayloadDecoder.fromRegisters(data, byteorder=Endian.BIG,
                                                          wordorder=Endian.BIG).decode_32bit_int()

    if "divider" in property_specifications:
        decoded_data /= property_specifications["divider"]

    return round(decoded_data, 2)


class SerialReaderRS485:
    def __init__(self, device, project):
        self.port = project.port
        self.device_custom_name = device.name
        self.device_address = device.device_address
        self.register_map = RegisterMap.get_register_map(device.model)

        self.client = AsyncModbusSerialClient(
            port=self.port,
            baudrate=project.baudrate,
            parity=project.parity,
            stopbits=project.stopbits,
            bytesize=project.bytesize,
            timeout=1,
            retries=1
        )

    def group_registers(self):
        grouped = []
        sorted_registers = sorted(self.register_map.items(), key=lambda x: x[1]['register'])
        current_group = {'start': None, 'length': 0, 'items': []}

        for name, spec in sorted_registers:
            start = spec['register']
            length = 2 if spec['format'] in ["float", "UD_WORD", "SD_WORD"] else 1

            if current_group['start'] is None:
                current_group['start'] = start
                current_group['length'] = length
                current_group['items'].append((name, length))
            elif start == current_group['start'] + current_group['length']:
                current_group['length'] += length
                current_group['items'].append((name, length))
            else:
                grouped.append(current_group)
                current_group = {'start': start, 'length': length, 'items': [(name, length)]}

        if current_group['items']:
            grouped.append(current_group)

        return grouped

    async def read_all_properties(self):
        result = {}
        try:
            connected = await self.client.connect()
            if not connected:
                logger.error(f"{self.device_custom_name} - Cannot open port {self.port}")
                return {}

            grouped_registers = self.group_registers()

            for group in grouped_registers:
                start_address = group['start']
                total_length = group['length']

                try:
                    response = await self.client.read_input_registers(
                        start_address, count=total_length, slave=self.device_address
                    )

                    if response.isError():
                        logger.error(f"{self.device_custom_name} - Modbus error on address {start_address}")
                        return {}

                    registers = response.registers
                    idx = 0
                    for name, length in group['items']:
                        spec = self.register_map[name]
                        data = registers[idx: idx + length]
                        result[name] = decode_data(data, spec)
                        idx += length

                except Exception as e:
                    logger.error(f"{self.device_custom_name} - Error reading registers {start_address}: {e}")
                    return {}

            return result

        except Exception as e:
            logger.error(f"{self.device_custom_name} - Unexpected Modbus error: {e}")
            return {}
        finally:
            # Обов'язково закриваємо порт після виконання пакету читання
            try:
                await self.client.close()
            except Exception as e:
                logger.error(f"{self.device_custom_name} - Error closing port: {e}")