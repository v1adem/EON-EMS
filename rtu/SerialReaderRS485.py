import logging

logger = logging.getLogger(__name__)

from pymodbus.client import ModbusSerialClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder

from register_maps.RegisterMaps import RegisterMap


def decode_data(data, property_specifications):
    decoded_data = 0

    if property_specifications["format"] == "float":
        decoded_data = decode_32bit_float(data)
    elif property_specifications["format"] == "U_WORD":
        decoded_data = data[0]
    elif property_specifications["format"] == "UD_WORD":
        decoded_data = (data[0] << 16) + data[1]
    elif property_specifications["format"] == "S_WORD":
        decoded_data = decode_16bit_signed(data)
    elif property_specifications["format"] == "SD_WORD":
        decoded_data = decode_32bit_signed(data)

    if "divider" in property_specifications:
        decoded_data /= property_specifications["divider"]

    return round(decoded_data, 2)


def decode_16bit_signed(data):
    return BinaryPayloadDecoder.fromRegisters(data, byteorder=Endian.BIG,
                                              wordorder=Endian.BIG).decode_16bit_int()


def decode_32bit_signed(data):
    return BinaryPayloadDecoder.fromRegisters(data, byteorder=Endian.BIG,
                                              wordorder=Endian.BIG).decode_32bit_int()


def decode_32bit_float(data):
    decoded_data = BinaryPayloadDecoder.fromRegisters(data, byteorder=Endian.BIG,
                                                      wordorder=Endian.BIG).decode_32bit_float()
    return decoded_data


class SerialReaderRS485:
    def __init__(self, device, project):
        self.port = project.port
        self.device_custom_name = device.name
        self.device_address = device.device_address
        self.register_map = RegisterMap.get_register_map(device.model)

        self.client = ModbusSerialClient(
            port=f"COM{project.port}", baudrate=project.baudrate, parity=project.parity,
            stopbits=project.stopbits, bytesize=project.bytesize, timeout=3, retries=2
        )

    def connect(self):
        try:
            return self.client.connect()
        except Exception as e:
            logger.error(f"{self.device_custom_name} - Connection error on port {self.port}: {str(e)}")
            return False

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

        # For IME
        sign_values = {}
        power_factor_sector_values = {}
        try:
            if not self.connect():
                logger.error(f"{self.device_custom_name} - No connection on port {self.port}")
                return {}

            grouped_registers = self.group_registers()

            for group in grouped_registers:
                start_address = group['start']
                total_length = group['length']
                try:
                    response = self.client.read_input_registers(
                        start_address, count=total_length, slave=self.device_address
                    )

                    if response.isError():
                        logger.error(f"{self.device_custom_name} - No response from {start_address} address")
                        return {}

                    registers_data = response.registers

                    current_idx_in_group = 0
                    for name, spec, length_in_registers in group['items']:
                        data_for_decode = registers_data[
                                          current_idx_in_group: current_idx_in_group + length_in_registers]

                        decoded_value = decode_data(data_for_decode, spec)

                        if decoded_value is not None:
                            if "sign_of_active_power" in name:
                                sign_values[name] = decoded_value
                            elif "sign_of_reactive_power" in name:
                                sign_values[name] = decoded_value
                            elif "power_factor_sector" in name:
                                power_factor_sector_values[name] = decoded_value
                            else:
                                result[name] = decoded_value
                        else:
                            result[name] = None

                        current_idx_in_group += length_in_registers

                except Exception as e:
                    logger.error(f"{self.device_custom_name} - No response from {start_address} address")
                    return {}

                for i in range(1, 4):
                    active_power_key = f"phase_{i}_active_power"
                    sign_key = f"phase_{i}_sign_of_active_power"

                    if active_power_key in result and sign_key in sign_values:
                        # Згідно з документацією (6): 0: positive, 1: negative
                        if sign_values[sign_key] == 1:
                            result[active_power_key] *= -1
                        del sign_values[sign_key]

                    # Для 3-фазної активної потужності
                if "3_phase_active_power" in result and "3_phase_sign_of_active_power" in sign_values:
                    if sign_values["3_phase_sign_of_active_power"] == 1:
                        result["3_phase_active_power"] *= -1
                    del sign_values["3_phase_sign_of_active_power"]

                for i in range(1, 4):
                    reactive_power_key = f"phase_{i}_reactive_power"
                    sign_key = f"phase_{i}_sign_of_reactive_power"

                    if reactive_power_key in result and sign_key in sign_values:
                        if sign_values[sign_key] == 1:
                            result[reactive_power_key] *= -1
                        del sign_values[sign_key]

                if "3_phase_reactive_power" in result and "3_phase_sign_of_reactive_power" in sign_values:
                    if sign_values["3_phase_sign_of_reactive_power"] == 1:
                        result["3_phase_reactive_power"] *= -1
                    del sign_values["3_phase_sign_of_reactive_power"]

                result.update(sign_values)
                result.update(power_factor_sector_values)

                return result

        except Exception as e:
            logger.error(f"{self.device_custom_name} - Неочікувана помилка при читанні: {str(e)}")
            return {}
        finally:
            try:
                self.client.close()
            except Exception as e:
                logger.error(f"{self.device_custom_name} - Помилка при закритті з'єднання: {str(e)}")
