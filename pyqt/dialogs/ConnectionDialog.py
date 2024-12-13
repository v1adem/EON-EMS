from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLabel, QHBoxLayout, QComboBox
from pymodbus.client import ModbusSerialClient

from models.Admin import Admin


class ConnectionDialog(QDialog):
    def __init__(self, main_window):
        super().__init__(main_window)

        self.db_session = main_window.db_session

        self.setWindowTitle("З'єднання")
        self.setFixedSize(300, 120)
        self.connection_status = False

        layout = QVBoxLayout(self)

        # Статус
        self.status_label = QLabel(f"Статус PORT:COM{self.db_session.query(Admin).first().port}: Невідомо", self)
        self.status_label.setStyleSheet("color: red;")
        layout.addWidget(self.status_label)

        # Перевірити статус
        self.check_button = QPushButton("Перевірити статус", self)
        self.check_button.clicked.connect(self.check_status)
        layout.addWidget(self.check_button)

        # Зміна порта
        port_layout = QHBoxLayout()
        self.port_label = QLabel("Змінити порт (3,4 зазвичай системні)", self)
        self.port_combo = QComboBox(self)
        self.port_combo.addItems([str(i) for i in range(1, 256)])
        self.port_combo.currentIndexChanged.connect(self.change_port)
        port_layout.addWidget(self.port_label)
        port_layout.addWidget(self.port_combo)
        layout.addLayout(port_layout)

        self.set_current_port()

        # Допомога
        self.help_button = QPushButton("Допомога", self)
        self.help_button.clicked.connect(self.show_help)
        layout.addWidget(self.help_button)

    def check_status(self):
        self.connection_status = self.check_converter_connection()

        if self.connection_status:
            self.status_label.setText(f"Статус PORT:COM{self.db_session.query(Admin).first().port} : З'єднання успішне")
            self.status_label.setStyleSheet("color: green;")
        else:
            self.status_label.setText(f"Статус PORT:COM{self.db_session.query(Admin).first().port} : Немає з'єднання! Див. Допомога")
            self.status_label.setStyleSheet("color: red;")

    def check_converter_connection(self):
        try:
            port = self.db_session.query(Admin).first().port
            client = ModbusSerialClient(
                port=f"COM{port}",
                baudrate=9600,
                parity='N',
                stopbits=1,
                bytesize=8
            )
            if client.connect():
                return True
            else:
                return False
        except Exception as e:
            print(f"Помилка при підключенні: {e}")
            return False
        finally:
            client.close()

    def change_port(self):
        selected_port = self.port_combo.currentText()
        print(f"Обрано порт: {selected_port}")
        self.change_port_function(int(selected_port))

    def change_port_function(self, port_number):
        session = self.db_session

        try:
            admin_record = session.query(Admin).first()

            if admin_record:
                admin_record.port = port_number
                session.commit()
                print(f"Порт змінено на: COM{port_number} в записі admin")
            else:
                print("Запис адміністратора не знайдено!")
        except Exception as e:
            session.rollback()
            print(f"Помилка при зміні порту: {e}")

    def show_help(self):
        print("Відкрито допомогу")

    def set_current_port(self):
        try:
            admin = self.db_session.query(Admin).first()
            if admin and admin.port:
                current_port = admin.port
                index = self.port_combo.findText(f"COM{current_port}")
                if index != -1:
                    self.port_combo.setCurrentIndex(index)
        except Exception as e:
            print(f"Помилка при зчитуванні порту з бази даних: {e}")