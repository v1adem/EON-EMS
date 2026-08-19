import logging
import os
from datetime import datetime

import pyqtgraph as pg
import xlsxwriter

logger = logging.getLogger(__name__)

from PySide6.QtCore import QTimer, QDate, Qt, QTime
from PySide6.QtGui import QStandardItemModel, QStandardItem, QIcon
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QSplitter, QLabel, QDateEdit,
                               QTableView, QTabWidget, QHBoxLayout, QCheckBox,
                               QGridLayout, QLCDNumber, QPushButton, QToolTip, QMessageBox, QFileDialog, QDialog)

from tools.config import resource_path
from tools.ThreadManager import data_bridge
from pyqt.widgets.DateAxisItem import DateAxisItem


class BaseDeviceDetailsWidget(QWidget):
    def __init__(self, main_window, device):
        super().__init__(main_window)
        self.device = device
        self.device_model = self.device.model
        self.main_window = main_window

        self.report_model = None
        self.column_labels, self.column_labels_for_excel = {}, {}
        self.phases = []
        self.phase_data = {}
        self.report_data = []

        self._mouse_callback_refs = {}

    def initUi(self):
        layout = QVBoxLayout(self)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.setChildrenCollapsible(False)
        layout.addWidget(main_splitter)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        self.label = QLabel(
            f"Ім'я пристрою: {self.device.name} | Модель: {self.device.manufacturer} {self.device.model}")
        self.label.setStyleSheet("font-size: 16px;")
        left_layout.addWidget(self.label)

        self.start_date_table_filter = QDateEdit(self)
        self.end_date_table_filter = QDateEdit(self)
        self.create_filter_buttons(left_layout)

        self.report_table = QTableView(self)
        left_layout.addWidget(self.report_table)
        main_splitter.addWidget(left_widget)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("font-size: 16px;")

        for phase_name in self.phases:
            self.create_phase_tab(phase_name)

        main_splitter.addWidget(self.tabs)
        self.set_light_theme()

    def init_timers(self):
        self.timer_clock_indicator = QTimer(self)
        self.timer_clock_indicator.timeout.connect(self.update_clock_text)
        self.timer_clock_indicator.setInterval(1000)
        self.timer_clock_indicator.start()

        self.load_report_data(initial_limit=True)
        self.main_window.hide_loading()

        self.timer_update_history = QTimer(self)
        self.timer_update_history.timeout.connect(self.auto_update_history)
        self.timer_update_history.setInterval(max(5000, self.device.reading_interval * 1000))
        self.timer_update_history.start()

        data_bridge.device_data_received.connect(self.on_live_data_received)

    def create_filter_buttons(self, layout):
        filter_widget = QWidget()
        filter_layout = QHBoxLayout(filter_widget)

        filter_layout.addWidget(QLabel("Від:", styleSheet="font-size: 16px;"))
        self.start_date_table_filter.setCalendarPopup(True)
        self.start_date_table_filter.setDate(QDate.currentDate().addMonths(-1))
        self.start_date_table_filter.setStyleSheet("font-size: 16px;")
        filter_layout.addWidget(self.start_date_table_filter)

        filter_layout.addWidget(QLabel("До:", styleSheet="font-size: 16px;"))
        self.end_date_table_filter.setCalendarPopup(True)
        self.end_date_table_filter.setDate(QDate.currentDate())
        self.end_date_table_filter.setStyleSheet("font-size: 16px;")
        filter_layout.addWidget(self.end_date_table_filter)

        filter_button = QPushButton("Застосувати фільтр")
        filter_button.setStyleSheet("font-size: 16px;")
        filter_button.clicked.connect(lambda: self.load_report_data(initial_limit=False))
        filter_layout.addWidget(filter_button)
        layout.addWidget(filter_widget)

        button_layout = QHBoxLayout()
        self.auto_update_checkbox = QCheckBox("Автооновлення історії")
        self.auto_update_checkbox.setStyleSheet("font-size: 16px;")
        self.auto_update_checkbox.setChecked(True)
        button_layout.addWidget(self.auto_update_checkbox)

        update_button = QPushButton("Оновити")
        update_button.setIcon(QIcon(resource_path("pyqt/icons/refresh.png")))
        update_button.setStyleSheet("font-size: 16px;")
        update_button.clicked.connect(lambda: self.load_report_data(initial_limit=True))
        button_layout.addWidget(update_button)

        export_button = QPushButton("Експорт в Excel")
        export_button.setStyleSheet("font-size: 16px; height: 36px;")
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
        energy_graph = pg.PlotWidget()

        graphs = [voltage_graph, current_graph, power_graph, energy_graph]
        labels = [('left', 'Напруга', 'V'), ('left', 'Струм', 'А'), ('left', 'Потужність', 'W'),
                  ('left', 'Спожито', 'kWh')]

        for g, (side, name, unit) in zip(graphs, labels):
            g.showGrid(x=True, y=True, alpha=0.5)
            g.setAxisItems({'bottom': DateAxisItem(orientation='bottom')})
            g.setLabel(side, name, units=unit)
            top_layout.addWidget(g)

        current_graph.setXLink(voltage_graph)
        energy_graph.setXLink(voltage_graph)
        power_graph.setXLink(voltage_graph)
        layout.addLayout(top_layout)

        bottom_left_layout = QGridLayout()
        clock_title = QLabel("Поточний час", styleSheet="font-size: 16pt; font-weight: bold;",
                             alignment=Qt.AlignmentFlag.AlignCenter)
        clock_label = QLabel(styleSheet="font-size: 16pt;", alignment=Qt.AlignmentFlag.AlignCenter)
        bottom_left_layout.addWidget(clock_title, 0, 0)
        bottom_left_layout.addWidget(clock_label, 1, 0)

        indicators_layout = QGridLayout()
        voltage_lcd = QLCDNumber()
        current_lcd = QLCDNumber()
        power_lcd = QLCDNumber()
        energy_lcd = QLCDNumber()

        for lcd in [voltage_lcd, current_lcd, power_lcd, energy_lcd]:
            lcd.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)
            lcd.setDigitCount(11)
            lcd.setStyleSheet("color: black; background: #e6f2ff;")

        if phase_name != "Загальне":
            indicators_layout.addWidget(QLabel("Напруга (V)", styleSheet="font-weight: bold;"), 0, 0)
            indicators_layout.addWidget(voltage_lcd, 1, 0)
            indicators_layout.addWidget(QLabel("Струм (A)", styleSheet="font-weight: bold;"), 0, 1)
            indicators_layout.addWidget(current_lcd, 1, 1)
            indicators_layout.addWidget(QLabel("Потужність (W)", styleSheet="font-weight: bold;"), 2, 0)
            indicators_layout.addWidget(power_lcd, 3, 0)

        indicators_layout.addWidget(QLabel("Спожито (kWh)", styleSheet="font-weight: bold;"), 2, 1)
        indicators_layout.addWidget(energy_lcd, 3, 1)

        bottom_layout.addLayout(bottom_left_layout)
        bottom_layout.addLayout(indicators_layout)
        layout.addLayout(bottom_layout)

        self.phase_data[phase_name] = {
            "tab": tab, "voltage_graph": voltage_graph, "current_graph": current_graph,
            "energy_graph": energy_graph, "power_graph": power_graph, "voltage_lcd": voltage_lcd,
            "current_lcd": current_lcd, "power_lcd": power_lcd, "energy_lcd": energy_lcd,
            "clock_label": clock_label
        }

        if phase_name != "Загальне":
            setattr(self, f"v_line_{phase_name}",
                    voltage_graph.plot([], [], pen=pg.mkPen(color=(0, 102, 204), width=2)))
            setattr(self, f"c_line_{phase_name}", current_graph.plot([], [], pen=pg.mkPen(color=(204, 51, 0), width=2)))
            setattr(self, f"p_line_{phase_name}", power_graph.plot([], [], pen=pg.mkPen(color=(0, 153, 0), width=2)))
        else:
            colors_v = [(0, 51, 153), (0, 102, 204), (51, 153, 255)]
            colors_c = [(153, 0, 0), (204, 51, 0), (255, 102, 0)]
            colors_p = [(0, 102, 0), (0, 153, 0), (51, 204, 51)]

            for i in range(1, 4):
                setattr(self, f"v_line_general_f{i}",
                        voltage_graph.plot([], [], pen=pg.mkPen(color=colors_v[i - 1], width=2), name=f"Ф{i}"))
                setattr(self, f"c_line_general_f{i}",
                        current_graph.plot([], [], pen=pg.mkPen(color=colors_c[i - 1], width=2), name=f"Ф{i}"))
                setattr(self, f"p_line_general_f{i}",
                        power_graph.plot([], [], pen=pg.mkPen(color=colors_p[i - 1], width=2), name=f"Ф{i}"))

            setattr(self, f"p_line_general_total",
                    power_graph.plot([], [], pen=pg.mkPen(color=(102, 0, 153), width=2.5, style=Qt.PenStyle.DashLine),
                                     name="Разом"))

        self.setup_graph_tooltip(voltage_graph, "voltage", phase_name)
        self.setup_graph_tooltip(current_graph, "current", phase_name)
        self.setup_graph_tooltip(power_graph, "power", phase_name)

        self.tabs.addTab(tab, phase_name)

    def update_clock_text(self):
        current_time = QTime.currentTime().toString("HH:mm:ss") + "\n" + QDate.currentDate().toString("dd.MM.yyyy")
        for phase in self.phase_data.values():
            phase["clock_label"].setText(current_time)

    def on_live_data_received(self, project_id, device_id, new_data):
        if device_id != self.device.id or not new_data:
            return

        phases_config = {
            "Фаза 1": {"v": "line_voltage_1", "c": "current_1", "p": "power_1", "e": "total_kWh_1"},
            "Фаза 2": {"v": "line_voltage_2", "c": "current_2", "p": "power_2", "e": "total_kWh_2"},
            "Фаза 3": {"v": "line_voltage_3", "c": "current_3", "p": "power_3", "e": "total_kWh_3"},
            "Загальне": {"v": None, "c": None, "p": "total_system_power", "e": "total_kWh"}
        }

        for p_name, keys in phases_config.items():
            if p_name not in self.phase_data:
                continue

            ui = self.phase_data[p_name]

            if ui["voltage_lcd"] and keys["v"] in new_data:
                ui["voltage_lcd"].display(f"{new_data[keys['v']]:.2f}")

            if ui["current_lcd"] and keys["c"] in new_data:
                ui["current_lcd"].display(f"{new_data[keys['c']]:.2f}")

            if ui["power_lcd"] and keys["p"] in new_data:
                ui["power_lcd"].display(f"{new_data[keys['p']]:.2f}")

            if ui["energy_lcd"]:
                e_val = new_data.get(keys["e"])
                if e_val is None and p_name != "Загальне":
                    e_val = new_data.get(f"total_kWh_{self.phases.index(p_name)}")
                if e_val is not None:
                    ui["energy_lcd"].display(f"{e_val:.2f}")

    def setup_graph_tooltip(self, graph_widget, graph_type, phase_name):
        def on_mouse_moved(pos):
            if not self.report_data or not graph_widget.sceneBoundingRect().contains(pos):
                return
            mouse_point = graph_widget.plotItem.vb.mapSceneToView(pos)
            x_mouse = mouse_point.x()

            try:
                closest_report = min(self.report_data, key=lambda r: abs(r.timestamp.timestamp() - x_mouse))

                if phase_name == "Загальне":
                    if graph_type == "power":
                        val_str = f"P1: {closest_report.power_1:.1f}W | P2: {closest_report.power_2:.1f}W | P3: {closest_report.power_3:.1f}W\nРазом: {closest_report.total_system_power:.1f}W"
                    elif graph_type == "voltage":
                        val_str = f"V1: {closest_report.line_voltage_1:.1f}V | V2: {closest_report.line_voltage_2:.1f}V | V3: {closest_report.line_voltage_3:.1f}V"
                    elif graph_type == "current":
                        val_str = f"A1: {closest_report.current_1:.2f}A | A2: {closest_report.current_2:.2f}A | A3: {closest_report.current_3:.2f}A"
                else:
                    p_idx = phase_name.split(" ")[1]
                    field_map = {"voltage": f"line_voltage_{p_idx}", "current": f"current_{p_idx}",
                                 "power": f"power_{p_idx}"}
                    val = getattr(closest_report, field_map[graph_type], 0)
                    unit = "V" if graph_type == "voltage" else "A" if graph_type == "current" else "W"
                    val_str = f"{val:.2f} {unit}"

                QToolTip.showText(graph_widget.mapToGlobal(graph_widget.mapFromScene(pos)), val_str)
            except Exception:
                pass

        graph_widget.scene().sigMouseMoved.connect(on_mouse_moved)
        self._mouse_callback_refs[f"{phase_name}_{graph_type}"] = on_mouse_moved

    def update_energy_graph(self, phase_name):
        if not self.report_data or len(self.report_data) < 2:
            return

        graph_widget = self.phase_data[phase_name]["energy_graph"]
        graph_widget.clear()

        energy_field = "total_kWh" if phase_name == "Загальне" else f"total_kWh_{phase_name.split(' ')[1]}"

        total_time_span = (self.report_data[-1].timestamp - self.report_data[0].timestamp).total_seconds()
        avg_interval = total_time_span / (len(self.report_data) - 1) if len(self.report_data) > 1 else 3600

        x_coords = []
        heights = []
        widths = []

        if avg_interval < 3000:
            hourly_data = {}
            for report in self.report_data:
                val = getattr(report, energy_field, None)
                if val is None or val <= 0:
                    continue
                hour_ts = report.timestamp.replace(minute=0, second=0, microsecond=0).timestamp()
                if hour_ts not in hourly_data:
                    hourly_data[hour_ts] = []
                hourly_data[hour_ts].append(val)

            for hour_ts, values in sorted(hourly_data.items()):
                if len(values) >= 2:
                    delta = values[-1] - values[0]
                    if delta > 0:
                        x_coords.append(hour_ts + 1800)
                        heights.append(delta)
                        widths.append(3400)

        else:
            for i in range(1, len(self.report_data)):
                prev_report = self.report_data[i - 1]
                curr_report = self.report_data[i]

                prev_val = getattr(prev_report, energy_field, None)
                curr_val = getattr(curr_report, energy_field, None)

                if prev_val is None or curr_val is None:
                    continue

                delta_energy = curr_val - prev_val
                if delta_energy < 0:
                    delta_energy = 0.0

                t_prev = prev_report.timestamp.timestamp()
                t_curr = curr_report.timestamp.timestamp()
                dt = t_curr - t_prev

                if dt <= 0:
                    continue

                x_coords.append(t_prev + (dt / 2.0))
                heights.append(delta_energy)
                widths.append(dt * 0.95)

        if not x_coords:
            return

        bar_graph = pg.BarGraphItem(
            x=x_coords,
            height=heights,
            width=widths,
            brush=pg.mkBrush(0, 153, 0, 200),
            pen=pg.mkPen(0, 102, 0, 255)
        )
        graph_widget.addItem(bar_graph)

        if hasattr(self, '_is_initial_load') and self._is_initial_load:
            graph_widget.autoRange()

    def auto_update_history(self):
        if self.auto_update_checkbox.isChecked():
            self.load_report_data(initial_limit=True)

    def load_report_data(self, initial_limit=True):
        pass

    def create_table_model(self, report_data, device):
        from register_maps.RegisterMaps import RegisterMap
        register_map = RegisterMap.get_register_map(device.model)
        columns_with_units = RegisterMap.get_columns_with_units(register_map)

        columns = [col for col in self.column_labels.keys()]
        model = QStandardItemModel(len(report_data), len(columns))

        for col_idx, column in enumerate(columns):
            lbl = self.column_labels.get(column, column)
            unit = columns_with_units.get(column, "")
            model.setHeaderData(col_idx, Qt.Orientation.Horizontal, f"{lbl} ({unit})" if unit else lbl)

        for row, report in enumerate(report_data):
            for col, column in enumerate(columns):
                val = getattr(report, column, "")
                if column == "timestamp" and isinstance(val, datetime):
                    val = val.strftime("%Y-%m-%d %H:%M:%S")
                model.setItem(row, col, QStandardItem(str(val) if val is not None else ""))
        return model

    def setup_table_click_handler(self, table_view):
        sm = table_view.selectionModel()
        if sm:
            sm.selectionChanged.connect(self.on_table_row_selected)

    def on_table_row_selected(self, selected):
        if not selected.indexes() or not self.report_data:
            return
        row = selected.indexes()[0].row()
        if 0 <= row < len(self.report_data):
            ts = self.report_data[row].timestamp.timestamp()
            for phase in self.phase_data.values():
                phase["voltage_graph"].setXRange(ts - 1800, ts + 1800, padding=0)

    def set_light_theme(self):
        for phase in self.phase_data.values():
            phase["voltage_graph"].setBackground('w')
            phase["current_graph"].setBackground('w')
            phase["power_graph"].setBackground('w')
            phase["energy_graph"].setBackground('w')

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

        self.main_window.run_async_task(run_export_to_excel())

    def closeEvent(self, event):
        try:
            self.timer_clock_indicator.stop()
            self.timer_update_history.stop()
            data_bridge.device_data_received.disconnect(self.on_live_data_received)
        except Exception:
            pass
        super().closeEvent(event)

    def normalize_report_timestamps(self):
        if not self.report_data:
            return

        local_tz = get_timezone()
        for r in self.report_data:
            if hasattr(r, "timestamp") and isinstance(r.timestamp, datetime):
                utc_dt = r.timestamp if r.timestamp.tzinfo else pytz.utc.localize(r.timestamp)
                r.timestamp = utc_dt.astimezone(local_tz)