from tortoise import fields
from tortoise.models import Model
from datetime import datetime, timezone


class SDM120Report(Model):
    id = fields.IntField(pk=True)
    device = fields.ForeignKeyField('models.Device', related_name='sdm120_reports')
    timestamp = fields.DatetimeField(default=lambda: datetime.now())

    line_voltage_1 = fields.FloatField(null=True)
    current_1 = fields.FloatField(null=True)
    active_power_1 = fields.FloatField(null=True)
    power_1 = fields.FloatField(null=True)
    reactive_power_1 = fields.FloatField(null=True)
    power_factor_1 = fields.FloatField(null=True)
    frequency_1 = fields.FloatField(null=True)
    import_active_energy_1 = fields.FloatField(null=True)
    export_active_energy_1 = fields.FloatField(null=True)
    total_active_energy = fields.FloatField(null=True)
    total_reactive_energy = fields.FloatField(null=True)

    @property
    def total_kWh_1(self):
        if self.total_active_energy is not None and self.total_reactive_energy is not None:
            result = (self.total_active_energy ** 2 + self.total_reactive_energy ** 2) ** 0.5
            return round(result, 2)
        return None

    class Meta:
        table = "sdm120_reports"


class SDM120ReportTmp(Model):
    id = fields.IntField(pk=True)
    device_id = fields.IntField()
    timestamp = fields.DatetimeField(default=lambda: datetime.now())

    line_voltage_1 = fields.FloatField(null=True)
    current_1 = fields.FloatField(null=True)
    power_1 = fields.FloatField(null=True)
    total_active_energy = fields.FloatField(null=True)
    total_reactive_energy = fields.FloatField(null=True)

    @property
    def total_kWh_1(self):
        if self.total_active_energy is not None and self.total_reactive_energy is not None:
            result = (self.total_active_energy ** 2 + self.total_reactive_energy ** 2) ** 0.5
            return round(result, 2)
        return None

    class Meta:
        table = "sdm120_reports_tmp"


class SDM630Report(Model):
    id = fields.IntField(pk=True)
    device = fields.ForeignKeyField('models.Device', related_name='sdm630_reports')
    timestamp = fields.DatetimeField(default=lambda: datetime.now())

    line_voltage_1 = fields.FloatField(null=True)
    line_voltage_2 = fields.FloatField(null=True)
    line_voltage_3 = fields.FloatField(null=True)
    current_1 = fields.FloatField(null=True)
    current_2 = fields.FloatField(null=True)
    current_3 = fields.FloatField(null=True)
    power_1 = fields.FloatField(null=True)
    power_2 = fields.FloatField(null=True)
    power_3 = fields.FloatField(null=True)
    power_factor_1 = fields.FloatField(null=True)
    power_factor_2 = fields.FloatField(null=True)
    power_factor_3 = fields.FloatField(null=True)
    total_system_power = fields.FloatField(null=True)
    total_system_VA = fields.FloatField(null=True)
    total_system_VAr = fields.FloatField(null=True)
    total_system_power_factor = fields.FloatField(null=True)
    total_import_kwh = fields.FloatField(null=True)
    total_export_kwh = fields.FloatField(null=True)
    total_import_kVAh = fields.FloatField(null=True)
    total_export_kVAh = fields.FloatField(null=True)
    total_kVAh = fields.FloatField(null=True)
    _1_to_2_voltage = fields.FloatField(null=True)
    _2_to_3_voltage = fields.FloatField(null=True)
    _3_to_1_voltage = fields.FloatField(null=True)
    neutral_current = fields.FloatField(null=True)
    line_voltage_THD_1 = fields.FloatField(null=True)
    line_voltage_THD_2 = fields.FloatField(null=True)
    line_voltage_THD_3 = fields.FloatField(null=True)
    line_current_THD_1 = fields.FloatField(null=True)
    line_current_THD_2 = fields.FloatField(null=True)
    line_current_THD_3 = fields.FloatField(null=True)
    current_demand_1 = fields.FloatField(null=True)
    current_demand_2 = fields.FloatField(null=True)
    current_demand_3 = fields.FloatField(null=True)
    phase_voltage_THD_1 = fields.FloatField(null=True)
    phase_voltage_THD_2 = fields.FloatField(null=True)
    phase_voltage_THD_3 = fields.FloatField(null=True)
    average_line_to_line_voltage_THD = fields.FloatField(null=True)
    total_kWh = fields.FloatField(null=True)
    total_kVArh = fields.FloatField(null=True)
    import_kWh_1 = fields.FloatField(null=True)
    import_kWh_2 = fields.FloatField(null=True)
    import_kWh_3 = fields.FloatField(null=True)
    export_kWh_1 = fields.FloatField(null=True)
    export_kWh_2 = fields.FloatField(null=True)
    export_kWh_3 = fields.FloatField(null=True)
    total_kWh_1 = fields.FloatField(null=True)
    total_kWh_2 = fields.FloatField(null=True)
    total_kWh_3 = fields.FloatField(null=True)
    import_kVArh_1 = fields.FloatField(null=True)
    import_kVArh_2 = fields.FloatField(null=True)
    import_kVArh_3 = fields.FloatField(null=True)
    export_kVArh_1 = fields.FloatField(null=True)
    export_kVArh_2 = fields.FloatField(null=True)
    export_kVArh_3 = fields.FloatField(null=True)
    total_kVArh_1 = fields.FloatField(null=True)
    total_kVArh_2 = fields.FloatField(null=True)
    total_kVArh_3 = fields.FloatField(null=True)

    class Meta:
        table = "sdm630_reports"


class SDM630ReportTmp(Model):
    id = fields.IntField(pk=True)
    device = fields.ForeignKeyField('models.Device', related_name='sdm630_reports_tmp')
    timestamp = fields.DatetimeField(default=lambda: datetime.now())

    line_voltage_1 = fields.FloatField(null=True)
    line_voltage_2 = fields.FloatField(null=True)
    line_voltage_3 = fields.FloatField(null=True)
    current_1 = fields.FloatField(null=True)
    current_2 = fields.FloatField(null=True)
    current_3 = fields.FloatField(null=True)
    power_1 = fields.FloatField(null=True)
    power_2 = fields.FloatField(null=True)
    power_3 = fields.FloatField(null=True)
    total_kWh_1 = fields.FloatField(null=True)
    total_kWh_2 = fields.FloatField(null=True)
    total_kWh_3 = fields.FloatField(null=True)
    total_kWh = fields.FloatField(null=True)

    class Meta:
        table = "sdm630_reports_tmp"

class SDM72DReport(Model):
    id = fields.IntField(pk=True)
    device = fields.ForeignKeyField('models.Device', related_name='sdm72d_reports')
    timestamp = fields.DatetimeField(default=lambda: datetime.now())

    line_voltage_1 = fields.FloatField(null=True)
    line_voltage_2 = fields.FloatField(null=True)
    line_voltage_3 = fields.FloatField(null=True)
    current_1 = fields.FloatField(null=True)
    current_2 = fields.FloatField(null=True)
    current_3 = fields.FloatField(null=True)
    active_power_1 = fields.FloatField(null=True)
    active_power_2 = fields.FloatField(null=True)
    active_power_3 = fields.FloatField(null=True)
    power_1 = fields.FloatField(null=True)
    power_2 = fields.FloatField(null=True)
    power_3 = fields.FloatField(null=True)
    reactive_power_1 = fields.FloatField(null=True)
    reactive_power_2 = fields.FloatField(null=True)
    reactive_power_3 = fields.FloatField(null=True)
    power_factor_1 = fields.FloatField(null=True)
    power_factor_2 = fields.FloatField(null=True)
    power_factor_3 = fields.FloatField(null=True)
    total_system_power = fields.FloatField(null=True)
    total_system_VA = fields.FloatField(null=True)
    total_system_VAr = fields.FloatField(null=True)
    total_system_power_factor = fields.FloatField(null=True)
    total_import_kwh = fields.FloatField(null=True)
    total_export_kwh = fields.FloatField(null=True)
    _1_to_2_voltage = fields.FloatField(null=True)
    _2_to_3_voltage = fields.FloatField(null=True)
    _3_to_1_voltage = fields.FloatField(null=True)
    neutral_current = fields.FloatField(null=True)
    total_kWh = fields.FloatField(null=True)
    total_kVArh = fields.FloatField(null=True)
    total_import_active_power = fields.FloatField(null=True)
    total_export_active_power = fields.FloatField(null=True)

    class Meta:
        table = "sdm72d_reports"

class SDM72DReportTmp(Model):
    id = fields.IntField(pk=True)
    device = fields.ForeignKeyField('models.Device', related_name='sdm72d_reports_tmp')
    timestamp = fields.DatetimeField(default=lambda: datetime.now())

    line_voltage_1 = fields.FloatField(null=True)
    line_voltage_2 = fields.FloatField(null=True)
    line_voltage_3 = fields.FloatField(null=True)
    current_1 = fields.FloatField(null=True)
    current_2 = fields.FloatField(null=True)
    current_3 = fields.FloatField(null=True)
    power_1 = fields.FloatField(null=True)
    power_2 = fields.FloatField(null=True)
    power_3 = fields.FloatField(null=True)
    total_kWh = fields.FloatField(null=True)

    class Meta:
        table = "sdm72d_reports_tmp"
