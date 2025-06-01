import random
import time
from datetime import datetime, timedelta, timezone  # Імпортуємо timezone!
from types import SimpleNamespace  # Для створення простих об'єктів для last_data

from tools.config import get_demo_port_status  # Припускаємо, що цей імпорт працює


def rand_variation(value, variation_percent=5):
    """Генерує випадкове значення в межах заданого відсотка варіації від початкового значення."""
    delta = value * (variation_percent / 100)
    return round(random.uniform(value - delta, value + delta), 2)


def _calculate_energy_increment(last_power_watts, current_power_watts, last_timestamp_dt, current_timestamp_dt):
    """
    Розраховує приріст енергії (в кВт*год) на основі середньої потужності та минулого часу.
    Час передається як datetime об'єкти.
    """
    # Якщо попереднього звіту немає, або timestamp відсутній/некоректний
    # Або якщо поточний час раніше або дорівнює останньому (може статися при дуже швидких викликах)
    if last_timestamp_dt is None or current_timestamp_dt <= last_timestamp_dt:
        return 0.0

    # Переконуємось, що обидва datetime об'єкти timezone-aware і в UTC
    if last_timestamp_dt.tzinfo is None:
        last_timestamp_dt = last_timestamp_dt.replace(tzinfo=timezone.utc)
    if current_timestamp_dt.tzinfo is None:
        current_timestamp_dt = current_timestamp_dt.replace(tzinfo=timezone.utc)

    time_diff: timedelta = current_timestamp_dt - last_timestamp_dt
    delta_time_seconds = time_diff.total_seconds()

    # Розраховуємо середню потужність у Ваттах
    avg_power_watts = (last_power_watts + current_power_watts) / 2

    # Конвертуємо потужність в кВт та час в години для розрахунку кВт*год
    energy_increment_kwh = (avg_power_watts / 1000) * (delta_time_seconds / 3600)
    return energy_increment_kwh


def _generate_sdm120_data(last_data, current_timestamp_dt):
    """Генерує тестові дані для моделі пристрою SDM120."""
    # Генеруємо поточні миттєві значення
    voltage_1 = rand_variation(230)
    current_1 = rand_variation(10)
    power_1 = round(voltage_1 * current_1 * 0.8, 3)  # Миттєва потужність у Ваттах

    # Отримуємо попередні значення потужності та загальної енергії
    # Якщо last_data немає, використовуємо 0.0 та None для timestamp
    last_power_1 = getattr(last_data, 'power_1', 0.0) if last_data else 0.0
    last_total_active_energy = getattr(last_data, 'total_active_energy', 0.0) if last_data else 0.0
    last_timestamp_dt = getattr(last_data, 'timestamp', None) if last_data else None

    # Розраховуємо приріст енергії та нове загальне значення
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
    """Генерує тестові дані для моделі пристрою SDM630."""
    data = {}
    total_system_power = 0
    total_kWh_sum = 0
    total_kVAh_sum = 0
    total_kVArh_sum = 0

    # Отримуємо timestamp попереднього звіту
    last_timestamp_dt = getattr(last_data, 'timestamp', None) if last_data else None

    # Генеруємо дані по фазах та розраховуємо енергію
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
        data[f"power_factor_{i}"] = 0.8  # Фіксований коефіцієнт потужності для прикладу

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
    """Генерує тестові дані спеціально для моделі пристрою SDM72."""
    data = {}
    total_power_sum = 0
    total_va_sum = 0
    total_var_sum = 0

    # Отримуємо timestamp попереднього звіту
    last_timestamp_dt = getattr(last_data, 'timestamp', None) if last_data else None

    # Генеруємо миттєві дані по фазах
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

    # Загальний кВт*год для SDM72 (сукупний, не по фазах)
    last_total_kwh = getattr(last_data, "total_kWh", 0.0) if last_data else 0.0
    last_total_power_sum = getattr(last_data, "total_system_power", 0.0) if last_data else 0.0

    energy_increment_kwh = _calculate_energy_increment(last_total_power_sum, total_power_sum, last_timestamp_dt,
                                                       current_timestamp_dt)
    total_kwh = round(last_total_kwh + energy_increment_kwh, 3)

    data["total_kWh"] = total_kwh
    data["total_system_power"] = round(total_power_sum, 3)

    # Додаємо інші значення
    data["total_system_power_factor"] = round(total_power_sum / total_va_sum, 3) if total_va_sum > 0 else 1.0
    data["total_system_VA"] = round(total_va_sum, 3)
    data["total_system_VAr"] = round(total_var_sum, 3)
    data["total_import_kwh"] = total_kwh  # Припускаємо, що все імпорт
    data["total_export_kwh"] = 0.0
    data["_1_to_2_voltage"] = rand_variation(400)
    data["_2_to_3_voltage"] = rand_variation(400)
    data["_3_to_1_voltage"] = rand_variation(400)
    data["neutral_current"] = rand_variation(0.5)

    last_total_kvarh = getattr(last_data, "total_kVArh", 0.0) if last_data else 0.0
    energy_increment_kvarh = _calculate_energy_increment(total_var_sum, total_var_sum, last_timestamp_dt,
                                                         current_timestamp_dt)  # Використовуємо total_var_sum
    data["total_kVArh"] = round(last_total_kvarh + energy_increment_kvarh, 3)

    data["total_import_active_power"] = total_power_sum  # Припускаємо, що загальна активна потужність - це імпорт
    data["total_export_active_power"] = 0.0

    return data


def get_test_data(device_model, last_data, current_timestamp_dt=None):
    """
    Генерує правдоподібні тестові дані для лічильників енергії на основі моделі пристрою,
    враховуючи попередні дані для накопичення енергії.
    current_timestamp_dt: datetime.datetime (UTC aware) - Час для якого генеруються дані.
                                                        Якщо None, використовується поточний час.
    """
    if get_demo_port_status() is False:
        return {}

    # Якщо current_timestamp_dt не вказано, використовуємо поточний час (UTC)
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


def generate_historical_data(
        device_model: str,
        num_days: int,
        report_interval_minutes: int,
        initial_last_data: SimpleNamespace = None
) -> list:
    """
    Генерує реалістичні історичні дані для пристрою за вказану кількість днів
    з певним інтервалом між звітами.

    :param device_model: Модель пристрою (наприклад, "SDM120", "SDM630", "SDM72").
    :param num_days: Кількість днів в минулому, за які потрібно згенерувати дані.
    :param report_interval_minutes: Інтервал між звітами в хвилинах (наприклад, 15, 60).
    :param initial_last_data: Початковий об'єкт SimpleNamespace з попередніми даними
                              (з полями, як у звіті, і 'timestamp'), якщо є.
                              Якщо None, дані починаються з нуля.
    :return: Список згенерованих словників зі звітами.
    """
    historical_reports = []

    current_real_time = datetime.now(timezone.utc)  # Поточний реальний час

    # Визначаємо час початку генерації історичних даних
    # Починаємо з минулого і рухаємося до поточного часу
    start_time_history = current_real_time - timedelta(days=num_days)

    # Ініціалізуємо об'єкт last_data для першого звіту
    # Якщо initial_last_data не надано, створюємо "порожній" для першого прогону
    # Встановлюємо timestamp для імітації, що він "трохи" раніше start_time_history
    last_data_point = initial_last_data
    if last_data_point is None:
        last_data_point = SimpleNamespace(
            timestamp=start_time_history - timedelta(minutes=report_interval_minutes)
            # Тут можна додати інші початкові поля, якщо це необхідно для першого звіту
            # Наприклад: total_active_energy=0.0, power_1=0.0, і т.д.
            # Однак, get_test_data вже обробляє None для last_data, використовуючи getattr(..., 0.0)
        )

    # Починаємо генерацію з першої точки після start_time_history
    current_iteration_dt = start_time_history

    # Генеруємо звіти, доки не досягнемо поточного часу
    while current_iteration_dt < current_real_time:
        # Генеруємо новий звіт для поточного часу ітерації
        new_report_data = get_test_data(device_model, last_data_point, current_timestamp_dt=current_iteration_dt)

        # Додаємо згенеровані дані до списку
        historical_reports.append(new_report_data)

        # Готуємо last_data_point для наступної ітерації
        # Для цього нам потрібні всі поля, які get_test_data згенерувала,
        # а також timestamp, який був використаний для цієї ітерації

        # Створюємо новий SimpleNamespace, копіюючи дані з new_report_data
        # і додаючи timestamp для наступного кроку
        next_last_data_point = SimpleNamespace(**new_report_data)
        next_last_data_point.timestamp = current_iteration_dt  # Зберігаємо timestamp, що був використаний

        last_data_point = next_last_data_point  # Оновлюємо last_data_point

        # Переходимо до наступної точки часу
        current_iteration_dt += timedelta(minutes=report_interval_minutes)

        # Додаткова перевірка, щоб не генерувати звіти за майбутнє, якщо current_iteration_dt
        # перевищить current_real_time після останнього додавання timedelta.
        # Це потрібно, щоб останній звіт не був за майбутнє, а лише до поточного моменту.
        if current_iteration_dt > current_real_time:
            # Згенеруємо останній звіт для поточного часу, якщо інтервал його не врахував точно
            # Це опціонально, може призвести до "надлишкового" звіту, але забезпечує,
            # що останній звіт буде максимально близьким до current_real_time
            last_report_dt = historical_reports[-1].get("timestamp")
            if last_report_dt is None or (current_real_time - last_report_dt).total_seconds() > (
                    report_interval_minutes * 60 / 2):  # Якщо останній звіт був давно
                final_report_data = get_test_data(device_model, last_data_point, current_timestamp_dt=current_real_time)
                # Перевіряємо, чи не є це повторенням останнього, щоб уникнути дублікатів
                if not historical_reports or final_report_data != historical_reports[
                    -1]:  # Порівняння може бути неточним для великих dict
                    historical_reports.append(final_report_data)
            break  # Виходимо з циклу після обробки кінцевого часу

    return historical_reports