from datetime import datetime, timedelta
import logging

from tools.config import get_timezone

logger = logging.getLogger(__name__)

import pytz
from PySide6.QtWidgets import QMessageBox
from pymodbus.client import ModbusSerialClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder

from models.Device import Device
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
    def __init__(self, device_custom_name, device_name, port, device_address, baudrate, bytesize, parity, stopbits,
                 main_window):
        self.no_response_error_flag = False
        self.error_flag = False

        self.port = port
        self.main_window = main_window
        self.device_custom_name = device_custom_name
        self.device_address = device_address
        self.register_map = RegisterMap.get_register_map(device_name)

        self.client = ModbusSerialClient(
            port=f"{port}", baudrate=baudrate, parity=parity,
            stopbits=stopbits, bytesize=bytesize, timeout=0.5, retries=1
        )

    def connect(self):
        return self.client.connect()

    def group_registers(self):
        grouped = []
        sorted_registers = sorted(self.register_map.items(), key=lambda x: x[1]['register'])
        current_group = {'start': None, 'length': 0, 'items': []}

        for name, spec in sorted_registers:
            start = spec['register']
            length = 2 if spec['format'] in ["float", "UD_WORD", "SD_WORD"] else 1

            if current_group['start'] is None:  # Початок групи
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
        if self.connect():
            grouped_registers = self.group_registers()
            try:
                for group in grouped_registers:
                    start_address = group['start']
                    total_length = group['length']
                    response = self.client.read_input_registers(start_address, count=total_length,
                                                                slave=self.device_address)

                    if response.isError():
                        self.error_text = f"No response from {start_address}"
                        logger.error(self.error_text)
                        self.no_response_error_flag = True
                        continue

                    registers = response.registers
                    idx = 0
                    for name, length in group['items']:
                        spec = self.register_map[name]
                        data = registers[idx: idx + length]
                        result[name] = decode_data(data, spec)
                        idx += length

            except Exception as e:
                self.error_text = f"{e}"
                logger.error(self.error_text)
                self.error_flag = True
            finally:
                self.client.close()
        else:
            self.error_text = f"No connection on port - {self.port}"
            self.error_flag = True

        if self.error_flag or self.no_response_error_flag:
            await self.update_device_status()

        return result

    async def update_device_status(self):
        device = await Device.filter(name=self.device_custom_name).first()
        if device:
            device.actual_status = False
            tz = get_timezone()
            now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)
            wait_time_local = now_utc + timedelta(seconds=300)

            device.wait_time = wait_time_local.astimezone(tz)

            await device.save(update_fields=['actual_status', 'wait_time'])

        msg = "Device is not connected" if self.error_flag else "There is no response from the device"
        QMessageBox.warning(
            self.main_window,
            f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
            f"{self.device_custom_name} - {msg} - {self.error_text}",
            QMessageBox.StandardButton.Ok,
            QMessageBox.StandardButton.Cancel
        )