import asyncio
import logging
import sys

from pyqt.widgets.DeviceDetailsWidgets.BaseDeviceDetailsWidget import BaseDeviceDetailsWidget

logger = logging.getLogger(__name__)

import pyqtgraph as pg
from PySide6.QtCore import Qt, QSortFilterProxyModel
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableView, QHBoxLayout, \
    QGridLayout, QLCDNumber

from models.Report import SDM72Report, SDM72ReportTmp
from pyqt.widgets.ConsoleWidget import ConsoleWidget, ConsoleOutputDuplicator
from pyqt.widgets.DateAxisItem import DateAxisItem


class SDM72DeviceDetailsWidget(BaseDeviceDetailsWidget):
    def __init__(self, parent=None, device=None):
        super(SDM72DeviceDetailsWidget, self).__init__(parent, device)
        self.column_labels, self.column_labels_for_excel = self.init_column_labels()
        self.phases = ["Загальне", "Фаза 1", "Фаза 2", "Фаза 3"]
        self.report_model = SDM72Report
        self.tmp_report_model = SDM72ReportTmp

        self.initUi()
        BaseDeviceDetailsWidget.init_timers(self)

    def init_column_labels(self):
        column_labels = {
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
        column_labels_for_excel = column_labels.copy()
        return column_labels, column_labels_for_excel

    def create_phase_tab(self, phase_name):
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

    def load_report_data(self, initial_limit=True):

        async def run_load_report_data():
            if initial_limit:
                self.report_data = await SDM72Report.filter(
                    device_id=self.device.id
                ).order_by("-timestamp").limit(1000)
                self.report_data.reverse()
            else:
                start_date = self.start_date_table_filter.date().toPython()
                end_date = self.end_date_table_filter.date().addDays(1).toPython()

                self.report_data = await SDM72Report.filter(
                    device_id=self.device.id,
                    timestamp__gte=start_date,
                    timestamp__lte=end_date
                ).order_by("timestamp").all()

            if not self.report_data:
                return

            self.normalize_report_timestamps()

            model = self.create_table_model(self.report_data, self.device)
            await asyncio.sleep(0)

            proxy_model = QSortFilterProxyModel()
            proxy_model.setSourceModel(model)
            self.report_table.setModel(proxy_model)
            self.report_table.setSortingEnabled(True)
            self.setup_table_click_handler(self.report_table)
            self.report_table.resizeColumnsToContents()

            timestamps = [r.timestamp.timestamp() for r in self.report_data]
            step = max(1, len(timestamps) // 1000) if not initial_limit else 1
            filtered_ts = timestamps[::step]

            for phase_name in self.phases:
                if phase_name == "Загальне":
                    v1 = [r.line_voltage_1 for r in self.report_data][::step]
                    v2 = [r.line_voltage_2 for r in self.report_data][::step]
                    v3 = [r.line_voltage_3 for r in self.report_data][::step]
                    c1 = [r.current_1 for r in self.report_data][::step]
                    c2 = [r.current_2 for r in self.report_data][::step]
                    c3 = [r.current_3 for r in self.report_data][::step]
                    p1 = [r.power_1 for r in self.report_data][::step]
                    p2 = [r.power_2 for r in self.report_data][::step]
                    p3 = [r.power_3 for r in self.report_data][::step]
                    p_tot = [r.total_system_power for r in self.report_data][::step]

                    getattr(self, "v_line_general_f1").setData(filtered_ts, v1)
                    getattr(self, "v_line_general_f2").setData(filtered_ts, v2)
                    getattr(self, "v_line_general_f3").setData(filtered_ts, v3)
                    getattr(self, "c_line_general_f1").setData(filtered_ts, c1)
                    getattr(self, "c_line_general_f2").setData(filtered_ts, c2)
                    getattr(self, "c_line_general_f3").setData(filtered_ts, c3)
                    getattr(self, "p_line_general_f1").setData(filtered_ts, p1)
                    getattr(self, "p_line_general_f2").setData(filtered_ts, p2)
                    getattr(self, "p_line_general_f3").setData(filtered_ts, p3)
                    getattr(self, "p_line_general_total").setData(filtered_ts, p_tot)
                else:
                    p_idx = phase_name.split(" ")[1]
                    v_vals = [getattr(r, f"line_voltage_{p_idx}", 0) for r in self.report_data][::step]
                    c_vals = [getattr(r, f"current_{p_idx}", 0) for r in self.report_data][::step]
                    p_vals = [getattr(r, f"power_{p_idx}", 0) for r in self.report_data][::step]

                    getattr(self, f"v_line_{phase_name}").setData(filtered_ts, v_vals)
                    getattr(self, f"c_line_{phase_name}").setData(filtered_ts, c_vals)
                    getattr(self, f"p_line_{phase_name}").setData(filtered_ts, p_vals)

            self._is_initial_load = initial_limit

            for phase_name in self.phases:
                self.update_energy_graph(phase_name)

        self.main_window.run_async_task(run_load_report_data())
        self.report_table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)