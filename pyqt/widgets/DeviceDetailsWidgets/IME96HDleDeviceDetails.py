import logging
import sys

from pyqt.widgets.DeviceDetailsWidgets.BaseDeviceDetailsWidget import BaseDeviceDetailsWidget

logger = logging.getLogger(__name__)

import pyqtgraph as pg
from AsyncioPySide6 import AsyncioPySide6
from PySide6.QtCore import QDate, Qt, QSortFilterProxyModel, QTime
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableView, QHBoxLayout, \
    QGridLayout, QLCDNumber

from models.Report import IME96HDLeReport, IME96HDLeReportTmp
from pyqt.widgets.ConsoleWidget import ConsoleWidget, ConsoleOutputDuplicator
from pyqt.widgets.DateAxisItem import DateAxisItem


class IME96HDleDetailsWidget(BaseDeviceDetailsWidget):
    def __init__(self, parent=None, device=None):
        super(IME96HDleDetailsWidget, self).__init__(parent, device)
        self.column_labels, self.column_labels_for_excel = self.init_column_labels()
        self.phases = ["Загальне", "Фаза 1", "Фаза 2", "Фаза 3"]
        self.report_model = IME96HDLeReport
        self.tmp_report_model = IME96HDLeReportTmp

        self.initUi()
        self.init_timers()

    def init_column_labels(self):
        column_labels = {
            #"timestamp": "Час",
            #"line_voltage_1": "Лінійна напруга\n(Фаза 1)\n",
            #"line_voltage_2": "Лінійна напруга\n(Фаза 2)\n",
            #"line_voltage_3": "Лінійна напруга\n(Фаза 3)\n",
            #"current_1": "Струм\n(Фаза 1)\n",
            #"current_2": "Струм\n(Фаза 2)\n",
            #"current_3": "Струм\n(Фаза 3)\n",
            #"power_1": "Потужність\n(Фаза 1)\n",
            #"power_2": "Потужність\n(Фаза 2)\n",
            #"power_3": "Потужність\n(Фаза 3)\n",
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
            #"total_apparent_power": "Загальна видима потужність",
            "total_system_VAr": "Загальна реактивна потужність",
            "total_system_power_factor": "Коефіцієнт потужності системи",
            "total_import_kwh": "Загальне споживання (імпорт)",
            "total_export_kwh": "Загальне споживання (експорт)",
            #"_1_to_2_voltage": "Напруга між\nФазою 1 і Фазою 2\n",
            #"_2_to_3_voltage": "Напруга між\nФазою 2 і Фазою 3\n",
            #"_3_to_1_voltage": "Напруга між\nФазою 3 і Фазою 1\n",
            #"neutral_current": "Струм нейтралі\n",
            "total_kWh": "Загальна енергія\n",
            "total_kVArh": "Загальна реактивна\nенергія\n",
            "total_active_power": "Загальна активна потужність\n",
            "total_reactive_power": "Загальна експортована\nактивна потужність\n"
        }
        column_labels_for_excel = column_labels.copy()
        return column_labels, column_labels_for_excel