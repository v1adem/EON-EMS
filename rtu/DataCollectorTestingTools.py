import random

from tools.config import get_demo_port_status


def rand_variation(value, variation_percent=5):
    delta = value * (variation_percent / 100)
    return round(random.uniform(value - delta, value + delta), 2)

def get_test_data(device_model, last_data):
    if get_demo_port_status() is False:
        return {}

    if device_model == "SDM120":
        voltage_1 = rand_variation(230)
        current_1 = rand_variation(10)
        power_1 = round(voltage_1 * current_1 * 0.8 / 1000, 3)

        if last_data is None:
            last_kwh = 0.0
        else:
            last_kwh = last_data.total_active_energy or 0.0
            last_kwh += random.uniform(0, power_1)

        return {
            "line_voltage_1": rand_variation(230),
            "current_1": rand_variation(10),
            "power_1": power_1,
            "total_active_energy": round(last_kwh, 3),
            "total_reactive_energy": 0.0,

            "active_power_1": power_1,
            "reactive_power_1": 0.0,
            "power_factor_1": 1.0,
            "frequency_1": 50.0,
            "import_active_energy_1": 0.0,
            "export_active_energy_1": 0.0,
        }

    elif device_model == "SDM630":
        voltage_1 = rand_variation(230)
        current_1 = rand_variation(10)
        power_1 = round(voltage_1 * current_1 * 0.8 / 1000, 3)

        voltage_2 = rand_variation(230)
        current_2 = rand_variation(10)
        power_2 = round(voltage_2 * current_2 * 0.8 / 1000, 3)

        voltage_3 = rand_variation(230)
        current_3 = rand_variation(10)
        power_3 = round(voltage_3 * current_3 * 0.8 / 1000, 3)

        if last_data is None:
            kwh_1 = kwh_2 = kwh_3 = 0.0
        else:
            kwh_1 = last_data.total_kWh_1 or 0.0
            kwh_2 = last_data.total_kWh_2 or 0.0
            kwh_3 = last_data.total_kWh_3 or 0.0
            kwh_1 += random.uniform(0, power_1)
            kwh_2 += random.uniform(0, power_2)
            kwh_3 += random.uniform(0, power_3)

        total_kwh = kwh_1 + kwh_2 + kwh_3

        return {
            "line_voltage_1": rand_variation(230),
            "line_voltage_2": rand_variation(230),
            "line_voltage_3": rand_variation(230),
            "current_1": rand_variation(10),
            "current_2": rand_variation(10),
            "current_3": rand_variation(10),
            "power_1": power_1,
            "power_2": power_2,
            "power_3": power_3,

            "total_kWh_1": round(kwh_1, 3),
            "total_kWh_2": round(kwh_2, 3),
            "total_kWh_3": round(kwh_3, 3),
            "total_kWh": round(total_kwh, 3),

            "power_factor_1": 1.0,
            "power_factor_2": 1.0,
            "power_factor_3": 1.0,
            "total_system_power": power_1 + power_2 + power_3,
            "total_system_power_factor": 1.0,
            "total_system_VA": 1.0,
            "total_system_VAr": 1.0,
            "total_import_kwh": 1.0,
            "total_export_kwh": 1.0,
            "total_import_kVAh": 1.0,
            "total_export_kVAh": 1.0,
            "total_kVAh": 1.0,
            "_1_to_2_voltage": 1.0,
            "_2_to_3_voltage": 1.0,
            "_3_to_1_voltage": 1.0,
            "neutral_current": 1.0,
            "line_voltage_THD_1": 1.0,
            "line_voltage_THD_2": 1.0,
            "line_voltage_THD_3": 1.0,
            "line_current_THD_1": 1.0,
            "line_current_THD_2": 1.0,
            "line_current_THD_3": 1.0,
            "current_demand_1": 1.0,
            "current_demand_2": 1.0,
            "current_demand_3": 1.0,
            "phase_voltage_THD_1": 1.0,
            "phase_voltage_THD_2": 1.0,
            "phase_voltage_THD_3": 1.0,
            "average_line_to_line_voltage_THD": 1.0,
            "total_kVArh": 1.0,
            "import_kWh_1": 1.0,
            "import_kWh_2": 1.0,
            "import_kWh_3": 1.0,
            "export_kWh_1": 1.0,
            "export_kWh_2": 1.0,
            "export_kWh_3": 1.0,
            "import_kVArh_1": 1.0,
            "import_kVArh_2": 1.0,
            "import_kVArh_3": 1.0,
            "export_kVArh_1": 1.0,
            "export_kVArh_2": 1.0,
            "export_kVArh_3": 1.0,
            "total_kVArh_1": 1.0,
            "total_kVArh_2": 1.0,
            "total_kVArh_3": 1.0,
        }

    elif device_model == "SDM72":
        voltage_1 = rand_variation(230)
        current_1 = rand_variation(10)
        power_1 = round(voltage_1 * current_1 * 0.8 / 1000, 3)

        voltage_2 = rand_variation(230)
        current_2 = rand_variation(10)
        power_2 = round(voltage_2 * current_2 * 0.8 / 1000, 3)

        voltage_3 = rand_variation(230)
        current_3 = rand_variation(10)
        power_3 = round(voltage_3 * current_3 * 0.8 / 1000, 3)

        if last_data is None:
            total_kwh = 0.0
        else:
            total_kwh = last_data.total_kWh or 0.0
            total_kwh += random.uniform(0, power_1 + power_2 + power_3)

        return {
            "line_voltage_1": rand_variation(230),
            "line_voltage_2": rand_variation(230),
            "line_voltage_3": rand_variation(230),
            "current_1": rand_variation(10),
            "current_2": rand_variation(10),
            "current_3": rand_variation(10),
            "power_1": power_1,
            "power_2": power_2,
            "power_3": power_3,
            "total_kWh": round(total_kwh, 3),

            "active_power_1": power_1,
            "active_power_2": power_2,
            "active_power_3": power_3,
            "reactive_power_1": 0.0,
            "reactive_power_2": 0.0,
            "reactive_power_3": 0.0,
            "power_factor_1": 1.0,
            "power_factor_2": 1.0,
            "power_factor_3": 1.0,
            "total_system_power": power_1 + power_2 + power_3,
            "total_system_power_factor": 1.0,
            "total_system_VA": 1.0,
            "total_system_VAr": 1.0,
            "total_import_kwh": 1.0,
            "total_export_kwh": 1.0,
            "_1_to_2_voltage": 1.0,
            "_2_to_3_voltage": 1.0,
            "_3_to_1_voltage": 1.0,
            "neutral_current": 1.0,
            "total_kVArh": 1.0,
            "total_import_active_power": 1.0,
            "total_export_active_power": 1.0,
        }
    else:
        return None

