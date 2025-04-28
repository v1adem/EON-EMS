import sys
from datetime import datetime, timedelta
import logging
logger = logging.getLogger(__name__)

import pyqtgraph as pg
import xlsxwriter
from AsyncioPySide6 import AsyncioPySide6
from PySide6.QtCore import QTimer, QDate, Qt, QSortFilterProxyModel, QTime
from PySide6.QtGui import QStandardItemModel, QFont, QStandardItem, QIcon
from PySide6.QtWidgets import QToolTip
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSplitter, QLabel, QDateEdit, QTableView, QTabWidget, QHBoxLayout, \
    QPushButton, QCheckBox, QGridLayout, QLCDNumber, QDialog, QMessageBox, QFileDialog

from tools.config import resource_path
from models.Report import SDM630Report, SDM630ReportTmp, SDM120Report, SDM120ReportTmp, SDM72Report, SDM72ReportTmp
from pyqt.widgets.ConsoleWidget import ConsoleWidget
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
        elif self.device_model == "SDM630" or self.device_model == "SDM72":
            self.phases = ["Фаза 1", "Фаза 2", "Фаза 3", "Загальне"]

        for phase_name in self.phases:
            if self.device_model == "SDM72":
                self.create_phase_tab_sdm72(phase_name)
            else:
                self.create_phase_tab(phase_name)

        self.set_light_theme()

        self.timer_clock_indicator = QTimer(self)
        self.timer_clock_indicator.timeout.connect(self.update_clock_indicators)
        self.timer_clock_indicator.setInterval(1000)
        self.timer_clock_indicator.start()

        self.load_report_data()

        self.timer_update_all_tabs_graphs = QTimer(self)
        self.timer_update_all_tabs_graphs.timeout.connect(self.auto_update)
        self.timer_update_all_tabs_graphs.setInterval(device.reading_interval * 1000)
        self.timer_update_all_tabs_graphs.start()

    def create_filter_buttons(self, layout):
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

        update_button = QPushButton("Оновити")
        update_button.setIcon(QIcon(resource_path("pyqt/icons/refresh.png")))
        update_button.setStyleSheet("font-size: 16px;")
        update_button.clicked.connect(self.load_report_data)
        button_layout.addWidget(update_button)

        export_button = QPushButton("Експорт в Excel")
        export_button.setStyleSheet("font-size: 16px;")
        export_button.setFixedHeight(36)
        export_button.clicked.connect(self.open_export_dialog)
        button_layout.addWidget(export_button)

        layout.addLayout(button_layout)

    def create_phase_tab(self, phase_name):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        top_layout = QVBoxLayout()
        bottom_layout = QHBoxLayout()

        voltage_graph = pg.PlotWidget()
        current_graph = pg.PlotWidget()
        power_graph = pg.PlotWidget()
        voltage_graph.showGrid(x=True, y=True, alpha=0.5)
        current_graph.showGrid(x=True, y=True, alpha=0.5)
        power_graph.showGrid(x=True, y=True, alpha=0.5)
        voltage_graph.setAxisItems({'bottom': DateAxisItem(orientation='bottom')})
        current_graph.setAxisItems({'bottom': DateAxisItem(orientation='bottom')})
        power_graph.setAxisItems({'bottom': DateAxisItem(orientation='bottom')})
        voltage_graph.setLabel('left', 'Напруга', units='V')
        current_graph.setLabel('left', 'Струм', units='А')
        power_graph.setLabel('left', 'Потужність', units='W')
        top_layout.addWidget(voltage_graph)
        top_layout.addWidget(current_graph)
        top_layout.addWidget(power_graph)

        energy_graph = pg.PlotWidget()
        energy_graph.showGrid(x=True, y=True, alpha=0.5)
        energy_graph.setAxisItems({'bottom': DateAxisItem(orientation='bottom')})
        energy_graph.setLabel('left', 'Спожито', units='kWh')
        top_layout.addWidget(energy_graph)

        current_graph.setXLink(voltage_graph)
        energy_graph.setXLink(voltage_graph)
        power_graph.setXLink(voltage_graph)

        layout.addLayout(top_layout)

        bottom_left_layout = QGridLayout()

        console_widget = ConsoleWidget()
        bottom_left_layout.addWidget(console_widget, 0, 0, 2, 1)  # Розташування консолі ліворуч

        clock_title = QLabel("Поточний час")
        clock_title.setStyleSheet("font-size: 16pt; font-weight: bold;")
        clock_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bottom_left_layout.addWidget(clock_title, 0, 1)

        clock_label = QLabel()
        clock_label.setStyleSheet("font-size: 16pt;")
        clock_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bottom_left_layout.addWidget(clock_label, 1, 1)

        layout.addStretch()

        indicators_layout = QGridLayout()

        voltage_label = QLabel("Напруга (V)")
        voltage_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        voltage_lcd = QLCDNumber()
        voltage_lcd.setStyleSheet("font-size: 18pt;")
        voltage_lcd.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)
        voltage_lcd.setDigitCount(10)

        current_label = QLabel("Струм (A)")
        current_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        current_lcd = QLCDNumber()
        current_lcd.setStyleSheet("font-size: 18pt;")
        current_lcd.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)
        current_lcd.setDigitCount(10)

        power_label = QLabel("Потужність (W)")
        power_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        power_lcd = QLCDNumber()
        power_lcd.setStyleSheet("font-size: 18pt;")
        power_lcd.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)
        power_lcd.setDigitCount(10)

        energy_label = QLabel("Спожито (kWh)")
        energy_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        energy_lcd = QLCDNumber()
        energy_lcd.setStyleSheet("font-size: 18pt;")
        energy_lcd.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)
        energy_lcd.setDigitCount(10)

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
            "power_graph": power_graph,
            "voltage_lcd": voltage_lcd,
            "current_lcd": current_lcd,
            "power_lcd": power_lcd,
            "energy_lcd": energy_lcd,
            "clock_label": clock_label,
            "console_widget": console_widget,  # Додавання консолі в phase_data
        }

        self.tabs.addTab(tab, phase_name)

        sys.stdout = console_widget  # Перенаправлення виводу на консоль
        logger.info("Console initialized")

    def auto_update(self):
        if not self.auto_update_checkbox.isChecked():
            return
        self.load_report_data()

    def load_report_data(self):
        async def run_load_report_data():
            start_date = self.start_date_table_filter.date().toPython()
            end_date = self.end_date_table_filter.date().addDays(1).toPython()

            if self.device_model == "SDM120":
                report_model = SDM120Report
            elif self.device_model == "SDM630":
                report_model = SDM630Report
            elif self.device_model == "SDM72":
                report_model = SDM72Report
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
            self.report_table.setSortingEnabled(True)
            self.report_table.resizeColumnsToContents()
            self.setup_table_click_handler(self.report_table)

            if self.device_model == "SDM72":
                self.update_graphs_sdm72()
            else:
                self.update_graphs()

        AsyncioPySide6.runTask(run_load_report_data())
        self.main_window.hide_loading()
        self.report_table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)

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

    def setup_table_click_handler(self, table_view):
        selection_model = table_view.selectionModel()
        if selection_model is not None:
            selection_model.selectionChanged.connect(self.on_table_row_selected)

    def on_table_row_selected(self, selected):
        if selected.indexes():
            row_index = selected.indexes()[0].row()
            self.center_graphs_on_table_row(row_index)

    def update_clock_indicators(self):
        async def run_update_clock_indicators():
            current_time = QTime.currentTime().toString("HH:mm:ss")
            current_time += "\n" + QDate.currentDate().toString("dd.MM.yyyy")

            for phase_name, phase_data in self.phase_data.items():
                phase_data["clock_label"].setText(current_time)

            if self.device_model == "SDM120":
                report_model = SDM120ReportTmp
            elif self.device_model == "SDM630":
                report_model = SDM630ReportTmp
            elif self.device_model == "SDM72":
                report_model = SDM72ReportTmp
            else:
                return

            last_report = await report_model.filter(
                device_id=self.device.id
            ).order_by("-timestamp").first()

            if not last_report:
                return

            if self.device_model == "SDM72":
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
                    voltage_lcd.display(f"{data['voltage']:.2f}")
                if current_lcd and "current" in data:
                    current_lcd.display(f"{data['current']:.2f}")
                if power_lcd and "power" in data:
                    power_lcd.display(f"{data['power']:.2f}")
                if energy_lcd and "energy" in data:
                    energy_lcd.display(f"{data['energy']:.2f}")

        AsyncioPySide6.runTask(run_update_clock_indicators())

    def add_tooltips(self, graph_widget, timestamps, values):
        points = list(zip(timestamps, values))

        def on_mouse_moved(evt):
            pos = evt
            if graph_widget.sceneBoundingRect().contains(pos):
                mouse_point = graph_widget.plotItem.vb.mapSceneToView(pos)
                x = mouse_point.x()
                y = mouse_point.y()

                if points:
                    points_with_timestamps = [(p[0].timestamp() if isinstance(p[0], datetime) else p[0], p[1]) for p in
                                              points]

                    closest_point_with_timestamp = min(points_with_timestamps,
                                                       key=lambda p: (p[0] - x) ** 2 + (p[1] - y) ** 2)

                    tooltip_text = f"{closest_point_with_timestamp[1]:.2f}"

                    QToolTip.showText(
                        graph_widget.mapToGlobal(graph_widget.mapFromScene(pos)), tooltip_text
                    )

        graph_widget.scene().sigMouseMoved.connect(on_mouse_moved)

    def on_graph_point_clicked(self, plot, points):
        if not points:
            return

        point = points[0]
        x_value = point.pos().x()
        x_value -= 7200

        model = self.report_table.model()
        timestamp_column_index = -1
        for column in range(model.columnCount()):
            header_text = model.headerData(column, Qt.Orientation.Horizontal)
            if "час" in header_text.lower():
                timestamp_column_index = column
                break

        if timestamp_column_index == -1:
            return

        closest_row = -1
        min_time_diff = float('inf')

        for row in range(model.rowCount()):
            index = model.index(row, timestamp_column_index)
            table_timestamp_str = index.data()

            try:
                table_datetime = datetime.strptime(table_timestamp_str, "%Y-%m-%d %H:%M:%S")
                table_timestamp = table_datetime.timestamp()
            except ValueError:
                logger.error(f"Time convert error in row - {row}: {table_timestamp_str}")
                continue

            time_diff = abs(table_timestamp - x_value)
            if time_diff < min_time_diff:
                min_time_diff = time_diff
                closest_row = row

        if closest_row != -1:
            self.report_table.selectRow(closest_row)
            self.report_table.scrollTo(model.index(closest_row, 0))
            self.report_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        else:
            logger.error("Row is not found")

    def update_voltage_graph(self, timestamps, voltages, phase_name):
        timestamps_numeric = [ts.timestamp() for ts in timestamps]
        graph_widget = self.phase_data[phase_name]["voltage_graph"]

        if phase_name == "Загальне":
            graph_widget.clear()
            legend = pg.LegendItem(offset=(70, 10), pen=pg.mkPen(None), brush=pg.mkBrush('w'))

            view_box = graph_widget.getViewBox()
            legend.setParentItem(view_box)  # Робимо ViewBox батьківським елементом для легенди
            legend.anchor(itemPos=(1, 0), parentPos=(1, 0), offset=(-10, 10))
            blue_shades = [(0, 0, 153), (0, 102, 204), (0, 153, 255)]

            for i in range(len(voltages)):  # num_phases замінено на len(voltages)
                color = blue_shades[i % len(blue_shades)]
                pen = pg.mkPen(color=color, width=2)
                phase_voltages = voltages[i]

                plot_item = graph_widget.plot(timestamps_numeric, phase_voltages, pen=pen,
                                              name=f"Напруга {self.phases[i]}")

                scatter = pg.ScatterPlotItem(pen=None, brush=color, size=7)
                scatter.setData(x=timestamps_numeric, y=phase_voltages)  # Оновлюємо scatter plot
                scatter.sigClicked.connect(self.on_graph_point_clicked)
                graph_widget.addItem(scatter)
                legend.addItem(plot_item, f"{self.phases[i]}")

            graph_widget.scene().addItem(legend)

        else:
            plot_attr = f"voltage_plot_item_{phase_name}"
            scatter_attr = f"voltage_scatter_item_{phase_name}"

            if not hasattr(self, plot_attr):
                plot_item = graph_widget.plot(timestamps_numeric, voltages, pen=pg.mkPen(color=(0, 102, 204), width=2),
                                              name=f"Напруга {phase_name}")
                setattr(self, plot_attr, plot_item)

                scatter = pg.ScatterPlotItem(pen=None, brush='b', size=7)
                scatter.setData(x=timestamps_numeric, y=voltages)
                scatter.sigClicked.connect(self.on_graph_point_clicked)
                graph_widget.addItem(scatter)
                setattr(self, scatter_attr, scatter)

            else:
                plot_item = getattr(self, plot_attr)
                plot_item.setData(timestamps_numeric, voltages)

                scatter = getattr(self, scatter_attr)
                scatter.setData(x=timestamps_numeric, y=voltages)

    def update_current_graph(self, timestamps, currents, phase_name):
        timestamps_numeric = [ts.timestamp() for ts in timestamps]
        graph_widget = self.phase_data[phase_name]["current_graph"]

        if phase_name == "Загальне":
            graph_widget.clear()  # Очищаємо перед перемалюванням
            legend = pg.LegendItem(offset=(70, 10), pen=pg.mkPen(None), brush=pg.mkBrush('w'))

            view_box = graph_widget.getViewBox()
            legend.setParentItem(view_box)  # Робимо ViewBox батьківським елементом для легенди
            legend.anchor(itemPos=(1, 0), parentPos=(1, 0), offset=(-10, 10))
            red_shades = [(153, 0, 0), (204, 51, 0), (255, 102, 0)]

            for i in range(len(currents)):  # num_phases замінено на len(currents)
                color = red_shades[i % len(red_shades)]
                pen = pg.mkPen(color=color, width=2)
                phase_currents = currents[i]

                plot_item = graph_widget.plot(timestamps_numeric, phase_currents, pen=pen,
                                              name=f"Струм {self.phases[i]}")

                scatter = pg.ScatterPlotItem(pen=None, brush=color, size=7)
                scatter.setData(x=timestamps_numeric, y=phase_currents)  # Оновлюємо scatter plot
                scatter.sigClicked.connect(self.on_graph_point_clicked)
                graph_widget.addItem(scatter)
                legend.addItem(plot_item, f"{self.phases[i]}")


        else:  # Single phase
            plot_attr = f"current_plot_item_{phase_name}"
            scatter_attr = f"current_scatter_item_{phase_name}"  # Атрибут для scatter plot

            if not hasattr(self, plot_attr):
                # Створюємо plot item та scatter plot
                plot_item = graph_widget.plot(timestamps_numeric, currents, pen=pg.mkPen(color=(204, 51, 0), width=2),
                                              name=f"Струм {phase_name}")
                setattr(self, plot_attr, plot_item)

                scatter = pg.ScatterPlotItem(pen=None, brush='r', size=7)
                scatter.setData(x=timestamps_numeric, y=currents)
                scatter.sigClicked.connect(self.on_graph_point_clicked)
                graph_widget.addItem(scatter)
                setattr(self, scatter_attr, scatter)

            else:
                plot_item = getattr(self, plot_attr)
                plot_item.setData(timestamps_numeric, currents)

                scatter = getattr(self, scatter_attr)
                scatter.setData(x=timestamps_numeric, y=currents)

    def update_power_graph(self, timestamps, powers, phase_name):
        timestamps_numeric = [ts.timestamp() for ts in timestamps]
        graph_widget = self.phase_data[phase_name]["power_graph"]

        if phase_name == "Загальне":
            graph_widget.clear()
            legend = pg.LegendItem(offset=(70, 10), pen=pg.mkPen(None), brush=pg.mkBrush('w'))

            view_box = graph_widget.getViewBox()
            legend.setParentItem(view_box)
            legend.anchor(itemPos=(1, 0), parentPos=(1, 0), offset=(-10, 10))
            green_shades = [(0, 153, 0), (51, 204, 0), (102, 255, 0)]

            for i in range(len(powers)):
                color = green_shades[i % len(green_shades)]
                pen = pg.mkPen(color=color, width=2)
                phase_powers = powers[i]

                plot_item = graph_widget.plot(timestamps_numeric, phase_powers, pen=pen,
                                              name=f"Потуж. {self.phases[i]}")

                scatter = pg.ScatterPlotItem(pen=None, brush=color, size=7)
                scatter.setData(x=timestamps_numeric, y=phase_powers)
                scatter.sigClicked.connect(self.on_graph_point_clicked)
                graph_widget.addItem(scatter)
                legend.addItem(plot_item, f"{self.phases[i]}")


        else:  # Single phase
            plot_attr = f"power_plot_item_{phase_name}"
            scatter_attr = f"power_scatter_item_{phase_name}"

            if not hasattr(self, plot_attr):
                plot_item = graph_widget.plot(timestamps_numeric, powers, pen=pg.mkPen(color=(0, 255, 0), width=2),
                                              name=f"Потуж. {phase_name}")
                setattr(self, plot_attr, plot_item)

                scatter = pg.ScatterPlotItem(pen=None, brush='g', size=7)
                scatter.setData(x=timestamps_numeric, y=powers)
                scatter.sigClicked.connect(self.on_graph_point_clicked)
                graph_widget.addItem(scatter)
                setattr(self, scatter_attr, scatter)

            else:
                plot_item = getattr(self, plot_attr)
                plot_item.setData(timestamps_numeric, powers)

                scatter = getattr(self, scatter_attr)
                scatter.setData(x=timestamps_numeric, y=powers)

    def update_energy_graph(self, hourly_timestamps, hourly_energy, phase_name):
        if not hourly_timestamps or not hourly_energy:
            return

        hourly_timestamps_numeric = [ts.timestamp() for ts in hourly_timestamps]
        valid_data = [
            (ts, energy) for ts, energy in zip(hourly_timestamps_numeric, hourly_energy)
            if energy > 0
        ]

        if not valid_data:
            return

        bar_attr = f"energy_bar_items_{phase_name}"
        graph_widget = self.phase_data[phase_name]["energy_graph"]

        graph_widget.clear()

        energy_bar_items = []

        for i, (ts, energy) in enumerate(valid_data):
            current_time = datetime.fromtimestamp(ts)
            hour_start = current_time.replace(minute=0, second=0, microsecond=0).timestamp()
            hour_end = hour_start + 3600

            if i == 0:
                first_report_timestamp = self.report_data[0].timestamp.timestamp()
                start_time = first_report_timestamp
                end_time = hour_end
            else:
                start_time = hour_start
                end_time = hour_end

            bar_item = pg.BarGraphItem(
                x0=start_time,
                x1=end_time,
                height=energy,
                brush='g'
            )
            energy_bar_items.append(bar_item)
            graph_widget.addItem(bar_item)

        y_max = max(energy for _, energy in valid_data)
        graph_widget.setYRange(0, y_max, padding=0.1)

        x_min = min(ts for ts, _ in valid_data)
        x_max = max(hour_end for ts, _ in valid_data)
        graph_widget.setXRange(x_min, x_max, padding=0.1)

        setattr(self, bar_attr, energy_bar_items)

    def update_graphs(self):
        for phase_name in self.phases:
            timestamps = []
            voltages = []
            currents = []
            powers = []
            energies = []

            for report in self.report_data:
                timestamps.append(report.timestamp)
                energies.append(getattr(report,
                                        f'total_kWh_{self.phases.index(phase_name) + 1}' if phase_name != "Загальне" else 'total_kWh'))
                if phase_name == "Загальне":
                    voltages_for_general = []
                    currents_for_general = []
                    powers_for_general = []
                    for i in range(len(self.phases) - 1):  # -1 щоб не включати "Загальне"
                        voltages_for_general.append(getattr(report, f'line_voltage_{i + 1}'))
                        currents_for_general.append(getattr(report, f'current_{i + 1}'))
                        powers_for_general.append(getattr(report, f'power_{i + 1}'))
                    voltages.append(voltages_for_general)
                    currents.append(currents_for_general)
                    powers.append(powers_for_general)
                else:
                    voltages.append(getattr(report, f'line_voltage_{self.phases.index(phase_name) + 1}'))
                    currents.append(getattr(report, f'current_{self.phases.index(phase_name) + 1}'))
                    powers.append(getattr(report, f'power_{self.phases.index(phase_name) + 1}'))

            if phase_name != "Загальне":
                self.update_voltage_graph(timestamps, voltages, phase_name)
                self.update_current_graph(timestamps, currents, phase_name)
                self.update_power_graph(timestamps, powers, phase_name)

                self.add_tooltips(self.phase_data[phase_name]["voltage_graph"], timestamps, voltages)
                self.add_tooltips(self.phase_data[phase_name]["current_graph"], timestamps, currents)
                self.add_tooltips(self.phase_data[phase_name]["power_graph"], timestamps, powers)

            else:
                transposed_voltages = list(zip(*voltages))
                transposed_currents = list(zip(*currents))
                transposed_powers = list(zip(*powers))

                self.update_voltage_graph(timestamps, transposed_voltages, phase_name)
                self.update_current_graph(timestamps, transposed_currents, phase_name)
                self.update_power_graph(timestamps, transposed_powers, phase_name)

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

    def center_graphs_on_table_row(self, row_index):
        if not self.report_data:
            return

        source_index = self.report_table.model().mapToSource(self.report_table.model().index(row_index, 0))
        source_row = source_index.row()

        selected_report = self.report_data[source_row]
        selected_timestamp = selected_report.timestamp

        for phase_name in self.phases:
            graph_widgets = [
                self.phase_data[phase_name]["voltage_graph"],
                self.phase_data[phase_name]["current_graph"],
                self.phase_data[phase_name]["power_graph"],
                self.phase_data[phase_name]["energy_graph"]
            ]

            for graph_widget in graph_widgets:
                min_time = selected_timestamp - timedelta(hours=1)
                max_time = selected_timestamp + timedelta(hours=1)

                min_timestamp_numeric = min_time.timestamp()
                max_timestamp_numeric = max_time.timestamp()

                graph_widget.setXRange(min_timestamp_numeric, max_timestamp_numeric, padding=0)

    def set_light_theme(self):
        for phase_name, phase_data in self.phase_data.items():
            phase_data["voltage_graph"].setBackground('w')
            phase_data["voltage_graph"].plot([], pen=pg.mkPen(color='b', width=2))
            phase_data["current_graph"].setBackground('w')
            phase_data["current_graph"].plot([], pen=pg.mkPen(color='r', width=2))
            phase_data["power_graph"].setBackground('w')
            phase_data["power_graph"].plot([], pen=pg.mkPen(color='g', width=2))
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
                "total_reactive_energy": "Загальна реактивна енергія kVArh",
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
        elif self.device_model == "SDM72":
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
            elif self.device_model == "SDM72":
                report_model = SDM72Report
            else:
                return

            report_data = await report_model.filter(
                device_id=self.device.id,
                timestamp__gte=start_datetime,
                timestamp__lte=end_datetime
            ).order_by("timestamp").all()

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

    def create_phase_tab_sdm72(self, phase_name):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        top_layout = QVBoxLayout()
        bottom_layout = QHBoxLayout()

        voltage_graph = pg.PlotWidget()
        current_graph = pg.PlotWidget()
        power_graph = pg.PlotWidget()
        energy_graph = pg.PlotWidget()

        voltage_graph.showGrid(x=True, y=True, alpha=0.5)
        current_graph.showGrid(x=True, y=True, alpha=0.5)
        power_graph.showGrid(x=True, y=True, alpha=0.5)
        voltage_graph.setAxisItems({'bottom': DateAxisItem(orientation='bottom')})
        current_graph.setAxisItems({'bottom': DateAxisItem(orientation='bottom')})
        power_graph.setAxisItems({'bottom': DateAxisItem(orientation='bottom')})
        voltage_graph.setLabel('left', 'Напруга', units='V')
        current_graph.setLabel('left', 'Струм', units='А')
        power_graph.setLabel('left', 'Потуж.', units='W')
        top_layout.addWidget(voltage_graph)
        top_layout.addWidget(current_graph)
        top_layout.addWidget(power_graph)

        if phase_name == "Загальне":
            energy_graph.showGrid(x=True, y=True, alpha=0.5)
            energy_graph.setAxisItems({'bottom': DateAxisItem(orientation='bottom')})
            energy_graph.setLabel('left', 'Спожито', units='kWh')
            top_layout.addWidget(energy_graph)

        current_graph.setXLink(voltage_graph)
        energy_graph.setXLink(voltage_graph)
        power_graph.setXLink(voltage_graph)

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
        voltage_lcd.setDigitCount(10)

        current_label = QLabel("Струм (A)")
        current_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        current_lcd = QLCDNumber()
        current_lcd.setStyleSheet("font-size: 18pt;")
        current_lcd.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)
        current_lcd.setDigitCount(10)

        power_label = QLabel("Потужність (W)")
        power_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        power_lcd = QLCDNumber()
        power_lcd.setStyleSheet("font-size: 18pt;")
        power_lcd.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)
        power_lcd.setDigitCount(10)

        energy_label = QLabel("Спожито (kWh)")
        energy_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        energy_lcd = QLCDNumber()
        energy_lcd.setStyleSheet("font-size: 18pt;")
        energy_lcd.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)
        energy_lcd.setDigitCount(10)

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
            "power_graph": power_graph,
            "energy_graph": energy_graph,
            "voltage_lcd": voltage_lcd,
            "current_lcd": current_lcd,
            "power_lcd": power_lcd,
            "energy_lcd": energy_lcd,
            "clock_label": clock_label,
        }

        self.tabs.addTab(tab, phase_name)

    def update_graphs_sdm72(self):
        for phase_name in self.phases:
            timestamps = []
            voltages = []
            currents = []
            powers = []

            for report in self.report_data:
                timestamps.append(report.timestamp)
                if phase_name == "Загальне":
                    voltages_for_general = []
                    currents_for_general = []
                    powers_for_general = []
                    for i in range(len(self.phases) - 1):
                        voltages_for_general.append(getattr(report, f'line_voltage_{i + 1}'))
                        currents_for_general.append(getattr(report, f'current_{i + 1}'))
                        powers_for_general.append(getattr(report, f'power_{i + 1}'))
                    voltages.append(voltages_for_general)
                    currents.append(currents_for_general)
                    powers.append(powers_for_general)
                else:
                    voltages.append(getattr(report, f'line_voltage_{self.phases.index(phase_name) + 1}'))
                    currents.append(getattr(report, f'current_{self.phases.index(phase_name) + 1}'))
                    powers.append(getattr(report, f'power_{self.phases.index(phase_name) + 1}'))
            if phase_name != "Загальне":
                self.update_voltage_graph(timestamps, voltages, phase_name)
                self.update_current_graph(timestamps, currents, phase_name)
                self.update_power_graph(timestamps, powers, phase_name)

                self.add_tooltips(self.phase_data[phase_name]["voltage_graph"], timestamps, voltages)
                self.add_tooltips(self.phase_data[phase_name]["current_graph"], timestamps, currents)
                self.add_tooltips(self.phase_data[phase_name]["power_graph"], timestamps, powers)
            else:
                transposed_voltages = list(zip(*voltages))
                transposed_currents = list(zip(*currents))
                transposed_powers = list(zip(*powers))
                self.update_voltage_graph(timestamps, transposed_voltages, phase_name)
                self.update_current_graph(timestamps, transposed_currents, phase_name)
                self.update_power_graph(timestamps, transposed_powers, phase_name)

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