from pyqt.widgets.DeviceDetailsWidgets.BaseDeviceDetailsWidget import BaseDeviceDetailsWidget


class IME96HDLeDeviceWidgetDetails(BaseDeviceDetailsWidget):
    def __init__(self, parent=None, device=None):
        super(IME96HDLeDeviceWidgetDetails, self).__init__(parent, device)
        self.column_labels, self.column_labels_for_excel = self.init_column_labels()
        self.phases = ["Загальне", "Фаза 1", "Фаза 2", "Фаза 3"]
        self.report_model = IME96HDLeReport
        self.tmp_report_model = IME96HDLeReportTmp

        self.initUi()
        self.init_timers()