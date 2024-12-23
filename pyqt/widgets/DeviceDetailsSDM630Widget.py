from datetime import datetime

import pyqtgraph as pg
import xlsxwriter
from PyQt5.QtCore import Qt, QSortFilterProxyModel, QTime, QTimer, QDate
from PyQt5.QtGui import QIcon, QStandardItemModel, QStandardItem, QFont
from PyQt5.QtWidgets import QMessageBox, QFileDialog
from PyQt5.QtWidgets import QVBoxLayout, QPushButton, QLabel, QWidget, QSplitter, QTableView, QCalendarWidget, \
    QHBoxLayout, QDialog, QLCDNumber, QCheckBox, QDateEdit, QGridLayout
from pyqtgraph import AxisItem
from sqlalchemy import desc

from config import resource_path
from models.Report import SDM630Report, SDM630ReportTmp
from pyqt.widgets.DeviceDetailsSDM120Widget import DateAxisItem
from register_maps.RegisterMaps import RegisterMap


class DeviceDetailsSDM630Widget(QWidget):
    def __init__(self, main_window, device):
        super().__init__(main_window)
        self.device = device
        self.db_session = main_window.db_session
        self.main_window = main_window

        layout = QVBoxLayout(self)

        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.setChildrenCollapsible(False)
        layout.addWidget(main_splitter)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        self.label = QLabel(f"Ім'я пристрою: {device.name} | Модель пристрою: {device.manufacturer} {device.model}")
        self.label.setStyleSheet("font-size: 16px;")
        table_layout.addWidget(self.label)

        button_layout = QHBoxLayout()

        filter_layout = QHBoxLayout()

        self.start_date_edit = QDateEdit(self)
        self.start_date_edit.setStyleSheet("font-size: 16px;")
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate().addYears(-1))
        vid = QLabel("Від:")
        vid.setStyleSheet("font-size: 16px;")
        filter_layout.addWidget(vid)
        filter_layout.addWidget(self.start_date_edit)

        self.end_date_edit = QDateEdit(self)
        self.end_date_edit.setStyleSheet("font-size: 16px;")
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())
        do = QLabel("До:")
        do.setStyleSheet("font-size: 16px;")
        filter_layout.addWidget(do)
        filter_layout.addWidget(self.end_date_edit)

        self.start_date = None
        self.end_date = None

        filter_button = QPushButton("Застосувати фільтр")
        filter_button.setStyleSheet("font-size: 16px;")
        filter_button.clicked.connect(self.apply_date_filter)
        filter_layout.addWidget(filter_button)

        table_layout.addLayout(filter_layout)

        refresh_button = QPushButton()
        refresh_button.setIcon(QIcon(resource_path("pyqt/icons/refresh.png")))
        refresh_button.setFixedSize(36, 36)
        refresh_button.clicked.connect(self.load_report_data)
        button_layout.addWidget(refresh_button)

        export_button = QPushButton("Експорт в Excel")
        export_button.setStyleSheet("font-size: 16px;")
        export_button.setFixedHeight(36)
        # export_button.clicked.connect(self.open_export_dialog)
        button_layout.addWidget(export_button)

        table_layout.addLayout(button_layout)

        self.report_table = QTableView(self)
        table_layout.addWidget(self.report_table)
        left_layout.addWidget(table_widget)
        main_splitter.addWidget(left_widget)

        right_splitter = QSplitter(Qt.Vertical)
        right_splitter.setChildrenCollapsible(False)
        main_splitter.addWidget(right_splitter)

        top_right_widget = QWidget()
        top_right_layout = QVBoxLayout(top_right_widget)

        self.select_range_button = QPushButton("Обрати проміжок")
        self.select_range_button.setStyleSheet("font-size: 16px;")
        # self.select_range_button.clicked.connect(self.open_date_range_dialog)
        top_right_layout.addWidget(self.select_range_button)

        self.voltage_graph_widget = pg.PlotWidget()
        self.current_graph_widget = pg.PlotWidget()
        self.energy_graph_widget = pg.PlotWidget()

        self.voltage_graph_widget.setAxisItems({'bottom': DateAxisItem(orientation='bottom')})
        self.current_graph_widget.setAxisItems({'bottom': DateAxisItem(orientation='bottom')})
        self.energy_graph_widget.setAxisItems({'bottom': DateAxisItem(orientation='bottom')})

        self.voltage_curve = self.voltage_graph_widget.plot(pen=pg.mkPen(color='b', width=2), name="Напруга")
        self.current_curve = self.current_graph_widget.plot(pen=pg.mkPen(color='r', width=2), name="Струм")

        # self.energy_bar_item = pg.BarGraphItem(width=5, height=5, brush='g', x=1)
        # self.energy_graph_widget.addItem(self.energy_bar_item)

        # Для графіка напруги
        self.voltage_graph_widget.setLabel('left', 'Напруга', units='В')

        # Для графіка струму
        self.current_graph_widget.setLabel('left', 'Струм', units='А')

        # Для графіка споживання
        self.energy_graph_widget.setLabel('left', 'Споживання', units='кВт·год')

        top_right_layout.addWidget(self.voltage_graph_widget)
        top_right_layout.addWidget(self.current_graph_widget)
        top_right_layout.addWidget(self.energy_graph_widget)

        self.auto_update_checkbox = QCheckBox("Автооновлення")
        self.auto_update_checkbox.setChecked(True)  # За замовчуванням увімкнено
        top_right_layout.addWidget(self.auto_update_checkbox)

        right_splitter.addWidget(top_right_widget)

        bottom_right_widget = QWidget()
        self.bottom_right_layout = QHBoxLayout(bottom_right_widget)

        # Ліва частина: Годинник
        self.left_layout = QVBoxLayout()

        # Заголовок "Поточний час"
        self.clock_title = QLabel("Поточний час")
        self.clock_title.setStyleSheet("font-size: 16pt; font-weight: bold;")
        self.clock_title.setAlignment(Qt.AlignCenter)  # Вирівнювання тексту по центру
        self.left_layout.addWidget(self.clock_title)

        # Годинник
        self.clock_label = QLabel()
        self.clock_label.setStyleSheet("font-size: 24pt;")  # Збільшений шрифт для годинника
        self.clock_label.setAlignment(Qt.AlignCenter)  # Вирівнювання по центру
        self.left_layout.addWidget(self.clock_label)

        self.left_layout.addStretch()

        # Права частина: Індикатори в сітці
        self.grid_layout = QGridLayout()

        # Індикатори
        self.voltage_lcd = QLCDNumber()
        self.voltage_lcd.setSegmentStyle(QLCDNumber.Flat)
        self.current_lcd = QLCDNumber()
        self.current_lcd.setSegmentStyle(QLCDNumber.Flat)
        self.power_lcd = QLCDNumber()
        self.power_lcd.setSegmentStyle(QLCDNumber.Flat)
        self.energy_lcd = QLCDNumber()
        self.energy_lcd.setSegmentStyle(QLCDNumber.Flat)

        # Підписи
        self.voltage_label = QLabel("Напруга (V)")
        self.voltage_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        self.current_label = QLabel("Струм (A)")
        self.current_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        self.power_label = QLabel("Потужність (W)")
        self.power_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        self.energy_label = QLabel("Спожито (kWh)")
        self.energy_label.setStyleSheet("font-size: 14pt; font-weight: bold;")

        # Додавання до сітки
        self.grid_layout.addWidget(self.voltage_label, 0, 0)
        self.grid_layout.addWidget(self.voltage_lcd, 1, 0)
        self.grid_layout.addWidget(self.current_label, 0, 1)
        self.grid_layout.addWidget(self.current_lcd, 1, 1)
        self.grid_layout.addWidget(self.power_label, 2, 0)
        self.grid_layout.addWidget(self.power_lcd, 3, 0)
        self.grid_layout.addWidget(self.energy_label, 2, 1)
        self.grid_layout.addWidget(self.energy_lcd, 3, 1)

        # Додавання до головного компонувальника
        self.bottom_right_layout.addLayout(self.left_layout)  # Ліва частина
        self.bottom_right_layout.addLayout(self.grid_layout)  # Права частина (сітка)

        right_splitter.addWidget(bottom_right_widget)

        self.set_splitter_fixed_ratios(main_splitter, [1, 1])
        self.set_splitter_fixed_ratios(right_splitter, [3, 1])

        #self.timer = QTimer(self)
        #self.timer.timeout.connect(self.update_ui)
        #self.timer.setInterval(1000)
        #self.timer.start()

        self.load_report_data()
        #self.update_graphs(self.start_date, self.end_date)
        self.set_light_theme()

    def set_light_theme(self):
        self.voltage_graph_widget.setBackground('w')
        self.current_graph_widget.setBackground('w')
        self.energy_graph_widget.setBackground('w')

        self.voltage_graph_widget.plot([], pen=pg.mkPen(color='b', width=2))
        self.current_graph_widget.plot([], pen=pg.mkPen(color='r', width=2))
        self.energy_graph_widget.plot([], pen=pg.mkPen(color='g', width=2))

    def set_splitter_fixed_ratios(self, splitter, ratios):
        total = sum(ratios)
        sizes = [int(ratio / total * splitter.size().width()) for ratio in ratios]
        splitter.setSizes(sizes)
        splitter.handle(1).setEnabled(False)

    def update_ui(self):
        self.update_clock()
        self.update_indicators()
        if self.auto_update_checkbox.isChecked():
            self.update_graphs(self.start_date, self.end_date)

    def update_indicators(self):
        last_report = (self.db_session.query(SDM630ReportTmp)
                       .filter_by(device_id=self.device.id).order_by(desc(SDM630ReportTmp.timestamp)).first())
        if last_report:
            self.voltage_lcd.display(getattr(last_report, 'voltage', 0))
            self.current_lcd.display(getattr(last_report, 'current', 0))
            self.energy_lcd.display(getattr(last_report, 'total_active_energy', 0))
            self.power_lcd.display(getattr(last_report, 'active_power', 0))

    def update_clock(self):
        current_time = QTime.currentTime().toString("HH:mm:ss")  # Час
        current_time += "\n" + QDate.currentDate().toString("dd.MM.yyyy")  # Дата
        self.clock_label.setText(f"{current_time}")

    def create_table_model(self, report_data, device):
        column_labels = {
            "timestamp": "Час",
            "line_voltage_1": "Лінійна напруга (Фаза 1)",
            "line_voltage_2": "Лінійна напруга (Фаза 2)",
            "line_voltage_3": "Лінійна напруга (Фаза 3)",
            "current_1": "Струм (Фаза 1)",
            "current_2": "Струм (Фаза 2)",
            "current_3": "Струм (Фаза 3)",
            "power_1": "Активна потужність (Фаза 1)",
            "power_2": "Активна потужність (Фаза 2)",
            "power_3": "Активна потужність (Фаза 3)",
            "power_factor_1": "Коефіцієнт потужності (Фаза 1)",
            "power_factor_2": "Коефіцієнт потужності (Фаза 2)",
            "power_factor_3": "Коефіцієнт потужності (Фаза 3)",
            "total_system_power": "Загальна потужність системи",
            #"total_system_VA": "Загальна потужність",
            #"total_system_VAr": "Загальна реактивна потужність",
            #"total_system_power_factor": "Коефіцієнт потужності системи",
            #"total_import_kwh": "Загальне споживання (імпорт)",
            #"total_export_kwh": "Загальне споживання (експорт)",
            #"total_import_kVAh": "Загальне споживання (імпорт)",
            #"total_export_kVAh": "Загальне споживання (експорт)",
            "total_kVAh": "Загальна енергія кВА·год",
            "_1_to_2_voltage": "Напруга між Фазою 1 і Фазою 2",
            "_2_to_3_voltage": "Напруга між Фазою 2 і Фазою 3",
            "_3_to_1_voltage": "Напруга між Фазою 3 і Фазою 1",
            "neutral_current": "Струм нейтралі",
            #"line_voltage_THD_1": "THD лінійної напруги (Фаза 1)",
            #"line_voltage_THD_2": "THD лінійної напруги (Фаза 2)",
            #"line_voltage_THD_3": "THD лінійної напруги (Фаза 3)",
            #"line_current_THD_1": "THD лінійного струму (Фаза 1)",
            #"line_current_THD_2": "THD лінійного струму (Фаза 2)",
            #"line_current_THD_3": "THD лінійного струму (Фаза 3)",
            #"current_demand_1": "Струмове навантаження (Фаза 1)",
            #"current_demand_2": "Струмове навантаження (Фаза 2)",
            #"current_demand_3": "Струмове навантаження (Фаза 3)",
            #"phase_voltage_THD_1": "THD фазної напруги (Фаза 1)",
            #"phase_voltage_THD_2": "THD фазної напруги (Фаза 2)",
            #"phase_voltage_THD_3": "THD фазної напруги (Фаза 3)",
            #"average_line_to_line_voltage_THD": "Середній THD лінійної напруги",
            "total_kWh": "Загальна енергія кВт·год",
            "total_kVArh": "Загальна реактивна енергія (кВАр·год)",
            #"import_kWh_1": "Імпортована енергія (Фаза 1)",
            #"import_kWh_2": "Імпортована енергія (Фаза 2)",
            #"import_kWh_3": "Імпортована енергія (Фаза 3)",
            #"export_kWh_1": "Експортована енергія (Фаза 1)",
            #"export_kWh_2": "Експортована енергія (Фаза 2)",
            #"export_kWh_3": "Експортована енергія (Фаза 3)",
            #"total_kWh_1": "Загальна енергія (Фаза 1)",
            #"total_kWh_2": "Загальна енергія (Фаза 2)",
            #"total_kWh_3": "Загальна енергія (Фаза 3)",
            #"import_kVArh_1": "Імпортована реактивна енергія (кВАр·год) (Фаза 1)",
            #"import_kVArh_2": "Імпортована реактивна енергія (кВАр·год) (Фаза 2)",
            #"import_kVArh_3": "Імпортована реактивна енергія (кВАр·год) (Фаза 3)",
            #"export_kVArh_1": "Експортована реактивна енергія (кВАр·год) (Фаза 1)",
            #"export_kVArh_2": "Експортована реактивна енергія (кВАр·год) (Фаза 2)",
            #"export_kVArh_3": "Експортована реактивна енергія (кВАр·год) (Фаза 3)",
            #"total_kVArh_1": "Загальна реактивна енергія (кВАр·год) (Фаза 1)",
            #"total_kVArh_2": "Загальна реактивна енергія (кВАр·год) (Фаза 2)",
            #"total_kVArh_3": "Загальна реактивна енергія (кВАр·год) (Фаза 3)",
        }

        # Get columns and units from RegisterMap
        register_map = RegisterMap.get_register_map(device.model)
        columns_with_units = RegisterMap.get_columns_with_units(register_map)

        columns = set()

        for report in report_data:
            for column_name in report.__table__.columns.keys():
                if column_name not in ['id', 'device_id'] and getattr(report, column_name) is not None:
                    columns.add(column_name)

        columns = sorted(columns)
        model = QStandardItemModel(len(report_data), len(columns))
        header_labels = []

        for column in columns:
            custom_label = column_labels.get(column, column)
            unit = columns_with_units.get(column, "")
            header_labels.append(f"{custom_label} ({unit})" if unit else custom_label)

        bold_font = QFont()
        bold_font.setBold(True)
        bold_font.setPointSize(12)

        for col_index, header in enumerate(header_labels):
            model.setHeaderData(col_index, Qt.Horizontal, header)
            model.setHeaderData(col_index, Qt.Horizontal, bold_font, Qt.FontRole)

        for row, report in enumerate(report_data):
            for col, column in enumerate(columns):
                value = getattr(report, column)
                model.setItem(row, col, QStandardItem(str(value) if value is not None else ""))

        return model

    def load_report_data(self):
        start_date = self.start_date_edit.date().toPyDate()
        end_date = self.end_date_edit.date().addDays(1).toPyDate()

        report_data = self.db_session.query(SDM630Report).filter_by(device_id=self.device.id).filter(
            SDM630Report.timestamp >= start_date, SDM630Report.timestamp <= end_date
        ).order_by(desc(SDM630Report.timestamp)).all()

        model = self.create_table_model(report_data, self.device)

        proxy_model = QSortFilterProxyModel()
        proxy_model.setSourceModel(model)
        proxy_model.setSortCaseSensitivity(Qt.CaseInsensitive)

        self.report_table.setModel(proxy_model)
        self.report_table.sortByColumn(3, Qt.DescendingOrder)
        self.report_table.setSortingEnabled(True)
        self.report_table.resizeColumnsToContents()

    def apply_date_filter(self):
        self.load_report_data()