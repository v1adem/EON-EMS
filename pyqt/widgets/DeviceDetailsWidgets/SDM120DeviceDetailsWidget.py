import logging
import sys

from pyqt.widgets.DeviceDetailsWidgets.BaseDeviceDetailsWidget import BaseDeviceDetailsWidget

logger = logging.getLogger(__name__)

import pyqtgraph as pg
from AsyncioPySide6 import AsyncioPySide6
from PySide6.QtCore import Qt, QSortFilterProxyModel
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableView, QHBoxLayout, \
    QGridLayout, QLCDNumber

from models.Report import SDM120Report, SDM120ReportTmp
from pyqt.widgets.ConsoleWidget import ConsoleWidget, ConsoleOutputDuplicator
from pyqt.widgets.DateAxisItem import DateAxisItem


class SDM120DeviceDetailsWidget(BaseDeviceDetailsWidget):
    def __init__(self, parent=None, device=None):
        super(SDM120DeviceDetailsWidget, self).__init__(parent, device)
        self.column_labels, self.column_labels_for_excel = self.init_column_labels()
        self.phases = ["Фаза 1"]
        self.report_model = SDM120Report
        self.tmp_report_model = SDM120ReportTmp

        self.initUi()
        self.init_timers()

    def init_column_labels(self):
        column_labels = {
            "timestamp": "Час",
            "line_voltage_1": "Напруга\n",
            "current_1": "Струм\n",
            "active_power_1": "Активна\nпотужність\n",
            "power_1": "Повна\nпотужність\n",
            "reactive_power_1": "Реактивна\nпотужність\n",
            "power_factor_1": "Коефіцієнт\nпотужності\n",
            "import_active_energy_1": "Імпортована\nактивна енергія\n",
            "export_active_energy_1": "Експортована\nактивна енергія\n",
            "total_active_energy": "Загальна\nактивна енергія\n",
            "total_reactive_energy": "Загальна\nреактивна енергія\n",
            "frequency_1": "Частота\n",
            "total_kWh_1": "Загально спожито\nkWh"
        }
        column_labels_for_excel = {
            "line_voltage_1": "Напруга Volts",
            "current_1": "Струм Amps",
            "active_power_1": "Активна потужність Watts",
            "power_1": "Повна потужність VA",
            "reactive_power_1": "Реактивна потужність VAr",
            "power_factor_1": "Коефіцієнт потужності",
            "import_active_energy_1": "Імпортована активна енергія kWh",
            "export_active_energy_1": "Експортована активна енергія kWh",
            "total_active_energy": "Загальна активна енергія kWh",
            "total_reactive_energy": "Загальна реактивна енергія kVArh",
            "frequency_1": "Частота Hz",
            "total_kWh_1": "Загально спожито kWh"
        }
        return column_labels, column_labels_for_excel

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

            self.report_data = await SDM120Report.filter(
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

                    voltage = getattr(report, f'line_voltage_{self.phases.index(phase_name) + 1}')
                    current = getattr(report, f'current_{self.phases.index(phase_name) + 1}')
                    power = getattr(report, f'power_{self.phases.index(phase_name) + 1}')
                    energy = getattr(report, f'total_kWh_{self.phases.index(phase_name) + 1}')

                    voltages.append(voltage)
                    currents.append(current)
                    powers.append(power)
                    energies.append(energy)

                except Exception as e:
                    logger.warning(e)
                    continue
            try:
                self._update_single_phase_line_graph(timestamps, voltages, phase_name, "voltage")
                self._update_single_phase_line_graph(timestamps, currents, phase_name, "current")
                self._update_single_phase_line_graph(timestamps, powers, phase_name, "power")
                self.add_tooltips(self.phase_data[phase_name]["voltage_graph"], timestamps, voltages)
                self.add_tooltips(self.phase_data[phase_name]["current_graph"], timestamps, currents)
                self.add_tooltips(self.phase_data[phase_name]["power_graph"], timestamps, powers)

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