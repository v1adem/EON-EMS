from datetime import datetime

import pyqtgraph as pg
from PySide6.QtWidgets import QToolTip, QAbstractItemView
import xlsxwriter
from AsyncioPySide6 import AsyncioPySide6
from PySide6.QtCore import QTimer, QDate, Qt, QSortFilterProxyModel, QTime
from PySide6.QtGui import QStandardItemModel, QFont, QStandardItem
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSplitter, QLabel, QDateEdit, QTableView, QTabWidget, QHBoxLayout, \
    QPushButton, QCheckBox, QGridLayout, QLCDNumber, QDialog, QMessageBox, QFileDialog

from models.Report import SDM630Report, SDM630ReportTmp, SDM120Report, SDM120ReportTmp, SDM72DReport, SDM72DReportTmp
from pyqt.widgets.DateAxisItem import DateAxisItem
from register_maps.RegisterMaps import RegisterMap


class DeviceDetailsWidget(QWidget):
    def __init__(self, main_window, device):
        super().__init__(main_window)
        self.auto_update_checkbox = None
        self.device = device
        self.device_model = self.device.model
        self.main_window = main_window

        self.report_data = None

        self.init_column_labels()

        layout = QVBoxLayout(self)

        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.setChildrenCollapsible(False)
        layout.addWidget(main_splitter)

        # Ліва частина - таблиця
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        self.label = QLabel(f"Ім'я пристрою: {device.name} | Модель пристрою: {device.manufacturer} {device.model}")
        self.label.setStyleSheet("font-size: 16px;")
        left_layout.addWidget(self.label)

        self.start_date_table_filter = QDateEdit(self)
        self.end_date_table_filter = QDateEdit(self)
        self.create_filter_buttons(left_layout)

        self.report_table = QTableView(self)
        left_layout.addWidget(self.report_table)

        main_splitter.addWidget(left_widget)

        # Права частина - вкладки
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("font-size: 16px;")
        main_splitter.addWidget(self.tabs)

        self.phase_data = {}
        self.phases = []
        if self.device_model == "SDM120":
            self.phases = ["Фаза 1"]
        elif self.device_model == "SDM630" or self.device_model == "SDM72D":
            self.phases = ["Фаза 1", "Фаза 2", "Фаза 3", "Загальне"]

        for phase_name in self.phases:
            if self.device_model == "SDM72D":
                self.create_phase_tab_sdm72d(phase_name)
            else:
                self.create_phase_tab(phase_name)

        self.set_light_theme()

        self.timer_clock_indicator = QTimer(self)
        self.timer_clock_indicator.timeout.connect(self.update_clock_indicators)
        self.timer_clock_indicator.setInterval(1000)
        self.timer_clock_indicator.start()

        self.load_report_data()

        self.timer_update_all_tabs_graphs = QTimer(self)
        self.timer_update_all_tabs_graphs.timeout.connect(self.load_report_data)
        self.timer_update_all_tabs_graphs.setInterval(((device.reading_interval - 60) * 1000) + 1000)
        self.timer_update_all_tabs_graphs.start()

    def create_filter_buttons(self, layout):
        """Створення фільтрів і кнопок для таблиці."""
        filter_widget = QWidget()
        filter_layout = QHBoxLayout(filter_widget)

        vid_label = QLabel("Від:")
        vid_label.setStyleSheet("font-size: 16px;")
        filter_layout.addWidget(vid_label)

        self.start_date_table_filter.setCalendarPopup(True)
        self.start_date_table_filter.setDate(QDate.currentDate().addMonths(-1))
        self.start_date_table_filter.setStyleSheet("font-size: 16px;")
        filter_layout.addWidget(self.start_date_table_filter)

        do_label = QLabel("До:")
        do_label.setStyleSheet("font-size: 16px;")
        filter_layout.addWidget(do_label)

        self.end_date_table_filter.setCalendarPopup(True)
        self.end_date_table_filter.setDate(QDate.currentDate())
        self.end_date_table_filter.setStyleSheet("font-size: 16px;")
        filter_layout.addWidget(self.end_date_table_filter)

        filter_button = QPushButton("Застосувати фільтр")
        filter_button.setStyleSheet("font-size: 16px;")
        filter_button.clicked.connect(self.apply_date_filter)
        filter_layout.addWidget(filter_button)

        layout.addWidget(filter_widget)

        # Кнопки для таблиці
        button_layout = QHBoxLayout()
        self.auto_update_checkbox = QCheckBox("Автооновлення")
        self.auto_update_checkbox.setStyleSheet("font-size: 16px;")
        self.auto_update_checkbox.setChecked(True)
        button_layout.addWidget(self.auto_update_checkbox)

        export_button = QPushButton("Експорт в Excel")
        export_button.setStyleSheet("font-size: 16px;")
        export_button.setFixedHeight(36)
        export_button.clicked.connect(self.open_export_dialog)
        button_layout.addWidget(export_button)

        layout.addLayout(button_layout)

    def create_phase_tab(self, phase_name):
        """Створює вкладку для заданої фази."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        top_layout = QVBoxLayout()
        bottom_layout = QHBoxLayout()

        voltage_graph = pg.PlotWidget()
        current_graph = pg.PlotWidget()
        if phase_name != "Загальне":
            voltage_graph.showGrid(x=True, y=True, alpha=0.5)
            current_graph.showGrid(x=True, y=True, alpha=0.5)
            voltage_graph.setAxisItems({'bottom': DateAxisItem(orientation='bottom')})
            current_graph.setAxisItems({'bottom': DateAxisItem(orientation='bottom')})
            voltage_graph.setLabel('left', 'Напруга', units='В')
            current_graph.setLabel('left', 'Струм', units='А')
            top_layout.addWidget(voltage_graph)
            top_layout.addWidget(current_graph)

        energy_graph = pg.PlotWidget()
        energy_graph.showGrid(x=True, y=True, alpha=0.5)
        energy_graph.setAxisItems({'bottom': DateAxisItem(orientation='bottom')})
        energy_graph.setLabel('left', 'Споживання', units='кВт·год')
        top_layout.addWidget(energy_graph)

        layout.addLayout(top_layout)

        bottom_left_layout = QGridLayout()

        clock_title = QLabel("Поточний час")
        clock_title.setStyleSheet("font-size: 16pt; font-weight: bold;")
        clock_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bottom_left_layout.addWidget(clock_title)

        clock_label = QLabel()
        clock_label.setStyleSheet("font-size: 16pt;")
        clock_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bottom_left_layout.addWidget(clock_label)

        layout.addStretch()

        indicators_layout = QGridLayout()

        voltage_label = QLabel("Напруга (V)")
        voltage_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        voltage_lcd = QLCDNumber()
        voltage_lcd.setStyleSheet("font-size: 18pt;")
        voltage_lcd.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)

        current_label = QLabel("Струм (A)")
        current_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        current_lcd = QLCDNumber()
        current_lcd.setStyleSheet("font-size: 18pt;")
        current_lcd.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)

        power_label = QLabel("Потужність (W)")
        power_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        power_lcd = QLCDNumber()
        power_lcd.setStyleSheet("font-size: 18pt;")
        power_lcd.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)

        energy_label = QLabel("Спожито (kWh)")
        energy_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        energy_lcd = QLCDNumber()
        energy_lcd.setStyleSheet("font-size: 18pt;")
        energy_lcd.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)

        if phase_name != "Загальне":
            indicators_layout.addWidget(voltage_label, 0, 0)
            indicators_layout.addWidget(voltage_lcd, 1, 0)
            indicators_layout.addWidget(current_label, 0, 1)
            indicators_layout.addWidget(current_lcd, 1, 1)
            indicators_layout.addWidget(power_label, 2, 0)
            indicators_layout.addWidget(power_lcd, 3, 0)
        indicators_layout.addWidget(energy_label, 2, 1)
        indicators_layout.addWidget(energy_lcd, 3, 1)

        bottom_layout.addLayout(bottom_left_layout)
        bottom_layout.addLayout(indicators_layout)

        layout.addLayout(bottom_layout)

        self.phase_data[phase_name] = {
            "tab": tab,
            "voltage_graph": voltage_graph,
            "current_graph": current_graph,
            "energy_graph": energy_graph,
            "voltage_lcd": voltage_lcd,
            "current_lcd": current_lcd,
            "power_lcd": power_lcd,
            "energy_lcd": energy_lcd,
            "clock_label": clock_label,
        }

        self.tabs.addTab(tab, phase_name)

    def load_report_data(self):
        async def run_load_report_data():
            start_date = self.start_date_table_filter.date().toPython()
            end_date = self.end_date_table_filter.date().addDays(1).toPython()

            if self.device_model == "SDM120":
                report_model = SDM120Report
            elif self.device_model == "SDM630":
                report_model = SDM630Report
            elif self.device_model == "SDM72D":
                report_model = SDM72DReport
            else:
                return

            self.report_data = await report_model.filter(
                device_id=self.device.id,
                timestamp__gte=start_date,
                timestamp__lte=end_date
            ).order_by("timestamp").all()
            model = self.create_table_model(self.report_data, self.device)

            proxy_model = QSortFilterProxyModel()
            proxy_model.setSourceModel(model)
            proxy_model.setSortCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

            self.report_table.setModel(proxy_model)
            self.report_table.sortByColumn(0, Qt.SortOrder.DescendingOrder)
            self.report_table.setSortingEnabled(True)
            self.report_table.resizeColumnsToContents()

            if self.device_model == "SDM72D":
                self.update_graphs_sdm72d()
            else:
                self.update_graphs()
        AsyncioPySide6.runTask(run_load_report_data())

    def apply_date_filter(self):
        self.load_report_data()

    def create_table_model(self, report_data, device):
        register_map = RegisterMap.get_register_map(device.model)
        columns_with_units = RegisterMap.get_columns_with_units(register_map)

        columns = []
        for column in self.column_labels.keys():
            if any(getattr(report, column) is not None for report in report_data):
                columns.append(column)

        model = QStandardItemModel(len(report_data), len(columns))
        header_labels = []

        for column in columns:
            custom_label = self.column_labels.get(column, column)
            unit = columns_with_units.get(column, "")
            header_labels.append(f"{custom_label} ({unit})" if unit else custom_label)

        bold_font = QFont()
        bold_font.setBold(True)
        bold_font.setPointSize(12)

        for col_index, header in enumerate(header_labels):
            model.setHeaderData(col_index, Qt.Orientation.Horizontal, header)
            model.setHeaderData(col_index, Qt.Orientation.Horizontal, bold_font, Qt.ItemDataRole.FontRole)

        for row, report in enumerate(report_data):
            for col, column in enumerate(columns):
                value = getattr(report, column)
                if column == "timestamp" and value is not None:
                    if isinstance(value, datetime):
                        value = value.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        value = datetime.fromisoformat(value).strftime("%Y-%m-%d %H:%M:%S")
                model.setItem(row, col, QStandardItem(str(value) if value is not None else ""))

        return model

    def update_clock_indicators(self):
        async def run_update_clock_indicators():
            if self.device_model == "SDM120":
                report_model = SDM120ReportTmp
            elif self.device_model == "SDM630":
                report_model = SDM630ReportTmp
            elif self.device_model == "SDM72D":
                report_model = SDM72DReportTmp
            else:
                return

            last_report = await report_model.filter(
                device_id=self.device.id
            ).order_by("-timestamp").first()

            if not last_report:
                return

            if self.device_model == "SDM72D":
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
            else:
                # Дані для фаз
                phases = {
                    "Фаза 1": {
                        "voltage": getattr(last_report, 'line_voltage_1', 0),
                        "current": getattr(last_report, 'current_1', 0),
                        "power": getattr(last_report, 'power_1', 0),
                        "energy": getattr(last_report, 'total_kWh_1', 0),
                    },
                    "Фаза 2": {
                        "voltage": getattr(last_report, 'line_voltage_2', 0),
                        "current": getattr(last_report, 'current_2', 0),
                        "power": getattr(last_report, 'power_2', 0),
                        "energy": getattr(last_report, 'total_kWh_2', 0),
                    },
                    "Фаза 3": {
                        "voltage": getattr(last_report, 'line_voltage_3', 0),
                        "current": getattr(last_report, 'current_3', 0),
                        "power": getattr(last_report, 'power_3', 0),
                        "energy": getattr(last_report, 'total_kWh_3', 0),
                    },
                    "Загальне": {
                        "energy": getattr(last_report, 'total_kWh', 0),
                    }
                }

            for phase_name, data in phases.items():
                if phase_name not in self.phase_data:
                    continue

                phase = self.phase_data[phase_name]
                voltage_lcd = phase["voltage_lcd"]
                current_lcd = phase["current_lcd"]
                power_lcd = phase["power_lcd"]
                energy_lcd = phase["energy_lcd"]

                if voltage_lcd and "voltage" in data:
                    voltage_lcd.display(f"{data['voltage']}")
                if current_lcd and "current" in data:
                    current_lcd.display(f"{data['current']}")
                if power_lcd and "power" in data:
                    power_lcd.display(f"{data['power']}")
                if energy_lcd and "energy" in data:
                    energy_lcd.display(f"{data['energy']}")

            current_time = QTime.currentTime().toString("HH:mm:ss")  # Час
            current_time += "\n" + QDate.currentDate().toString("dd.MM.yyyy")  # Дата

            for phase_name, phase_data in self.phase_data.items():
                phase_data["clock_label"].setText(current_time)
        AsyncioPySide6.runTask(run_update_clock_indicators())

    def add_tooltips(self, graph_widget, timestamps, values):
        points = list(zip(timestamps, values))

        def on_mouse_moved(evt):
            pos = evt
            if graph_widget.sceneBoundingRect().contains(pos):
                mouse_point = graph_widget.plotItem.vb.mapSceneToView(pos)
                x, y = mouse_point.x(), mouse_point.y()

                # Пошук найближчої точки
                closest_point = min(points, key=lambda p: (p[0] - x) ** 2 + (p[1] - y) ** 2)
                tooltip_text = f"{closest_point[1]:.2f}"

                # Відображення підказки
                QToolTip.showText(
                    graph_widget.mapToGlobal(graph_widget.mapFromScene(pos)), tooltip_text
                )

        graph_widget.scene().sigMouseMoved.connect(on_mouse_moved)

    def on_graph_point_clicked(self, plot, points):
        if not points:
            return  # Нічого не робимо, якщо точки не передані

        point = points[0]  # Беремо першу точку
        row_index = point.data()  # Отримуємо індекс рядка таблиці

        # Виділяємо рядок у таблиці та прокручуємо до нього
        self.report_table.selectRow(row_index)
        self.report_table.scrollTo(self.report_table.model().index(row_index, 0))

    def update_voltage_graph(self, timestamps, voltages, phase_name):
        timestamps_numeric = [ts.timestamp() for ts in timestamps]

        plot_attr = f"voltage_plot_item_{phase_name}"
        graph_widget = self.phase_data[phase_name]["voltage_graph"]

        if not hasattr(self, plot_attr):
            # Додаємо графік
            setattr(self, plot_attr, graph_widget.plot(
                timestamps_numeric,
                voltages,
                pen=pg.mkPen(color='b', width=2),
                name=f"Напруга {phase_name}"
            ))

            # Додаємо точки на графік
            scatter_points = []
            for i, (x, y) in enumerate(zip(timestamps_numeric, voltages)):
                scatter_points.append({'pos': (x, y), 'data': i})  # Прив'язуємо індекс рядка таблиці

            scatter = pg.ScatterPlotItem(pen=None, brush='b', size=10)
            scatter.addPoints(scatter_points)

            # Додаємо обробник кліків
            scatter.sigClicked.connect(self.on_graph_point_clicked)

            graph_widget.addItem(scatter)

        else:
            # Оновлюємо графік
            getattr(self, plot_attr).setData(timestamps_numeric, voltages)

    def update_current_graph(self, timestamps, currents, phase_name):
        timestamps_numeric = [ts.timestamp() for ts in timestamps]

        plot_attr = f"current_plot_item_{phase_name}"
        graph_widget = self.phase_data[phase_name]["current_graph"]

        if not hasattr(self, plot_attr):
            # Додаємо графік
            setattr(self, plot_attr, graph_widget.plot(
                timestamps_numeric,
                currents,
                pen=pg.mkPen(color='r', width=2),
                name=f"Струм {phase_name}"
            ))

            # Додаємо точки на графік
            scatter_points = []
            for i, (x, y) in enumerate(zip(timestamps_numeric, currents)):
                scatter_points.append({'pos': (x, y), 'data': i})  # Прив'язуємо індекс рядка таблиці

            scatter = pg.ScatterPlotItem(pen=None, brush='r', size=10)
            scatter.addPoints(scatter_points)

            # Додаємо обробник кліків
            scatter.sigClicked.connect(self.on_graph_point_clicked)

            graph_widget.addItem(scatter)

        else:
            # Оновлюємо графік
            getattr(self, plot_attr).setData(timestamps_numeric, currents)

    def update_energy_graph(self, hourly_timestamps, hourly_energy, phase_name):
        if not hourly_timestamps or not hourly_energy:
            return

        # Перетворення timestamp в числовий формат
        hourly_timestamps_numeric = [ts.timestamp() for ts in hourly_timestamps]
        valid_data = [(ts, energy) for ts, energy in zip(hourly_timestamps_numeric, hourly_energy) if energy > 0]

        if not valid_data:
            return

        bar_attr = f"energy_bar_items_{phase_name}"
        graph_widget = self.phase_data[phase_name]["energy_graph"]

        # Ініціалізація списку стовпчиків, якщо його ще немає
        if not hasattr(self, bar_attr):
            setattr(self, bar_attr, [])

        energy_bar_items = getattr(self, bar_attr)

        # Оптимізоване оновлення або додавання стовпчиків
        for i, (ts, energy) in enumerate(valid_data):
            start_time = ts
            end_time = start_time + 3600  # Діапазон стовпчика

            if i < len(energy_bar_items):
                # Оновлення існуючого стовпчика
                energy_bar_items[i].setOpts(x0=start_time, x1=end_time, height=energy)
            else:
                # Додавання нового стовпчика
                bar_item = pg.BarGraphItem(
                    x0=start_time,
                    x1=end_time,
                    height=energy,
                    brush='g'
                )
                energy_bar_items.append(bar_item)
                graph_widget.addItem(bar_item)

                # Налаштування діапазону осей
                y_max = max(energy for _, energy in valid_data)
                graph_widget.setYRange(0, y_max, padding=0.1)

                x_min = min(ts for ts, _ in valid_data)
                x_max = max(ts for ts, _ in valid_data) + 3600
                graph_widget.setXRange(x_min, x_max, padding=0.1)

    def update_graphs(self):
        for phase_name in self.phases:
            timestamps = []
            voltages = []
            currents = []
            energies = []

            for report in self.report_data:
                timestamps.append(report.timestamp)
                if phase_name == "Загальне":
                    energies.append(getattr(report, f'total_kWh'))
                else:
                    voltages.append(getattr(report, f'line_voltage_{self.phases.index(phase_name) + 1}'))
                    currents.append(getattr(report, f'current_{self.phases.index(phase_name) + 1}'))
                    energies.append(getattr(report, f'total_kWh_{self.phases.index(phase_name) + 1}'))
            if phase_name != "Загальне":
                self.update_voltage_graph(timestamps, voltages, phase_name)
                self.update_current_graph(timestamps, currents, phase_name)

            hourly_energy = []
            hourly_timestamps = []

            last_energy = None
            current_hour_start = None
            current_hour_energy = 0.0

            for report in self.report_data:
                current_hour = report.timestamp.replace(minute=0, second=0, microsecond=0)

                if current_hour_start is None:
                    current_hour_start = current_hour

                if current_hour != current_hour_start:
                    if last_energy is not None:
                        hourly_energy.append(current_hour_energy)
                        hourly_timestamps.append(current_hour_start)
                    current_hour_start = current_hour
                    current_hour_energy = 0.0
                if phase_name == "Загальне":
                    energy_value = getattr(report, f'total_kWh')
                else:
                    energy_value = getattr(report, f'total_kWh_{self.phases.index(phase_name) + 1}')

                if last_energy is not None:
                    current_hour_energy += abs(energy_value - last_energy)

                last_energy = energy_value

            if last_energy is not None:
                hourly_energy.append(current_hour_energy)
                hourly_timestamps.append(current_hour_start)

            self.update_energy_graph(hourly_timestamps, hourly_energy, phase_name)

    def set_light_theme(self):
        for phase_name, phase_data in self.phase_data.items():
            phase_data["voltage_graph"].setBackground('w')
            phase_data["voltage_graph"].plot([], pen=pg.mkPen(color='b', width=2))
            phase_data["current_graph"].setBackground('w')
            phase_data["current_graph"].plot([], pen=pg.mkPen(color='r', width=2))
            phase_data["energy_graph"].setBackground('w')
            phase_data["energy_graph"].plot([], pen=pg.mkPen(color='g', width=2))

    def init_column_labels(self):
        if self.device_model == "SDM120":
            self.column_labels = {
                "timestamp": "Час",
                "line_voltage_1": "Напруга\n",
                "current_1": "Струм\n",
                "active_power_1": "Активна\nпотужність\n",
                "power_1": "Повна\nпотужність\n",
                "reactive_power_1": "Реактивна\nпотужність\n",
                "power_factor_1": "Коефіцієнт\nперетворення\n",
                "import_active_energy_1": "Імпортована\nактивна енергія\n",
                "export_active_energy_1": "Експортована\nактивна енергія\n",
                "total_active_energy": "Загальна\nактивна енергія\n",
                "total_reactive_energy": "Загальна\nреактивна енергія\n",
                "frequency_1": "Частота\n",
                "total_kWh_1": "Загально спожито\nkWh"
            }
            self.column_labels_for_excel = {
                "line_voltage_1": "Напруга Volts",
                "current_1": "Струм Amps",
                "active_power_1": "Активна потужність Watts",
                "power_1": "Повна потужність VA",
                "reactive_power_1": "Реактивна потужність VAr",
                "power_factor_1": "Коефіцієнт перетворення",
                "import_active_energy_1": "Імпортована активна енергія kWh",
                "export_active_energy_1": "Експортована активна енергія kWh",
                "total_active_energy": "Загальна активна енергія kWh",
                "total_reactive_energy": "Загальна реактивна енергія kWh",
                "frequency_1": "Частота Hz",
                "total_kWh_1": "Загально спожито kWh"
            }
        elif self.device_model == "SDM630":
            self.column_labels = {
                "timestamp": "Час",
                "line_voltage_1": "Лінійна напруга\n(Фаза 1)\n",
                "line_voltage_2": "Лінійна напруга\n(Фаза 2)\n",
                "line_voltage_3": "Лінійна напруга\n(Фаза 3)\n",
                "current_1": "Струм\n(Фаза 1)\n",
                "current_2": "Струм\n(Фаза 2)\n",
                "current_3": "Струм\n(Фаза 3)\n",
                "power_1": "Потужність\n(Фаза 1)\n",
                "power_2": "Потужність\n(Фаза 2)\n",
                "power_3": "Потужність\n(Фаза 3)\n",
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
                "total_kWh_1": "Загальна енергія (Фаза 1)",
                "total_kWh_2": "Загальна енергія (Фаза 2)",
                "total_kWh_3": "Загальна енергія (Фаза 3)",
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
            self.column_labels_for_excel = {
                "line_voltage_1": "Лінійна напруга (Фаза 1) Volts",
                "line_voltage_2": "Лінійна напруга (Фаза 2) Volts",
                "line_voltage_3": "Лінійна напруга (Фаза 3) Volts",
                "current_1": "Струм (Фаза 1) Amps",
                "current_2": "Струм (Фаза 2) Amps",
                "current_3": "Струм (Фаза 3) Amps",
                "power_1": "Потужність (Фаза 1) Watts",
                "power_2": "Потужність (Фаза 2) Watts",
                "power_3": "Потужність (Фаза 3) Watts",
                "power_factor_1": "Коефіцієнт потужності (Фаза 1)",
                "power_factor_2": "Коефіцієнт потужності (Фаза 2)",
                "power_factor_3": "Коефіцієнт потужності (Фаза 3)",
                "total_system_power": "Загальна потужність системи Watts",
                "total_system_VA": "Загальна потужність VA",
                "total_system_VAr": "Загальна реактивна потужність VAr",
                "total_system_power_factor": "Коефіцієнт потужності системи",
                "total_import_kwh": "Загальне споживання (імпорт) kWh",
                "total_export_kwh": "Загальне споживання (експорт) kWh",
                "total_import_kVAh": "Загальне споживання (імпорт) kWh",
                "total_export_kVAh": "Загальне споживання (експорт) kWh",
                "total_kVAh": "Загальна енергія kVAh",
                "_1_to_2_voltage": "Напруга між Фазою 1 і Фазою 2 Volts",
                "_2_to_3_voltage": "Напруга між Фазою 2 і Фазою 3 Volts",
                "_3_to_1_voltage": "Напруга між Фазою 3 і Фазою 1 Volts",
                "neutral_current": "Струм нейтралі Amps",
                "line_voltage_THD_1": "THD лінійної напруги (Фаза 1) %",
                "line_voltage_THD_2": "THD лінійної напруги (Фаза 2) %",
                "line_voltage_THD_3": "THD лінійної напруги (Фаза 3) %",
                "line_current_THD_1": "THD лінійного струму (Фаза 1) %",
                "line_current_THD_2": "THD лінійного струму (Фаза 2) %",
                "line_current_THD_3": "THD лінійного струму (Фаза 3) %",
                "current_demand_1": "Струмове навантаження (Фаза 1) Amps",
                "current_demand_2": "Струмове навантаження (Фаза 2) Amps",
                "current_demand_3": "Струмове навантаження (Фаза 3) Amps",
                "phase_voltage_THD_1": "THD фазної напруги (Фаза 1) %",
                "phase_voltage_THD_2": "THD фазної напруги (Фаза 2) %",
                "phase_voltage_THD_3": "THD фазної напруги (Фаза 3) %",
                "average_line_to_line_voltage_THD": "Середній THD лінійної напруги",
                "total_kWh": "Загальна енергія kWh",
                "total_kVArh": "Загальна реактивна енергія kVArh",
                "import_kWh_1": "Імпортована енергія (Фаза 1) kWh",
                "import_kWh_2": "Імпортована енергія (Фаза 2) kWh",
                "import_kWh_3": "Імпортована енергія (Фаза 3) kWh",
                "export_kWh_1": "Експортована енергія (Фаза 1) kWh",
                "export_kWh_2": "Експортована енергія (Фаза 2) kWh",
                "export_kWh_3": "Експортована енергія (Фаза 3) kWh",
                "total_kWh_1": "Загальна енергія (Фаза 1) kWh",
                "total_kWh_2": "Загальна енергія (Фаза 2) kWh",
                "total_kWh_3": "Загальна енергія (Фаза 3) kWh",
                "import_kVArh_1": "Імпортована реактивна енергія (кВАр·год) (Фаза 1)",
                "import_kVArh_2": "Імпортована реактивна енергія (кВАр·год) (Фаза 2)",
                "import_kVArh_3": "Імпортована реактивна енергія (кВАр·год) (Фаза 3)",
                "export_kVArh_1": "Експортована реактивна енергія (кВАр·год) (Фаза 1)",
                "export_kVArh_2": "Експортована реактивна енергія (кВАр·год) (Фаза 2)",
                "export_kVArh_3": "Експортована реактивна енергія (кВАр·год) (Фаза 3)",
                "total_kVArh_1": "Загальна реактивна енергія (кВАр·год) (Фаза 1)",
                "total_kVArh_2": "Загальна реактивна енергія (кВАр·год) (Фаза 2)",
                "total_kVArh_3": "Загальна реактивна енергія (кВАр·год) (Фаза 3)",
            }
        elif self.device_model == "SDM72D":
            self.column_labels = {
                "timestamp": "Час",
                "line_voltage_1": "Лінійна напруга\n(Фаза 1)\n",
                "line_voltage_2": "Лінійна напруга\n(Фаза 2)\n",
                "line_voltage_3": "Лінійна напруга\n(Фаза 3)\n",
                "current_1": "Струм\n(Фаза 1)\n",
                "current_2": "Струм\n(Фаза 2)\n",
                "current_3": "Струм\n(Фаза 3)\n",
                "power_1": "Потужність\n(Фаза 1)\n",
                "power_2": "Потужність\n(Фаза 2)\n",
                "power_3": "Потужність\n(Фаза 3)\n",
                "active_power_1": "Активна потужність\n(Фаза 1)\n)",
                "active_power_2": "Активна потужність\n(Фаза 2)\n)",
                "active_power_3": "Активна потужність\n(Фаза 3)\n)",
                "reactive_power_1": "Активна потужність\n(Фаза 1)\n)",
                "reactive_power_2": "Активна потужність\n(Фаза 2)\n)",
                "reactive_power_3": "Активна потужність\n(Фаза 3)\n)",
                "power_factor_1": "Коефіцієнт\nпотужності\n(Фаза 1)",
                "power_factor_2": "Коефіцієнт\nпотужності\n(Фаза 2)",
                "power_factor_3": "Коефіцієнт\nпотужності\n(Фаза 3)",
                "total_system_power": "Загальна\nпотужність\nсистеми",
                "total_system_VA": "Загальна потужність",
                "total_system_VAr": "Загальна реактивна потужність",
                "total_system_power_factor": "Коефіцієнт потужності системи",
                "total_import_kwh": "Загальне споживання (імпорт)",
                "total_export_kwh": "Загальне споживання (експорт)",
                "_1_to_2_voltage": "Напруга між\nФазою 1 і Фазою 2\n",
                "_2_to_3_voltage": "Напруга між\nФазою 2 і Фазою 3\n",
                "_3_to_1_voltage": "Напруга між\nФазою 3 і Фазою 1\n",
                "neutral_current": "Струм нейтралі\n",
                "total_kWh": "Загальна енергія\n",
                "total_kVArh": "Загальна реактивна\nенергія\n",
                "total_import_active_power": "Загальна імпортована\nактивна потужність\n",
                "total_export_active_power": "Загальна експортована\nактивна потужність\n"
            }
            self.column_labels_for_excel = self.column_labels.copy()
        else:
            self.column_labels = {}

    def open_export_dialog(self):
        self.dialog = QDialog(self)
        self.dialog.setWindowTitle("Експорт в Excel")
        self.dialog.setFixedSize(400, 150)

        layout = QVBoxLayout(self.dialog)

        date_range_layout = QHBoxLayout()
        start_label = QLabel("Початок:")
        self.start_export_date = QDateEdit(QDate.currentDate().addYears(-1))
        self.start_export_date.setCalendarPopup(True)
        end_label = QLabel("Кінець:")
        self.end_export_date = QDateEdit(QDate.currentDate())
        self.end_export_date.setCalendarPopup(True)
        date_range_layout.addWidget(start_label)
        date_range_layout.addWidget(self.start_export_date)
        date_range_layout.addWidget(end_label)
        date_range_layout.addWidget(self.end_export_date)

        layout.addLayout(date_range_layout)

        self.include_charts = QCheckBox("Додати графіки")
        self.include_charts.setChecked(False)
        if self.device_model == "SDM120":
            layout.addWidget(self.include_charts)

        save_button = QPushButton("Зберегти в Excel")
        save_button.clicked.connect(self.export_to_excel)
        layout.addWidget(save_button)

        self.dialog.setLayout(layout)
        self.dialog.exec()

    def export_to_excel(self):
        start_datetime = self.start_export_date.dateTime().toPython()
        end_datetime_for_name = self.end_export_date.dateTime().toPython()
        end_datetime = self.end_export_date.dateTime().addDays(1).toPython()

        async def run_export_to_excel():
            if self.device_model == "SDM120":
                report_model = SDM120Report
            elif self.device_model == "SDM630":
                report_model = SDM630Report
            elif self.device_model == "SDM72D":
                report_model = SDM72DReport
            else:
                return

            # Виконуємо асинхронний запит для отримання даних
            report_data = await report_model.filter(
                device_id=self.device.id,
                timestamp__gte=start_datetime,  # `__gte` означає ">="
                timestamp__lte=end_datetime  # `__lte` означає "<="
            ).order_by("timestamp").all()  # Сортування за `timestamp`

            if not report_data:
                QMessageBox.warning(self, "Експорт", "Дані за вибраний період відсутні.")
                return

            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Зберегти файл",
                f"{self.device.name}_{start_datetime.date()}_{end_datetime_for_name.date()}.xlsx",
                "Excel Files (*.xlsx)")

            if not file_path:
                return

            try:
                workbook = xlsxwriter.Workbook(file_path)

                # Визначення фаз та загальних колонок
                phases = {1: [], 2: [], 3: [], 'general': []}
                for column in self.column_labels_for_excel.keys():
                    if column == "timestamp":
                        continue
                    if "_1" in column:
                        phases[1].append(column)
                    elif "_2" in column:
                        phases[2].append(column)
                    elif "_3" in column:
                        phases[3].append(column)
                    else:
                        phases['general'].append(column)

                # Функція для запису даних у лист
                def write_sheet(worksheet, data, columns):
                    worksheet.write(0, 0, self.column_labels["timestamp"])
                    for col_idx, column in enumerate(columns, start=1):
                        worksheet.write(0, col_idx, self.column_labels_for_excel.get(column, column))

                    for row_idx, entry in enumerate(data, start=1):
                        worksheet.write(row_idx, 0, entry.timestamp.strftime('%Y-%m-%d %H:%M:%S'))
                        for col_idx, column in enumerate(columns, start=1):
                            value = getattr(entry, column, None)
                            worksheet.write(row_idx, col_idx, value)

                    worksheet.set_column(0, len(columns), 20)

                # Створення листів для кожної фази
                for phase, columns in phases.items():
                    if phase == 'general':
                        sheet_name = "Загальне"
                    else:
                        sheet_name = f"Фаза {phase}"

                    phase_data = [entry for entry in report_data if any(hasattr(entry, col) for col in columns)]
                    if not phase_data:
                        continue

                    worksheet = workbook.add_worksheet(sheet_name)
                    write_sheet(worksheet, phase_data, columns)

                if self.include_charts.isChecked():
                    parameters = {'line_voltage_1': 'Напруга', 'current_1': 'Струм', 'power_1': 'Потужність'}
                    for param in parameters.keys():
                        worksheet_param = workbook.add_worksheet(param)

                        worksheet_param.write('A1', 'Дата/Час')
                        worksheet_param.write('B1', param)

                        row = 1
                        for entry in report_data:
                            worksheet_param.write(row, 0, entry.timestamp.strftime('%Y-%m-%d %H:%M:%S'))
                            worksheet_param.write(row, 1, getattr(entry, param.lower()))
                            row += 1

                        worksheet_param.add_table(f'A1:B{row}', {'name': f'{param}_data',
                                                                 'columns': [{'header': 'Дата/Час'},
                                                                             {'header': parameters[param]}], })

                        chart = workbook.add_chart({'type': 'line'})
                        chart.add_series({'values': f'={param}!$B$2:$B${row}', 'name': parameters[param],
                                          'categories': f'={param}!$A$2:$A${row - 1}'})
                        chart.set_title({'name': parameters[param]})

                        chart.set_x_axis({'date_axis': True, 'num_format': 'yyyy-mm-dd hh:mm:ss'})

                        worksheet_param.insert_chart('D2', chart)

                        for col in range(4):
                            worksheet.set_column(col, col, 20)

                workbook.close()
                QMessageBox.information(self, "Експорт", "Експорт даних в Excel пройшов успішно.")
                self.dialog.accept()

            except Exception as e:
                QMessageBox.warning(self, "Помилка", f"Сталася помилка при експорті даних: {e}")
        AsyncioPySide6.runTask(run_export_to_excel())

    def create_phase_tab_sdm72d(self, phase_name):
        """Створює вкладку для заданої фази."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        top_layout = QVBoxLayout()
        bottom_layout = QHBoxLayout()

        voltage_graph = pg.PlotWidget()
        current_graph = pg.PlotWidget()
        energy_graph = pg.PlotWidget()

        if phase_name != "Загальне":
            voltage_graph.showGrid(x=True, y=True, alpha=0.5)
            current_graph.showGrid(x=True, y=True, alpha=0.5)
            voltage_graph.setAxisItems({'bottom': DateAxisItem(orientation='bottom')})
            current_graph.setAxisItems({'bottom': DateAxisItem(orientation='bottom')})
            voltage_graph.setLabel('left', 'Напруга', units='В')
            current_graph.setLabel('left', 'Струм', units='А')
            top_layout.addWidget(voltage_graph)
            top_layout.addWidget(current_graph)
        else:
            energy_graph.showGrid(x=True, y=True, alpha=0.5)
            energy_graph.setAxisItems({'bottom': DateAxisItem(orientation='bottom')})
            energy_graph.setLabel('left', 'Споживання', units='кВт·год')
            top_layout.addWidget(energy_graph)

        layout.addLayout(top_layout)

        bottom_left_layout = QGridLayout()

        clock_title = QLabel("Поточний час")
        clock_title.setStyleSheet("font-size: 16pt; font-weight: bold;")
        clock_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bottom_left_layout.addWidget(clock_title)

        clock_label = QLabel()
        clock_label.setStyleSheet("font-size: 16pt;")
        clock_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bottom_left_layout.addWidget(clock_label)

        layout.addStretch()

        indicators_layout = QGridLayout()

        voltage_label = QLabel("Напруга (V)")
        voltage_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        voltage_lcd = QLCDNumber()
        voltage_lcd.setStyleSheet("font-size: 18pt;")
        voltage_lcd.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)

        current_label = QLabel("Струм (A)")
        current_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        current_lcd = QLCDNumber()
        current_lcd.setStyleSheet("font-size: 18pt;")
        current_lcd.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)

        power_label = QLabel("Потужність (W)")
        power_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        power_lcd = QLCDNumber()
        power_lcd.setStyleSheet("font-size: 18pt;")
        power_lcd.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)

        energy_label = QLabel("Спожито (kWh)")
        energy_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        energy_lcd = QLCDNumber()
        energy_lcd.setStyleSheet("font-size: 18pt;")
        energy_lcd.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)

        if phase_name != "Загальне":
            indicators_layout.addWidget(voltage_label, 0, 0)
            indicators_layout.addWidget(voltage_lcd, 1, 0)
            indicators_layout.addWidget(current_label, 0, 1)
            indicators_layout.addWidget(current_lcd, 1, 1)
            indicators_layout.addWidget(power_label, 2, 0)
            indicators_layout.addWidget(power_lcd, 3, 0)
        indicators_layout.addWidget(energy_label, 2, 1)
        indicators_layout.addWidget(energy_lcd, 3, 1)

        bottom_layout.addLayout(bottom_left_layout)
        bottom_layout.addLayout(indicators_layout)

        layout.addLayout(bottom_layout)

        self.phase_data[phase_name] = {
            "tab": tab,
            "voltage_graph": voltage_graph,
            "current_graph": current_graph,
            "energy_graph": energy_graph,
            "voltage_lcd": voltage_lcd,
            "current_lcd": current_lcd,
            "power_lcd": power_lcd,
            "energy_lcd": energy_lcd,
            "clock_label": clock_label,
        }

        self.tabs.addTab(tab, phase_name)

    def update_graphs_sdm72d(self):
        for phase_name in self.phases:
            timestamps = []
            voltages = []
            currents = []
            energies = []

            for report in self.report_data:
                timestamps.append(report.timestamp)
                if phase_name == "Загальне":
                    energies.append(getattr(report, f'total_kWh'))
                else:
                    voltages.append(getattr(report, f'line_voltage_{self.phases.index(phase_name) + 1}'))
                    currents.append(getattr(report, f'current_{self.phases.index(phase_name) + 1}'))
            if phase_name != "Загальне":
                self.update_voltage_graph(timestamps, voltages, phase_name)
                self.update_current_graph(timestamps, currents, phase_name)
            else:
                hourly_energy = []
                hourly_timestamps = []

                last_energy = None
                current_hour_start = None
                current_hour_energy = 0.0

                for report in self.report_data:
                    current_hour = report.timestamp.replace(minute=0, second=0, microsecond=0)

                    if current_hour_start is None:
                        current_hour_start = current_hour

                    if current_hour != current_hour_start:
                        if last_energy is not None:
                            hourly_energy.append(current_hour_energy)
                            hourly_timestamps.append(current_hour_start)
                        current_hour_start = current_hour
                        current_hour_energy = 0.0
                    energy_value = getattr(report, f'total_kWh')

                    if last_energy is not None:
                        current_hour_energy += abs(energy_value - last_energy)

                    last_energy = energy_value

                if last_energy is not None:
                    hourly_energy.append(current_hour_energy)
                    hourly_timestamps.append(current_hour_start)

                self.update_energy_graph(hourly_timestamps, hourly_energy, phase_name)
