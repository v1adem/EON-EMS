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
        export_button.clicked.connect(self.open_export_dialog)
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
        self.select_range_button.clicked.connect(self.open_date_range_dialog)
        top_right_layout.addWidget(self.select_range_button)

        self.voltage_graph_widget = pg.PlotWidget()
        self.current_graph_widget = pg.PlotWidget()
        self.energy_graph_widget = pg.PlotWidget()

        self.voltage_graph_widget.setAxisItems({'bottom': DateAxisItem(orientation='bottom')})
        self.current_graph_widget.setAxisItems({'bottom': DateAxisItem(orientation='bottom')})
        self.energy_graph_widget.setAxisItems({'bottom': DateAxisItem(orientation='bottom')})

        self.voltage_curve = self.voltage_graph_widget.plot(pen=pg.mkPen(color='b', width=2), name="Напруга")
        self.current_curve = self.current_graph_widget.plot(pen=pg.mkPen(color='r', width=2), name="Струм")

        self.energy_bar_item = pg.BarGraphItem(width=5, height=5, brush='g', x=1)
        self.energy_graph_widget.addItem(self.energy_bar_item)

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

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_ui)
        self.timer.setInterval(1000)
        self.timer.start()

        self.load_report_data()
        self.update_graphs(self.start_date, self.end_date)
        self.set_light_theme()