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