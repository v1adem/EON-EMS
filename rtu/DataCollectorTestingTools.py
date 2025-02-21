import random


def get_test_data(device_model, last_data):
    if device_model == "SDM120":
        if last_data is None:
            last_kwh = 0.0
        else:
            last_kwh = last_data.total_kWh_1 if last_data.total_kWh_1 else 0.0
            last_kwh += random.uniform(0.1, 0.5)
        return {
            "line_voltage_1": random.randrange(200, 240),
            "current_1": random.randrange(1, 20),
            "power_1": 0.22,
            "total_active_energy": last_kwh,
            "total_reactive_energy": 0.0,

            "active_power_1": 0.22,
            "reactive_power_1": 0.22,
            "power_factor_1": 1,
            "frequency_1": 50.0,
            "import_active_energy_1": 0.0,
            "export_active_energy_1": 0.0,
        }
    elif device_model == "SDM630":
        if last_data is None:
            last_kwh_1 = 0.0
            last_kwh_2 = 0.0
            last_kwh_3 = 0.0
        else:
            last_kwh_1 = last_data.total_kWh_1 if last_data.total_kWh_1 else 0.0
            last_kwh_1 += random.uniform(0.1, 0.5)
            last_kwh_2 = last_data.total_kWh_2 if last_data.total_kWh_2 else 0.0
            last_kwh_2 += random.uniform(0.1, 0.5)
            last_kwh_3 = last_data.total_kWh_3 if last_data.total_kWh_3 else 0.0
            last_kwh_3 += random.uniform(0.1, 0.5)
        last_kwh = last_kwh_1 + last_kwh_2 + last_kwh_3
        return {
            "line_voltage_1": random.randrange(200, 240),
            "line_voltage_2": random.randrange(200, 240),
            "line_voltage_3": random.randrange(200, 240),
            "current_1": random.randrange(1, 20),
            "current_2": random.randrange(1, 20),
            "current_3": random.randrange(1, 20),
            "power_1": 0.22,
            "power_2": 0.22,
            "power_3": 0.22,
            "total_kWh_1": last_kwh_1,
            "total_kWh_2": last_kwh_2,
            "total_kWh_3": last_kwh_3,
            "total_kWh": last_kwh,

            "power_factor_1": 1,
            "power_factor_2": 1,
            "power_factor_3": 1,
            "total_system_power": 1,
            "total_system_power_factor": 1,
            "total_system_VA": 1,
            "total_system_VAr": 1,
            "total_import_kwh": 1,
            "total_export_kwh": 1,
            "total_import_kVAh": 1,
            "total_export_kVAh": 1,
            "total_kVAh": 1,
            "_1_to_2_voltage": 1,
            "_2_to_3_voltage": 1,
            "_3_to_1_voltage": 1,
            "neutral_current": 1,
            "line_voltage_THD_1": 1,
            "line_voltage_THD_2": 1,
            "line_voltage_THD_3": 1,
            "line_current_THD_1": 1,
            "line_current_THD_2": 1,
            "line_current_THD_3": 1,
            "current_demand_1": 1,
            "current_demand_2": 1,
            "current_demand_3": 1,
            "phase_voltage_THD_1": 1,
            "phase_voltage_THD_2": 1,
            "phase_voltage_THD_3": 1,
            "average_line_to_line_voltage_THD": 1,
            "total_kVArh": 1,
            "import_kWh_1": 1,
            "import_kWh_2": 1,
            "import_kWh_3": 1,
            "export_kWh_1": 1,
            "export_kWh_2": 1,
            "export_kWh_3": 1,
            "import_kVArh_1": 1,
            "import_kVArh_2": 1,
            "import_kVArh_3": 1,
            "export_kVArh_1": 1,
            "export_kVArh_2": 1,
            "export_kVArh_3": 1,
            "total_kVArh_1": 1,
            "total_kVArh_2": 1,
            "total_kVArh_3": 1,

        }
    elif device_model == "SDM72D":
        if last_data is None:
            last_kwh = 0.0
        else:
            last_kwh = last_data.total_kWh if last_data.total_kWh else 0.0
            last_kwh += random.uniform(0.1, 0.5)
        return {
            "line_voltage_1": random.randrange(200, 240),
            "line_voltage_2": random.randrange(200, 240),
            "line_voltage_3": random.randrange(200, 240),
            "current_1": random.randrange(1, 20),
            "current_2": random.randrange(1, 20),
            "current_3": random.randrange(1, 20),
            "power_1": 0.22,
            "power_2": 0.22,
            "power_3": 0.22,
            "total_kWh": last_kwh,

            "active_power_1": 0.22,
            "active_power_2": 0.22,
            "active_power_3": 0.22,
            "reactive_power_1": 0.22,
            "reactive_power_2": 0.22,
            "reactive_power_3": 0.22,
            "power_factor_1": 1,
            "power_factor_2": 1,
            "power_factor_3": 1,
            "total_system_power": 1,
            "total_system_power_factor": 1,
            "total_system_VA": 1,
            "total_system_VAr": 1,
            "total_import_kwh": 1,
            "total_export_kwh": 1,
            "_1_to_2_voltage": 1,
            "_2_to_3_voltage": 1,
            "_3_to_1_voltage": 1,
            "neutral_current": 1,
            "total_kVArh": 1,
            "total_import_active_power": 1,
            "total_export_active_power": 1,
        }
