from datetime import datetime

import pyqtgraph as pg
import xlsxwriter
from PyQt5.QtCore import Qt, QSortFilterProxyModel, QTime, QTimer, QDate
from PyQt5.QtGui import QIcon, QStandardItemModel, QStandardItem, QFont
from PyQt5.QtWidgets import QMessageBox, QFileDialog, QTabWidget
from PyQt5.QtWidgets import QVBoxLayout, QPushButton, QLabel, QWidget, QSplitter, QTableView, QCalendarWidget, \
    QHBoxLayout, QDialog, QLCDNumber, QCheckBox, QDateEdit, QGridLayout
from pyqtgraph import AxisItem
from sqlalchemy import desc

from config import resource_path
from models.Report import SDM630Report, SDM630ReportTmp
from pyqt.widgets.DeviceDetailsSDM120Widget import DateAxisItem
from register_maps.RegisterMaps import RegisterMap


class DeviceDetailsSDM630Widget(QWidget):
    def __init__(self, main_window, device):
        super().__init__(main_window)
        self.device = device
        self.db_session = main_window.db_session
        self.main_window = main_window

        layout = QVBoxLayout(self)

        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.setChildrenCollapsible(False)
        layout.addWidget(main_splitter)

        # Ліва частина - таблиця
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        self.label = QLabel(f"Ім'я пристрою: {device.name} | Модель пристрою: {device.manufacturer} {device.model}")
        self.label.setStyleSheet("font-size: 16px;")
        left_layout.addWidget(self.label)

        filter_widget = QWidget()
        filter_layout = QHBoxLayout(filter_widget)

        vid_label = QLabel("Від:")
        vid_label.setStyleSheet("font-size: 16px;")
        filter_layout.addWidget(vid_label)

        self.start_date_edit = QDateEdit(self)
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate().addYears(-1))
        self.start_date_edit.setStyleSheet("font-size: 16px;")
        filter_layout.addWidget(self.start_date_edit)

        do_label = QLabel("До:")
        do_label.setStyleSheet("font-size: 16px;")
        filter_layout.addWidget(do_label)

        self.end_date_edit = QDateEdit(self)
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.setStyleSheet("font-size: 16px;")
        filter_layout.addWidget(self.end_date_edit)

        filter_button = QPushButton("Застосувати фільтр")
        filter_button.setStyleSheet("font-size: 16px;")
        filter_button.clicked.connect(self.apply_date_filter)
        filter_layout.addWidget(filter_button)

        left_layout.addWidget(filter_widget)

        # Кнопки для таблиці
        button_layout = QHBoxLayout()
        refresh_button = QPushButton()
        refresh_button.setIcon(QIcon(resource_path("pyqt/icons/refresh.png")))
        refresh_button.setFixedSize(36, 36)
        refresh_button.clicked.connect(self.load_report_data)
        button_layout.addWidget(refresh_button)

        export_button = QPushButton("Експорт в Excel")
        export_button.setStyleSheet("font-size: 16px;")
        export_button.setFixedHeight(36)
        button_layout.addWidget(export_button)

        left_layout.addLayout(button_layout)

        self.report_table = QTableView(self)
        left_layout.addWidget(self.report_table)

        main_splitter.addWidget(left_widget)

        # Права частина - вкладки
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("font-size: 16px;")
        main_splitter.addWidget(self.tabs)

        # Зберігаємо елементи для кожної вкладки
        self.phase_data = {}
        phases = ["Фаза 1", "Фаза 2", "Фаза 3", "Загальне"]
        for phase_name in phases:
            self.create_phase_tab(phase_name)

        # Зміна вкладки
        self.tabs.currentChanged.connect(self.update_active_tab_graphs)

        # Завантаження початкових даних
        self.load_report_data()

    def create_phase_tab(self, phase_name):
        """Створює вкладку для заданої фази."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Додати графіки
        voltage_graph = pg.PlotWidget()
        current_graph = pg.PlotWidget()
        energy_graph = pg.PlotWidget()

        # Налаштування осей
        voltage_graph.setAxisItems({'bottom': DateAxisItem(orientation='bottom')})
        current_graph.setAxisItems({'bottom': DateAxisItem(orientation='bottom')})
        energy_graph.setAxisItems({'bottom': DateAxisItem(orientation='bottom')})

        # Налаштування підписів
        voltage_graph.setLabel('left', 'Напруга', units='В')
        current_graph.setLabel('left', 'Струм', units='А')
        energy_graph.setLabel('left', 'Споживання', units='кВт·год')

        # Додати графіки до вкладки
        layout.addWidget(voltage_graph)
        layout.addWidget(current_graph)
        layout.addWidget(energy_graph)

        # Додати чекбокс автооновлення
        auto_update_checkbox = QCheckBox("Автооновлення")
        auto_update_checkbox.setChecked(True)
        layout.addWidget(auto_update_checkbox)

        # Додати годинник
        clock_label = QLabel("00:00:00")
        clock_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        clock_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(clock_label)

        # Додати індикатори
        indicators_layout = QGridLayout()

        voltage_label = QLabel("Напруга (V)")
        voltage_label.setStyleSheet("font-size: 16px;")
        voltage_lcd = QLCDNumber()
        voltage_lcd.setSegmentStyle(QLCDNumber.Flat)

        current_label = QLabel("Струм (A)")
        current_label.setStyleSheet("font-size: 16px;")
        current_lcd = QLCDNumber()
        current_lcd.setSegmentStyle(QLCDNumber.Flat)

        power_label = QLabel("Потужність (W)")
        power_label.setStyleSheet("font-size: 16px;")
        power_lcd = QLCDNumber()
        power_lcd.setSegmentStyle(QLCDNumber.Flat)

        energy_label = QLabel("Спожито (kWh)")
        energy_label.setStyleSheet("font-size: 16px;")
        energy_lcd = QLCDNumber()
        energy_lcd.setSegmentStyle(QLCDNumber.Flat)

        # Додати індикатори в сітку
        indicators_layout.addWidget(voltage_label, 0, 0)
        indicators_layout.addWidget(voltage_lcd, 1, 0)
        indicators_layout.addWidget(current_label, 0, 1)
        indicators_layout.addWidget(current_lcd, 1, 1)
        indicators_layout.addWidget(power_label, 2, 0)
        indicators_layout.addWidget(power_lcd, 3, 0)
        indicators_layout.addWidget(energy_label, 2, 1)
        indicators_layout.addWidget(energy_lcd, 3, 1)

        layout.addLayout(indicators_layout)

        # Зберігаємо графіки, індикатори, годинник і чекбокс у phase_data
        self.phase_data[phase_name] = {
            "tab": tab,
            "voltage_graph": voltage_graph,
            "current_graph": current_graph,
            "energy_graph": energy_graph,
            "auto_update_checkbox": auto_update_checkbox,
            "voltage_lcd": voltage_lcd,
            "current_lcd": current_lcd,
            "power_lcd": power_lcd,
            "energy_lcd": energy_lcd,
            "clock_label": clock_label,
        }

        self.tabs.addTab(tab, phase_name)

    def update_active_tab_graphs(self, index):
        """Оновлює графіки та індикатори лише на активній вкладці."""
        active_tab = self.tabs.tabText(index)
        if active_tab in self.phase_data:
            phase_data = self.phase_data[active_tab]
            self.update_graphs(phase_data)
            self.update_indicators()

    def update_voltage_graph(self, timestamps, voltages, phase_name):
        timestamps_numeric = [ts.timestamp() for ts in timestamps]

        plot_attr = f"voltage_plot_item_{phase_name}"
        graph_widget = self.phase_data[phase_name]["voltage_graph"]

        if not hasattr(self, plot_attr):
            setattr(self, plot_attr, graph_widget.plot(
                timestamps_numeric,
                voltages,
                pen=pg.mkPen(color='b', width=2),
                name=f"Напруга {phase_name}"
            ))
        else:
            getattr(self, plot_attr).setData(timestamps_numeric, voltages)

    def update_current_graph(self, timestamps, currents, phase_name):
        timestamps_numeric = [ts.timestamp() for ts in timestamps]

        plot_attr = f"current_plot_item_{phase_name}"
        graph_widget = self.phase_data[phase_name]["current_graph"]

        if not hasattr(self, plot_attr):
            setattr(self, plot_attr, graph_widget.plot(
                timestamps_numeric,
                currents,
                pen=pg.mkPen(color='r', width=2),
                name=f"Струм {phase_name}"
            ))
        else:
            getattr(self, plot_attr).setData(timestamps_numeric, currents)

    def update_energy_graph(self, hourly_timestamps, hourly_energy, phase_name):
        if len(hourly_timestamps) == 0 or len(hourly_energy) == 0:
            return

        hourly_timestamps_numeric = [ts.timestamp() for ts in hourly_timestamps]

        valid_data = [(ts, energy) for ts, energy in zip(hourly_timestamps_numeric, hourly_energy) if energy > 0]

        if len(valid_data) == 0:
            return

        bar_attr = f"energy_bar_items_{phase_name}"
        graph_widget = self.phase_data[phase_name]["energy_graph"]

        if not hasattr(self, bar_attr):
            setattr(self, bar_attr, [])

        energy_bar_items = getattr(self, bar_attr)

        for i, (ts, energy) in enumerate(valid_data):
            if i >= len(energy_bar_items):
                start_time = ts
                end_time = start_time + 3600

                bar_item = pg.BarGraphItem(
                    x0=start_time,
                    x1=end_time,
                    height=energy,
                    brush='g'
                )
                energy_bar_items.append(bar_item)
                graph_widget.addItem(bar_item)
            else:
                start_time = ts
                end_time = start_time + 3600
                energy_bar_items[i].setOpts(x0=start_time, x1=end_time, y0=0, y1=energy)

        while len(energy_bar_items) > len(valid_data):
            bar_item = energy_bar_items.pop()
            graph_widget.removeItem(bar_item)

        y_max = max([energy for _, energy in valid_data]) if valid_data else 5
        graph_widget.setYRange(0, y_max)

        x_min = min([ts for ts, _ in valid_data])
        x_max = max([ts for ts, _ in valid_data]) + 3600
        graph_widget.setXRange(x_min, x_max)

    def update_graphs(self, start_date=None, end_date=None):
        query = self.db_session.query(SDM630ReportTmp).filter_by(device_id=self.device.id)
        if start_date is not None and end_date is not None:
            query = query.filter(SDM630ReportTmp.timestamp >= start_date, SDM630ReportTmp.timestamp <= end_date)
        report_data = query.order_by(desc(SDM630ReportTmp.timestamp)).all()

        if not report_data:
            self.start_date = None
            self.end_date = None
            return

        phase_keys = ["Фаза 1", "Фаза 2", "Фаза 3"]

        for phase_name in phase_keys:
            timestamps = []
            voltages = []
            currents = []
            energies = []

            for report in report_data:
                timestamps.append(report.timestamp)
                voltages.append(getattr(report, f'line_voltage_{phase_keys.index(phase_name) + 1}'))
                currents.append(getattr(report, f'current_{phase_keys.index(phase_name) + 1}'))
                energies.append(getattr(report, f'power_{phase_keys.index(phase_name) + 1}'))

            self.update_voltage_graph(timestamps, voltages, phase_name)
            self.update_current_graph(timestamps, currents, phase_name)

            hourly_energy = []
            hourly_timestamps = []

            last_energy = None
            current_hour_start = None
            current_hour_energy = 0.0

            for report in report_data:
                current_hour = report.timestamp.replace(minute=0, second=0, microsecond=0)

                if current_hour_start is None:
                    current_hour_start = current_hour

                if current_hour != current_hour_start:
                    if last_energy is not None:
                        hourly_energy.append(current_hour_energy)
                        hourly_timestamps.append(current_hour_start)
                    current_hour_start = current_hour
                    current_hour_energy = 0.0

                energy_value = getattr(report, f'power_{phase_keys.index(phase_name) + 1}')

                if last_energy is not None:
                    current_hour_energy += abs(energy_value - last_energy)

                last_energy = energy_value

            if last_energy is not None:
                hourly_energy.append(current_hour_energy)
                hourly_timestamps.append(current_hour_start)

            self.update_energy_graph(hourly_timestamps, hourly_energy, phase_name)

    def update_indicators(self):
        """
        Оновлює значення індикаторів для всіх фаз SDM630.
        """
        # Отримання останнього звіту з бази даних
        last_report = (self.db_session.query(SDM630ReportTmp)
                       .filter_by(device_id=self.device.id)
                       .order_by(desc(SDM630ReportTmp.timestamp))
                       .first())
        if not last_report:
            return  # Якщо немає звітів, нічого не оновлюємо

        # Дані для фаз
        phases = {
            "Фаза 1": {
                "voltage": getattr(last_report, 'line_voltage_1', 0),
                "current": getattr(last_report, 'current_1', 0),
                "power": getattr(last_report, 'power_1', 0),
                "energy": getattr(last_report, 'total_kWh', 0),
            },
            "Фаза 2": {
                "voltage": getattr(last_report, 'line_voltage_2', 0),
                "current": getattr(last_report, 'current_2', 0),
                "power": getattr(last_report, 'power_2', 0),
                "energy": getattr(last_report, 'total_kWh', 0),
            },
            "Фаза 3": {
                "voltage": getattr(last_report, 'line_voltage_3', 0),
                "current": getattr(last_report, 'current_3', 0),
                "power": getattr(last_report, 'power_3', 0),
                "energy": getattr(last_report, 'total_kWh', 0),
            },
            "Загальне": {
                "energy": getattr(last_report, 'total_kWh', 0),
            }
        }

        # Оновлення індикаторів для кожної фази
        for phase_name, data in phases.items():
            if phase_name not in self.phase_data:
                continue  # Якщо фаза не налаштована, пропускаємо її

            # Отримання індикаторів
            phase = self.phase_data[phase_name]
            voltage_lcd = phase["voltage_lcd"]
            current_lcd = phase["current_lcd"]
            power_lcd = phase["power_lcd"]
            energy_lcd = phase["energy_lcd"]

            # Оновлення значень
            if voltage_lcd and "voltage" in data:
                voltage_lcd.display(f"{data['voltage']:.2f}")
            if current_lcd and "current" in data:
                current_lcd.display(f"{data['current']:.2f}")
            if power_lcd and "power" in data:
                power_lcd.display(f"{data['power']:.2f}")
            if energy_lcd and "energy" in data:
                energy_lcd.display(f"{data['energy']:.2f}")

            # Автоматичне оновлення графіків, якщо активовано
            if phase["auto_update_checkbox"].isChecked():
                self.update_graphs(phase_name)

    def create_table_model(self, report_data, device):
        column_labels = {
            "timestamp": "Час",
            "line_voltage_1": "Лінійна напруга\n(Фаза 1)\n",
            "line_voltage_2": "Лінійна напруга\n(Фаза 2)\n",
            "line_voltage_3": "Лінійна напруга\n(Фаза 3)\n",
            "current_1": "Струм\n(Фаза 1)\n",
            "current_2": "Струм\n(Фаза 2)\n",
            "current_3": "Струм\n(Фаза 3)\n",
            "power_1": "Активна потужність\n(Фаза 1)\n",
            "power_2": "Активна потужність\n(Фаза 2)\n",
            "power_3": "Активна потужність\n(Фаза 3)\n",
            "power_factor_1": "Коефіцієнт\nпотужності\n(Фаза 1)",
            "power_factor_2": "Коефіцієнт\nпотужності\n(Фаза 2)",
            "power_factor_3": "Коефіцієнт\nпотужності\n(Фаза 3)",
            "total_system_power": "Загальна\nпотужність\nсистеми",
            # "total_system_VA": "Загальна потужність",
            # "total_system_VAr": "Загальна реактивна потужність",
            # "total_system_power_factor": "Коефіцієнт потужності системи",
            # "total_import_kwh": "Загальне споживання (імпорт)",
            # "total_export_kwh": "Загальне споживання (експорт)",
            # "total_import_kVAh": "Загальне споживання (імпорт)",
            # "total_export_kVAh": "Загальне споживання (експорт)",
            "total_kVAh": "Загальна енергія\n",
            "_1_to_2_voltage": "Напруга між\nФазою 1 і Фазою 2\n",
            "_2_to_3_voltage": "Напруга між\nФазою 2 і Фазою 3\n",
            "_3_to_1_voltage": "Напруга між\nФазою 3 і Фазою 1\n",
            "neutral_current": "Струм нейтралі\n",
            # "line_voltage_THD_1": "THD лінійної напруги (Фаза 1)",
            # "line_voltage_THD_2": "THD лінійної напруги (Фаза 2)",
            # "line_voltage_THD_3": "THD лінійної напруги (Фаза 3)",
            # "line_current_THD_1": "THD лінійного струму (Фаза 1)",
            # "line_current_THD_2": "THD лінійного струму (Фаза 2)",
            # "line_current_THD_3": "THD лінійного струму (Фаза 3)",
            # "current_demand_1": "Струмове навантаження (Фаза 1)",
            # "current_demand_2": "Струмове навантаження (Фаза 2)",
            # "current_demand_3": "Струмове навантаження (Фаза 3)",
            # "phase_voltage_THD_1": "THD фазної напруги (Фаза 1)",
            # "phase_voltage_THD_2": "THD фазної напруги (Фаза 2)",
            # "phase_voltage_THD_3": "THD фазної напруги (Фаза 3)",
            # "average_line_to_line_voltage_THD": "Середній THD лінійної напруги",
            "total_kWh": "Загальна енергія\n",
            "total_kVArh": "Загальна реактивна\nенергія\n",
            # "import_kWh_1": "Імпортована енергія (Фаза 1)",
            # "import_kWh_2": "Імпортована енергія (Фаза 2)",
            # "import_kWh_3": "Імпортована енергія (Фаза 3)",
            # "export_kWh_1": "Експортована енергія (Фаза 1)",
            # "export_kWh_2": "Експортована енергія (Фаза 2)",
            # "export_kWh_3": "Експортована енергія (Фаза 3)",
            # "total_kWh_1": "Загальна енергія (Фаза 1)",
            # "total_kWh_2": "Загальна енергія (Фаза 2)",
            # "total_kWh_3": "Загальна енергія (Фаза 3)",
            # "import_kVArh_1": "Імпортована реактивна енергія (кВАр·год) (Фаза 1)",
            # "import_kVArh_2": "Імпортована реактивна енергія (кВАр·год) (Фаза 2)",
            # "import_kVArh_3": "Імпортована реактивна енергія (кВАр·год) (Фаза 3)",
            # "export_kVArh_1": "Експортована реактивна енергія (кВАр·год) (Фаза 1)",
            # "export_kVArh_2": "Експортована реактивна енергія (кВАр·год) (Фаза 2)",
            # "export_kVArh_3": "Експортована реактивна енергія (кВАр·год) (Фаза 3)",
            # "total_kVArh_1": "Загальна реактивна енергія (кВАр·год) (Фаза 1)",
            # "total_kVArh_2": "Загальна реактивна енергія (кВАр·год) (Фаза 2)",
            # "total_kVArh_3": "Загальна реактивна енергія (кВАр·год) (Фаза 3)",
        }

        # Get columns and units from RegisterMap
        register_map = RegisterMap.get_register_map(device.model)
        columns_with_units = RegisterMap.get_columns_with_units(register_map)

        # Формуємо список стовпців, який потрібно відображати в порядку, визначеному в column_labels
        columns = []
        for column in column_labels.keys():
            if any(getattr(report, column) is not None for report in report_data):
                columns.append(column)

        model = QStandardItemModel(len(report_data), len(columns))
        header_labels = []

        for column in columns:
            custom_label = column_labels.get(column, column)
            unit = columns_with_units.get(column, "")
            header_labels.append(f"{custom_label} ({unit})" if unit else custom_label)

        bold_font = QFont()
        bold_font.setBold(True)
        bold_font.setPointSize(12)

        for col_index, header in enumerate(header_labels):
            model.setHeaderData(col_index, Qt.Horizontal, header)
            model.setHeaderData(col_index, Qt.Horizontal, bold_font, Qt.FontRole)

        for row, report in enumerate(report_data):
            for col, column in enumerate(columns):
                value = getattr(report, column)
                if column == "timestamp" and value is not None:
                    # Перетворюємо timestamp на строку без мілісекунд
                    if isinstance(value, datetime):
                        value = value.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        # Якщо timestamp представлений як строка, парсимо і форматуюємо
                        value = datetime.fromisoformat(value).strftime("%Y-%m-%d %H:%M:%S")
                model.setItem(row, col, QStandardItem(str(value) if value is not None else ""))

        return model

    def load_report_data(self):
        start_date = self.start_date_edit.date().toPyDate()
        end_date = self.end_date_edit.date().addDays(1).toPyDate()

        report_data = self.db_session.query(SDM630Report).filter_by(device_id=self.device.id).filter(
            SDM630Report.timestamp >= start_date, SDM630Report.timestamp <= end_date
        ).order_by(desc(SDM630Report.timestamp)).all()

        model = self.create_table_model(report_data, self.device)

        proxy_model = QSortFilterProxyModel()
        proxy_model.setSourceModel(model)
        proxy_model.setSortCaseSensitivity(Qt.CaseInsensitive)

        self.report_table.setModel(proxy_model)
        self.report_table.sortByColumn(0, Qt.DescendingOrder)
        self.report_table.setSortingEnabled(True)
        self.report_table.resizeColumnsToContents()

    def apply_date_filter(self):
        self.load_report_data()
