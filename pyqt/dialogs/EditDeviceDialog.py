from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox, QSpinBox, QLabel, QPushButton, \
    QRadioButton, QTimeEdit, QCheckBox, QGroupBox, QFormLayout
from PyQt5.QtCore import QTime


class EditDeviceDialog(QDialog):
    def __init__(self, device, db_session, parent=None):
        super().__init__(parent)
        self.device = device
        self.db_session = db_session

        self.setWindowTitle("Редагувати пристрій")
        layout = QVBoxLayout(self)

        # Поле для назви пристрою
        self.name_edit = QLineEdit(self)
        self.name_edit.setText(device.name)

        # Випадаючий список для вибору моделі
        self.model_combo = QComboBox(self)
        self.model_combo.addItems(["SDM120", "SDM630"])  # Додайте інші моделі за потреби
        self.model_combo.setCurrentText(device.model)

        # Випадаючий список для виробника
        self.manufacturer_combo = QComboBox(self)
        self.manufacturer_combo.addItems(["Eastron"])  # Додайте інші виробники за потреби
        self.manufacturer_combo.setCurrentText(device.manufacturer)

        # Випадаючий список для baudrate
        self.baudrate_combo = QComboBox(self)
        self.baudrate_combo.addItems(["1200", "2400", "4800", "9600", "19200", "38400", "57600", "115200"])
        self.baudrate_combo.setCurrentText(str(device.baudrate))

        # Налаштування інших параметрів
        self.device_address_spin = QSpinBox(self)
        self.device_address_spin.setValue(device.device_address)

        self.bytesize_spin = QSpinBox(self)
        self.bytesize_spin.setValue(device.bytesize)

        self.stopbits_spin = QSpinBox(self)
        self.stopbits_spin.setValue(device.stopbits)

        self.parity_combo = QComboBox(self)
        self.parity_combo.addItems(["N", "E", "O"])  # No Parity, Even, Odd
        self.parity_combo.setCurrentText(device.parity)

        # Вибір типу зчитування (Reading Type) та його налаштування
        self.interval_radio = QRadioButton("Інтервал")
        self.time_radio = QRadioButton("Час")

        self.interval_spin = QSpinBox(self)
        self.interval_spin.setRange(1, 1440)  # Інтервал у хвилинах
        self.interval_spin.setValue(device.reading_interval // 60)  # Перетворення секунд в хвилини

        self.time_edit = QTimeEdit(self)
        self.time_edit.setTime(QTime.fromMSecsSinceStartOfDay(int(device.reading_time * 60000)))  # Години:Хвилини

        if device.reading_type == 1:
            self.interval_radio.setChecked(True)
            self.interval_spin.setEnabled(True)
            self.time_edit.setEnabled(False)
        else:
            self.time_radio.setChecked(True)
            self.interval_spin.setEnabled(False)
            self.time_edit.setEnabled(True)

        self.interval_radio.toggled.connect(self.toggle_reading_type)

        # Параметри для звіту (Parameters)
        self.parameters_checkboxes = []
        available_parameters = ["Voltage", "Current", "Power"]  # Список параметрів
        current_parameters = device.get_parameter_names()

        for param in available_parameters:
            checkbox = QCheckBox(param)
            checkbox.setChecked(param in current_parameters)
            self.parameters_checkboxes.append(checkbox)

        # Кнопка Зберегти
        self.save_button = QPushButton("Зберегти")
        self.save_button.clicked.connect(self.save_changes)

        # Додавання всіх елементів у діалогове вікно
        form_layout = QFormLayout()
        form_layout.addRow("Назва:", self.name_edit)
        form_layout.addRow("Модель:", self.model_combo)
        form_layout.addRow("Виробник:", self.manufacturer_combo)
        form_layout.addRow("Baudrate:", self.baudrate_combo)
        form_layout.addRow("Адреса пристрою:", self.device_address_spin)
        form_layout.addRow("Bytesize:", self.bytesize_spin)
        form_layout.addRow("Stopbits:", self.stopbits_spin)
        form_layout.addRow("Parity:", self.parity_combo)

        reading_layout = QVBoxLayout()
        reading_layout.addWidget(self.interval_radio)
        reading_layout.addWidget(self.interval_spin)
        reading_layout.addWidget(self.time_radio)
        reading_layout.addWidget(self.time_edit)
        form_layout.addRow("Тип зчитування:", reading_layout)

        parameters_layout = QVBoxLayout()
        for checkbox in self.parameters_checkboxes:
            parameters_layout.addWidget(checkbox)
        parameters_group = QGroupBox("Параметри для звіту")
        parameters_group.setLayout(parameters_layout)

        layout.addLayout(form_layout)
        layout.addWidget(parameters_group)
        layout.addWidget(self.save_button)

    def toggle_reading_type(self):
        self.interval_spin.setEnabled(self.interval_radio.isChecked())
        self.time_edit.setEnabled(self.time_radio.isChecked())

    def save_changes(self):
        self.device.name = self.name_edit.text()
        self.device.model = self.model_combo.currentText()
        self.device.manufacturer = self.manufacturer_combo.currentText()
        self.device.baudrate = int(self.baudrate_combo.currentText())
        self.device.device_address = self.device_address_spin.value()
        self.device.bytesize = self.bytesize_spin.value()
        self.device.stopbits = self.stopbits_spin.value()
        self.device.parity = self.parity_combo.currentText()

        if self.interval_radio.isChecked():
            self.device.reading_type = 1
            self.device.reading_interval = self.interval_spin.value() * 60  # Зберігаємо в секундах
            self.device.reading_time = 0
        else:
            self.device.reading_type = 2
            time = self.time_edit.time()
            self.device.reading_time = time.hour() * 60 + time.minute()

        selected_parameters = [checkbox.text() for checkbox in self.parameters_checkboxes if checkbox.isChecked()]
        self.device.parameters = ','.join([f"{param}:Units" for param in selected_parameters])  # Збережіть одиниці

        self.db_session.commit()
        self.accept()
