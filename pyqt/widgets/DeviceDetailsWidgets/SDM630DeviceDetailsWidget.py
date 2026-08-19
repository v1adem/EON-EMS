import asyncio
import logging

from PySide6.QtCore import QSortFilterProxyModel
from PySide6.QtWidgets import QTableView

from models.Report import SDM630Report
from pyqt.widgets.DeviceDetailsWidgets.BaseDeviceDetailsWidget import BaseDeviceDetailsWidget

logger = logging.getLogger(__name__)


class SDM630DeviceDetailsWidget(BaseDeviceDetailsWidget):
    def __init__(self, parent=None, device=None):
        super(SDM630DeviceDetailsWidget, self).__init__(parent, device)
        self.column_labels, self.column_labels_for_excel = self.init_column_labels()
        self.phases = ["Загальне", "Фаза 1", "Фаза 2", "Фаза 3"]
        self.report_model = SDM630Report

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
        column_labels_for_excel = {
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
        return column_labels, column_labels_for_excel

    def load_report_data(self, initial_limit=True):
        async def run_load_report_data():
            if initial_limit:
                self.report_data = await SDM630Report.filter(
                    device_id=self.device.id
                ).order_by("-timestamp").limit(1000)
                self.report_data.reverse()
            else:
                start_date = self.start_date_table_filter.date().toPython()
                end_date = self.end_date_table_filter.date().addDays(1).toPython()

                self.report_data = await SDM630Report.filter(
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