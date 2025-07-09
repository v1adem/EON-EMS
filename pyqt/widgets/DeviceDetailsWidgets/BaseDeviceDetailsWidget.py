import logging
import os
import sys
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

import pyqtgraph as pg
import xlsxwriter
from AsyncioPySide6 import AsyncioPySide6
from PySide6.QtCore import QTimer, QDate, Qt, QTime
from PySide6.QtGui import QStandardItemModel, QFont, QStandardItem, QIcon
from PySide6.QtWidgets import QToolTip
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSplitter, QLabel, QDateEdit, QTableView, QTabWidget, QHBoxLayout, \
    QCheckBox, QGridLayout, QLCDNumber, QDialog, QMessageBox, QFileDialog, QPushButton

from tools.config import resource_path
from pyqt.widgets.ConsoleWidget import ConsoleWidget, ConsoleOutputDuplicator
from pyqt.widgets.DateAxisItem import DateAxisItem
from register_maps.RegisterMaps import RegisterMap


class BaseDeviceDetailsWidget(QWidget):
    def __init__(self, main_window, device):
        super().__init__(main_window)
        self.report_model = None
        self.tmp_report_model = None
        self.auto_update_checkbox = None
        self.device = device
        self.device_model = self.device.model
        self.main_window = main_window

        self.column_labels, self.column_labels_for_excel = {}, {}
        self.phases = []

        self.phase_data = {}
        self.report_data = None

    def initUi(self):
        layout = QVBoxLayout(self)

        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.setChildrenCollapsible(False)
        layout.addWidget(main_splitter)

        # Left side
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        self.label = QLabel(f"Ім'я пристрою: {self.device.name} | Модель пристрою: {self.device.manufacturer} {self.device.model}")
        self.label.setStyleSheet("font-size: 16px;")
        left_layout.addWidget(self.label)

        self.start_date_table_filter = QDateEdit(self)
        self.end_date_table_filter = QDateEdit(self)
        self.create_filter_buttons(left_layout)

        self.report_table = QTableView(self)
        left_layout.addWidget(self.report_table)

        main_splitter.addWidget(left_widget)

        # Right side (Tabs)
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("font-size: 16px;")
        main_splitter.addWidget(self.tabs)

        for phase_name in self.phases:
            self.create_phase_tab(phase_name)

        self.set_light_theme()

        logger.info("Loading data...")

    def init_timers(self):
        self.timer_clock_indicator = QTimer(self)
        self.timer_clock_indicator.timeout.connect(self.update_clock_indicators)
        self.timer_clock_indicator.setInterval(1000)
        self.timer_clock_indicator.start()

        self.load_report_data()

        self.timer_update_all_tabs_graphs = QTimer(self)
        self.timer_update_all_tabs_graphs.timeout.connect(self.auto_update)
        self.timer_update_all_tabs_graphs.setInterval(self.device.reading_interval * 1000)
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
        if phase_name == "Загальне":
            console_widget = ConsoleWidget()
            bottom_left_layout.addWidget(console_widget, 0, 0, 2, 1)
            sys.stdout = ConsoleOutputDuplicator(console_widget, sys.__stdout__)
            logger.info(f"Console widget initialized in {self.device.name}")

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
            "clock_label": clock_label
        }

        voltage_plot_item = voltage_graph.plot([], [], pen=pg.mkPen(color=(0, 102, 204), width=2),
                                               name=f"Напруга {phase_name}")
        voltage_scatter_item = pg.ScatterPlotItem(pen=None, brush=(0, 102, 204), size=7)
        voltage_graph.addItem(voltage_scatter_item)
        setattr(self, f"voltage_plot_item_{phase_name}", voltage_plot_item)
        setattr(self, f"voltage_scatter_item_{phase_name}", voltage_scatter_item)

        current_plot_item = current_graph.plot([], [], pen=pg.mkPen(color=(204, 51, 0), width=2),
                                               name=f"Струм {phase_name}")
        current_scatter_item = pg.ScatterPlotItem(pen=None, brush=(204, 51, 0), size=7)
        current_graph.addItem(current_scatter_item)
        setattr(self, f"current_plot_item_{phase_name}", current_plot_item)
        setattr(self, f"current_scatter_item_{phase_name}", current_scatter_item)

        power_plot_item = power_graph.plot([], [], pen=pg.mkPen(color=(0, 255, 0), width=2),
                                           name=f"Потуж. {phase_name}")
        power_scatter_item = pg.ScatterPlotItem(pen=None, brush=(0, 255, 0), size=7)
        power_graph.addItem(power_scatter_item)
        setattr(self, f"power_plot_item_{phase_name}", power_plot_item)
        setattr(self, f"power_scatter_item_{phase_name}", power_scatter_item)

        self.tabs.addTab(tab, phase_name)

    def auto_update(self):
        if self.auto_update_checkbox.isChecked():
            self.load_report_data()

    def load_report_data(self):
        pass

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
        if not selected.indexes():
            return

        proxy_index = selected.indexes()[0]
        model = self.report_table.model()

        if hasattr(model, 'mapToSource'):
            source_index = model.mapToSource(proxy_index)
            row_index = source_index.row()
        else:
            row_index = proxy_index.row()

        if 0 <= row_index < len(self.report_data):
            selected_timestamp = self.report_data[row_index].timestamp
            self.center_graphs_on_timestamp(selected_timestamp)

    def update_clock_indicators(self):
        async def run_update_clock_indicators():
            current_time = QTime.currentTime().toString("HH:mm:ss")
            current_time += "\n" + QDate.currentDate().toString("dd.MM.yyyy")

            for phase_name, phase_data in self.phase_data.items():
                phase_data["clock_label"].setText(current_time)

            last_report = await self.tmp_report_model.filter(
                device_id=self.device.id
            ).order_by("-timestamp").first()

            if not last_report:
                return

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
        if not points or not self.report_data:
            return

        point_index = points[0].index()

        model = self.report_table.model()

        source_model = model.sourceModel() if hasattr(model, 'sourceModel') else model

        if 0 <= point_index < source_model.rowCount():
            if hasattr(model, 'mapFromSource'):
                proxy_index = model.mapFromSource(source_model.index(point_index, 0))
            else:
                proxy_index = source_model.index(point_index, 0)

            self.report_table.selectRow(proxy_index.row())
            self.report_table.scrollTo(proxy_index, QTableView.ScrollHint.PositionAtCenter)

            selected_timestamp = self.report_data[point_index].timestamp
            self.center_graphs_on_timestamp(selected_timestamp)

    def create_legend(self, graph_widget):
        legend = pg.LegendItem(offset=(70, 10), pen=None, brush=pg.mkBrush('w'))
        view_box = graph_widget.getViewBox()
        legend.setParentItem(view_box)
        legend.anchor(itemPos=(1, 0), parentPos=(1, 0), offset=(-10, 10))
        return legend

    def _update_single_phase_line_graph(self, timestamps, values, phase_name, graph_type):
        timestamps_numeric = [int(ts.timestamp()) for ts in timestamps]
        plot_item = getattr(self, f"{graph_type}_plot_item_{phase_name}")
        scatter = getattr(self, f"{graph_type}_scatter_item_{phase_name}")


        if not timestamps_numeric or not values:
            plot_item.setData([], [])
            scatter.setData([], [])
            return

        try:
            plot_item.setData(timestamps_numeric, values)
            scatter.setData([
                {'pos': (x, y), 'data': x}
                for x, y in zip(timestamps_numeric, values)
            ])

            if not hasattr(scatter, '_clicked_connected'):
                scatter.sigClicked.connect(self.on_graph_point_clicked)
                scatter._clicked_connected = True

        except Exception as e:
            logger.error(f"[_update_single_phase_line_graph] Error updating graph for {phase_name} - {graph_type}: {e}")

    def _update_general_line_graph(self, timestamps, all_phase_values, y_label, graph_type, color_shades):
        timestamps_numeric = [ts.timestamp() for ts in timestamps]
        graph_widget = self.phase_data["Загальне"][f"{graph_type}_graph"]

        items_to_remove = []
        for item in graph_widget.items():
            if isinstance(item, pg.PlotDataItem) or isinstance(item, pg.ScatterPlotItem):
                items_to_remove.append(item)
        for item in items_to_remove:
            graph_widget.removeItem(item)

        if hasattr(graph_widget, 'legend') and graph_widget.legend is not None:
            if hasattr(graph_widget.legend, 'clear'):
                graph_widget.legend.clear()
            else:
                if graph_widget.legend is not None:
                    graph_widget.removeItem(graph_widget.legend)
                del graph_widget.legend

        if not hasattr(graph_widget, 'legend') or graph_widget.legend is None:
            legend = self.create_legend(graph_widget)
        else:
            legend = graph_widget.legend

        try:
            for i, phase_values in enumerate(all_phase_values):
                color = color_shades[i % len(color_shades)]

                pen = pg.mkPen(color=color, width=2)
                plot_item = graph_widget.plot(timestamps_numeric, phase_values, pen=pen,
                                              name=f"{y_label} {self.phases[i + 1]}")
                legend.addItem(plot_item,
                               f"{self.phases[i + 1]}")

                scatter = pg.ScatterPlotItem(pen=None, brush=color, size=7)
                scatter.setData([
                    {'pos': (x, y), 'data': x}
                    for x, y in zip(timestamps_numeric, phase_values)
                ])
                if not hasattr(scatter, '_clicked_connected'):
                    scatter.sigClicked.connect(self.on_graph_point_clicked)
                    scatter._clicked_connected = True
                graph_widget.addItem(scatter)

        except Exception as e:
            logger.error(f"[_update_general_line_graph] Error updating graph: {e}")

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
            logger.info(f"Loading phase - {phase_name}")

            timestamps = []
            voltages = []
            currents = []
            powers = []
            energies = []

            hourly_energy = []
            hourly_timestamps = []

            last_energy = None
            current_hour_start = None
            current_hour_energy = 0.0

            for report in self.report_data:
                try:
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
                        energies.append(report.total_kWh)
                    else:
                        voltage = getattr(report, f'line_voltage_{self.phases.index(phase_name)}')
                        current = getattr(report, f'current_{self.phases.index(phase_name)}')
                        power = getattr(report, f'power_{self.phases.index(phase_name)}')

                        voltages.append(voltage)
                        currents.append(current)
                        powers.append(power)

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
                        energy_value = getattr(report, 'total_kWh')
                    else:
                        energy_value = getattr(report, f'total_kWh_{self.phases.index(phase_name)}')


                    if last_energy is not None:
                        current_hour_energy += abs(energy_value - last_energy)

                    last_energy = energy_value

                    if last_energy is not None:
                        hourly_energy.append(current_hour_energy)
                        hourly_timestamps.append(current_hour_start)

                except Exception as e:
                    logger.warning(e)
                    continue
            try:
                if phase_name != "Загальне":
                    self._update_single_phase_line_graph(timestamps, voltages, phase_name, "voltage")
                    self._update_single_phase_line_graph(timestamps, currents, phase_name, "current")
                    self._update_single_phase_line_graph(timestamps, powers, phase_name, "power")
                    self.add_tooltips(self.phase_data[phase_name]["voltage_graph"], timestamps, voltages)
                    self.add_tooltips(self.phase_data[phase_name]["current_graph"], timestamps, currents)
                    self.add_tooltips(self.phase_data[phase_name]["power_graph"], timestamps, powers)
                else:
                    transposed_voltages = list(zip(*voltages))
                    transposed_currents = list(zip(*currents))
                    transposed_powers = list(zip(*powers))
                    self._update_general_line_graph(timestamps, transposed_voltages, "Напруга", "voltage",
                                                    color_shades=[(0, 0, 153), (0, 102, 204), (0, 153, 255)])
                    self._update_general_line_graph(timestamps, transposed_currents, "Струм", "current",
                                                    color_shades=[(153, 0, 0), (204, 51, 0), (255, 102, 0)])
                    self._update_general_line_graph(timestamps, transposed_powers, "Потуж.", "power",
                                                    color_shades=[(0, 153, 0), (51, 204, 0), (102, 255, 0)])

                self.update_energy_graph(hourly_timestamps, hourly_energy, phase_name)
            except Exception as e:
                logger.error(e)


    def center_graphs_on_timestamp(self, timestamp):
        for phase_name in self.phases:
            graph_widgets = [
                self.phase_data[phase_name]["voltage_graph"],
                self.phase_data[phase_name]["current_graph"],
                self.phase_data[phase_name]["power_graph"],
                self.phase_data[phase_name]["energy_graph"]
            ]

            for graph_widget in graph_widgets:
                min_time = timestamp - timedelta(minutes=300)
                max_time = timestamp + timedelta(minutes=300)

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

        # Remove when charts will be for all models
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
            report_data = await self.report_model.filter(
                device_id=self.device.id,
                timestamp__gte=start_datetime,
                timestamp__lte=end_datetime
            ).order_by("timestamp").all()

            if not report_data:
                QMessageBox.warning(self, "Експорт", "Дані за вибраний період відсутні.")
                return

            desktop_reports_path = os.path.join(os.path.expanduser("~"), "Desktop", "Reports")
            os.makedirs(desktop_reports_path, exist_ok=True)

            default_filename = f"{self.device.name}_{start_datetime.date()}_{end_datetime_for_name.date()}.xlsx"
            default_path = os.path.join(desktop_reports_path, default_filename)

            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Зберегти файл",
                default_path,
                "Excel Files (*.xlsx)"
            )

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
