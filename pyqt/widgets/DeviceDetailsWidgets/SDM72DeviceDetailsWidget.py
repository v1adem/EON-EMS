import logging
import sys

from pyqt.widgets.DeviceDetailsWidgets.BaseDeviceDetailsWidget import BaseDeviceDetailsWidget

logger = logging.getLogger(__name__)

import pyqtgraph as pg
from AsyncioPySide6 import AsyncioPySide6
from PySide6.QtCore import QDate, Qt, QSortFilterProxyModel, QTime
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
        self.init_timers()

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

        console_widget = ConsoleWidget()
        bottom_left_layout.addWidget(console_widget, 0, 0, 2, 1)

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
            "console_widget": console_widget,
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

        sys.stdout = ConsoleOutputDuplicator(console_widget, sys.__stdout__)
        logger.info(f"Console widget initialized in {self.device.name}")

    def load_report_data(self):
        async def run_load_report_data():
            start_date = self.start_date_table_filter.date().toPython()
            end_date = self.end_date_table_filter.date().addDays(1).toPython()

            self.report_data = await SDM72Report.filter(
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

            self.update_graphs()

        AsyncioPySide6.runTask(run_load_report_data())
        self.report_table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)

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
                "Загальне": {
                    "energy": getattr(last_report, 'total_kWh', 0),
                },
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

    def update_graphs(self):
        for phase_name in self.phases:
            timestamps = []
            voltages = []
            currents = []
            powers = []
            energies = []

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
                        voltage = getattr(report, f'line_voltage_{self.phases.index(phase_name) + 1}')
                        current = getattr(report, f'current_{self.phases.index(phase_name) + 1}')
                        power = getattr(report, f'power_{self.phases.index(phase_name) + 1}')

                        voltages.append(voltage)
                        currents.append(current)
                        powers.append(power)

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
            except Exception as e:
                logger.error(e)

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