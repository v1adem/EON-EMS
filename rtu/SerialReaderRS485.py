import json
import os
from datetime import datetime
from logging import error

from PyQt5.QtWidgets import QMessageBox
from pymodbus.client import ModbusSerialClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder

from models.Device import Device


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
    def __init__(self,
                 device_custom_name,
                 device_name,
                 port,
                 device_address,
                 baudrate,
                 bytesize,
                 parity,
                 stopbits,
                 main_window):
        self.port = port
        self.no_response_error_flag = False
        self.error_flag = False
        self.main_window = main_window
        self.device_custom_name = device_custom_name
        self.device_address = device_address

        json_path = os.path.join(os.path.dirname(__file__), '..', 'register_maps', f'{device_name}.json')

        with open(json_path, 'r') as f:
            property_specifications_list = json.load(f)
        self.property_specifications_list = property_specifications_list

        self.client = ModbusSerialClient(
            port=f"COM{port}",
            baudrate=baudrate,
            parity=parity,
            stopbits=stopbits,
            bytesize=bytesize,
            timeout=0.2
        )

    def connect(self):
        return self.client.connect()

    def read_property(self, property_name: str):
        if self.connect():
            property_specifications = self.property_specifications_list[property_name]
            property_address = property_specifications['register']
            count = 4 if property_specifications["format"] in ["float", "UD_WORD", "SD_WORD"] else 4

            try:
                if property_specifications["type"] == "holding":
                    response = self.client.read_holding_registers(property_address, count=count,
                                                                  slave=self.device_address)
                elif property_specifications["type"] == "input":
                    response = self.client.read_input_registers(property_address, count=count,
                                                                slave=self.device_address)
                if response.isError():
                    error(
                        f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')} | No response | {property_specifications}")
                    self.no_response_error_flag = True
                    return None

                return decode_data(data=response.registers, property_specifications=property_specifications)

            except Exception as e:
                error(f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')} | {e}")

            finally:
                self.client.close()

        else:
            self.error_flag = True

    def read_all_properties(self, properties_list):
        result = {}
        for property_name in properties_list:
            value = self.read_property(property_name)
            if value is not None:
                result[property_name] = value
            else:
                result[property_name] = None

        if self.error_flag:
            device = self.main_window.db_session.query(Device).filter(Device.name == self.device_custom_name).first()
            if device:
                device.reading_status = False
                self.main_window.db_session.commit()
            QMessageBox.warning(self.main_window, f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
                                f"{self.device_custom_name} - Пристрій не підключено")
        if self.no_response_error_flag:
            device = self.main_window.db_session.query(Device).filter(Device.name == self.device_custom_name).first()
            if device:
                device.reading_status = False
                self.main_window.db_session.commit()
            QMessageBox.warning(self.main_window, f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
                                f"Порт COM{self.port} - Немає відповіді. Пристрій {self.device_custom_name} - зчитування вимкнено")
        return result
