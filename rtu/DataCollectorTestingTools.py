import random
from datetime import datetime, timedelta, timezone

from models.Report import SDM72Report, SDM72ReportTmp, SDM630ReportTmp, SDM120Report, SDM630Report
from tools.config import get_demo_port_status  # Припускаємо, що цей імпорт працює


def rand_variation(value, variation_percent=5):
    delta = value * (variation_percent / 100)
    return round(random.uniform(value - delta, value + delta), 2)


def _calculate_energy_increment(last_power_watts, current_power_watts, last_timestamp_dt, current_timestamp_dt):
    if last_timestamp_dt is None or current_timestamp_dt <= last_timestamp_dt:
        return 0.0

    if last_timestamp_dt.tzinfo is None:
        last_timestamp_dt = last_timestamp_dt.replace(tzinfo=timezone.utc)
    if current_timestamp_dt.tzinfo is None:
        current_timestamp_dt = current_timestamp_dt.replace(tzinfo=timezone.utc)

    time_diff: timedelta = current_timestamp_dt - last_timestamp_dt
    delta_time_seconds = time_diff.total_seconds()

    avg_power_watts = (last_power_watts + current_power_watts) / 2

    energy_increment_kwh = (avg_power_watts / 1000) * (delta_time_seconds / 3600)
    return energy_increment_kwh


def _generate_sdm120_data(last_data, current_timestamp_dt):
    voltage_1 = rand_variation(230)
    current_1 = rand_variation(10)
    power_1 = round(voltage_1 * current_1 * 0.8, 3)

    last_power_1 = getattr(last_data, 'power_1', 0.0) if last_data else 0.0
    last_total_active_energy = getattr(last_data, 'total_active_energy', 0.0) if last_data else 0.0
    last_timestamp_dt = getattr(last_data, 'timestamp', None) if last_data else None

    energy_increment = _calculate_energy_increment(last_power_1, power_1, last_timestamp_dt, current_timestamp_dt)
    total_active_energy = round(last_total_active_energy + energy_increment, 3)

    return {
        "line_voltage_1": voltage_1,
        "current_1": current_1,
        "power_1": power_1,
        "total_active_energy": total_active_energy,
        "total_reactive_energy": 0.0,
        "active_power_1": power_1,
        "reactive_power_1": 0.0,
        "power_factor_1": 1.0,
        "frequency_1": 50.0,
        "import_active_energy_1": total_active_energy,  # Припускаємо, що це імпорт
        "export_active_energy_1": 0.0,
    }


def _generate_sdm630_data(last_data, current_timestamp_dt):
    data = {}
    total_system_power = 0
    total_kWh_sum = 0
    total_kVAh_sum = 0
    total_kVArh_sum = 0

    last_timestamp_dt = getattr(last_data, 'timestamp', None) if last_data else None

    for i in range(1, 4):
        voltage = rand_variation(230)
        current = rand_variation(10)
        power = round(voltage * current * 0.8, 3)  # Активна потужність у Ваттах
        va = round(voltage * current, 3)  # Повна потужність у ВА
        var = round(va * 0.6, 3)  # Реактивна потужність у ВАр (Q = S * sin(phi))

        data[f"line_voltage_{i}"] = voltage
        data[f"current_{i}"] = current
        data[f"power_{i}"] = power
        data[f"active_power_{i}"] = power
        data[f"reactive_power_{i}"] = var
        data[f"power_factor_{i}"] = 0.8

        total_system_power += power

        # Розрахунок активної енергії по фазах
        last_power_i = getattr(last_data, f'power_{i}', 0.0) if last_data else 0.0
        last_kwh_i = getattr(last_data, f'total_kWh_{i}', 0.0) if last_data else 0.0

        energy_increment_kwh_i = _calculate_energy_increment(last_power_i, power, last_timestamp_dt,
                                                             current_timestamp_dt)
        data[f"total_kWh_{i}"] = round(last_kwh_i + energy_increment_kwh_i, 3)
        total_kWh_sum += data[f"total_kWh_{i}"]

        # Розрахунок повної енергії по фазах
        last_va_i = getattr(last_data, f'total_system_VA_{i}',
                            0.0) if last_data else 0.0  # Припускаємо, що є такий ключ
        energy_increment_kvah_i = _calculate_energy_increment(last_va_i, va, last_timestamp_dt, current_timestamp_dt)
        data[f"total_kVAh_{i}"] = round(getattr(last_data, f'total_kVAh_{i}', 0.0) + energy_increment_kvah_i,
                                        3) if last_data else round(energy_increment_kvah_i, 3)
        total_kVAh_sum += data[f"total_kVAh_{i}"]

        # Розрахунок реактивної енергії по фазах
        last_var_i = getattr(last_data, f'reactive_power_{i}', 0.0) if last_data else 0.0
        energy_increment_kvarh_i = _calculate_energy_increment(last_var_i, var, last_timestamp_dt, current_timestamp_dt)
        data[f"total_kVArh_{i}"] = round(getattr(last_data, f'total_kVArh_{i}', 0.0) + energy_increment_kvarh_i,
                                         3) if last_data else round(energy_increment_kvarh_i, 3)
        total_kVArh_sum += data[f"total_kVArh_{i}"]

    # Додаємо загальносистемні значення
    data["total_system_power"] = round(total_system_power, 3)
    data["total_kWh"] = round(total_kWh_sum, 3)  # Сума кВт*год по фазах

    # Додаємо інші значення
    data["total_system_power_factor"] = round(total_system_power / (total_system_power / 0.8),
                                              3) if total_system_power > 0 else 1.0
    data["total_system_VA"] = round(total_system_power / 0.8, 3)  # S = P / cos(phi)
    data["total_system_VAr"] = round(total_system_power * 0.6 / 0.8, 3)  # Q = P * tg(phi)

    data["total_import_kwh"] = data["total_kWh"]  # Припускаємо, що все є імпортом
    data["total_export_kwh"] = 0.0
    data["total_import_kVAh"] = round(total_kVAh_sum, 3)  # Загальна імпортна повна енергія
    data["total_export_kVAh"] = 0.0
    data["total_kVAh"] = round(total_kVAh_sum, 3)

    data["_1_to_2_voltage"] = rand_variation(400)  # Міжфазна напруга
    data["_2_to_3_voltage"] = rand_variation(400)
    data["_3_to_1_voltage"] = rand_variation(400)
    data["neutral_current"] = rand_variation(0.5)  # Невеликий струм нейтралі
    data["line_voltage_THD_1"] = 1.0
    data["line_voltage_THD_2"] = 1.0
    data["line_voltage_THD_3"] = 1.0
    data["line_current_THD_1"] = 1.0
    data["line_current_THD_2"] = 1.0
    data["line_current_THD_3"] = 1.0
    data["current_demand_1"] = data["current_1"]
    data["current_demand_2"] = data["current_2"]
    data["current_demand_3"] = data["current_3"]
    data["phase_voltage_THD_1"] = 1.0
    data["phase_voltage_THD_2"] = 1.0
    data["phase_voltage_THD_3"] = 1.0
    data["average_line_to_line_voltage_THD"] = 1.0
    data["total_kVArh"] = round(total_kVArh_sum, 3)  # Загальна реактивна енергія

    data["import_kWh_1"] = data["total_kWh_1"]
    data["import_kWh_2"] = data["total_kWh_2"]
    data["import_kWh_3"] = data["total_kWh_3"]
    data["export_kWh_1"] = 0.0
    data["export_kWh_2"] = 0.0
    data["export_kWh_3"] = 0.0

    data["import_kVArh_1"] = data["total_kVArh_1"]
    data["import_kVArh_2"] = data["total_kVArh_2"]
    data["import_kVArh_3"] = data["total_kVArh_3"]
    data["export_kVArh_1"] = 0.0
    data["export_kVArh_2"] = 0.0
    data["export_kVArh_3"] = 0.0

    return data


def _generate_sdm72_data(last_data, current_timestamp_dt):
    data = {}
    total_power_sum = 0
    total_va_sum = 0
    total_var_sum = 0

    last_timestamp_dt = getattr(last_data, 'timestamp', None) if last_data else None

    for i in range(1, 4):
        voltage = rand_variation(230)
        current = rand_variation(10)
        power = round(voltage * current * 0.8, 3)
        va = round(voltage * current, 3)
        var = round(va * 0.6, 3)

        data[f"line_voltage_{i}"] = voltage
        data[f"current_{i}"] = current
        data[f"power_{i}"] = power
        data[f"active_power_{i}"] = power
        data[f"reactive_power_{i}"] = var
        data[f"power_factor_{i}"] = 0.8

        total_power_sum += power
        total_va_sum += va
        total_var_sum += var

    last_total_kwh = getattr(last_data, "total_kWh", 0.0) if last_data else 0.0
    last_total_power_sum = getattr(last_data, "total_system_power", 0.0) if last_data else 0.0

    energy_increment_kwh = _calculate_energy_increment(last_total_power_sum, total_power_sum, last_timestamp_dt,
                                                       current_timestamp_dt)
    total_kwh = round(last_total_kwh + energy_increment_kwh, 3)

    data["total_kWh"] = total_kwh
    data["total_system_power"] = round(total_power_sum, 3)

    data["total_system_power_factor"] = round(total_power_sum / total_va_sum, 3) if total_va_sum > 0 else 1.0
    data["total_system_VA"] = round(total_va_sum, 3)
    data["total_system_VAr"] = round(total_var_sum, 3)
    data["total_import_kwh"] = total_kwh
    data["total_export_kwh"] = 0.0
    data["_1_to_2_voltage"] = rand_variation(400)
    data["_2_to_3_voltage"] = rand_variation(400)
    data["_3_to_1_voltage"] = rand_variation(400)
    data["neutral_current"] = rand_variation(0.5)

    last_total_kvarh = getattr(last_data, "total_kVArh", 0.0) if last_data else 0.0
    energy_increment_kvarh = _calculate_energy_increment(total_var_sum, total_var_sum, last_timestamp_dt,
                                                         current_timestamp_dt)
    data["total_kVArh"] = round(last_total_kvarh + energy_increment_kvarh, 3)

    data["total_import_active_power"] = total_power_sum
    data["total_export_active_power"] = 0.0

    return data


def get_test_data(device_model, last_data, current_timestamp_dt=None):
    if get_demo_port_status() is False:
        return {}

    if current_timestamp_dt is None:
        current_timestamp_dt = datetime.now(timezone.utc)

    if device_model == "SDM120":
        return _generate_sdm120_data(last_data, current_timestamp_dt)
    elif device_model == "SDM630":
        return _generate_sdm630_data(last_data, current_timestamp_dt)
    elif device_model == "SDM72":
        return _generate_sdm72_data(last_data, current_timestamp_dt)
    else:
        return None


async def generate_historical_data(device):
    start_date = datetime.now().date() - timedelta(days=60)  # Approximately 2 months ago
    current_date = datetime(start_date.year, start_date.month, start_date.day,
                            tzinfo=timezone.utc)  # Convert to datetime with timezone

    delay = device.reading_time
    db_model = get_db_model(device)
    
    historical_data = []
    last_data = None

    while current_date <= datetime.now(timezone.utc):
        data = get_test_data(device, last_data, current_date)
        last_data = data
        historical_data.append(db_model(**data))
        current_date += timedelta(minutes=delay)
    await db_model.bulk_create(historical_data, batch_size=100)
        
def get_db_model(device):
    if device.model == "SDM120":
        return SDM120Report
    elif device.model == "SDM630":
        return SDM630Report
    elif device.model == "SDM72":
        return SDM72Report
    else:
        pass