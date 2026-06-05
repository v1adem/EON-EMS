import asyncio
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

    def load_report_data(self, initial_limit=True):
        """Зчитування історії SDM120 з лімітом або фільтром за період"""

        async def run_load_report_data():
            if initial_limit:
                self.report_data = await SDM120Report.filter(
                    device_id=self.device.id
                ).order_by("-timestamp").limit(1000)
                self.report_data.reverse()
            else:
                start_date = self.start_date_table_filter.date().toPython()
                end_date = self.end_date_table_filter.date().addDays(1).toPython()

                self.report_data = await SDM120Report.filter(
                    device_id=self.device.id,
                    timestamp__gte=start_date,
                    timestamp__lte=end_date
                ).order_by("timestamp").all()

            if not self.report_data:
                return

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
                v_vals = [r.line_voltage_1 for r in self.report_data][::step]
                c_vals = [r.current_1 for r in self.report_data][::step]
                p_vals = [r.power_1 for r in self.report_data][::step]

                getattr(self, f"v_line_{phase_name}").setData(filtered_ts, v_vals)
                getattr(self, f"c_line_{phase_name}").setData(filtered_ts, c_vals)
                getattr(self, f"p_line_{phase_name}").setData(filtered_ts, p_vals)

            self._is_initial_load = initial_limit

            for phase_name in self.phases:
                self.update_energy_graph(phase_name)

        self.main_window.run_async_task(run_load_report_data())
        self.report_table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)