import logging
import logging.handlers
import json
import os
import sys
import threading
import pytz

logger = logging.getLogger(__name__)


class AppConfig:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.lock = threading.Lock()
        self.config_path = self._get_config_path()
        self.default_config = {
            "deleting_time": 180,
            "timezone": "Europe/Kyiv",
            "warnings": False  # Тепер використовуємо чистий Boolean замість рядка
        }
        self.config_data = {}
        self.load_config()
        self._initialized = True

    def _get_config_path(self):
        appdata_dir = os.getenv('APPDATA') if sys.platform == 'win32' else os.path.expanduser('~/.config')
        app_dir = os.path.join(appdata_dir, 'EON')
        os.makedirs(app_dir, exist_ok=True)
        return os.path.join(app_dir, 'conf.json')

    def load_config(self):
        with self.lock:
            try:
                if os.path.exists(self.config_path):
                    with open(self.config_path, "r", encoding="utf-8") as file:
                        self.config_data = json.load(file)
                else:
                    self.config_data = self.default_config.copy()
                    self._save_config_unlocked()

                # Перевірка наявності всіх дефолтних ключів
                updated = False
                for key, value in self.default_config.items():
                    if key not in self.config_data:
                        self.config_data[key] = value
                        updated = True
                if updated:
                    self._save_config_unlocked()
            except Exception as e:
                logger.error(f"Config loading error, using defaults: {e}")
                self.config_data = self.default_config.copy()

    def _save_config_unlocked(self):
        """Внутрішній метод запису (має викликатися під lock)"""
        try:
            with open(self.config_path, "w", encoding="utf-8") as file:
                json.dump(self.config_data, file, indent=4)
        except Exception as e:
            logger.error(f"Config saving error: {e}")

    def get(self, key, default=None):
        with self.lock:
            return self.config_data.get(key, default)

    def set(self, key, value):
        with self.lock:
            self.config_data[key] = value
            self._save_config_unlocked()


# Експортуємо один глобальний інстанс для всього додатку
config_manager = AppConfig()


# Зберігаємо старі функції-обгортки для сумісності з вашим поточним кодом
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def init_config():
    # Виклик ініціалізує синглтон
    _ = AppConfig()


def get_deleting_time():
    return config_manager.get("deleting_time", 180)


def set_deleting_time(new_time):
    config_manager.set("deleting_time", new_time)


def get_timezone():
    timezone_str = config_manager.get('timezone', 'Europe/Kyiv')
    try:
        return pytz.timezone(timezone_str)
    except pytz.exceptions.UnknownTimeZoneError:
        config_manager.set('timezone', 'Europe/Kyiv')
        return pytz.timezone('Europe/Kyiv')


def set_timezone(new_timezone_str):
    config_manager.set('timezone', new_timezone_str)


def get_warnings():
    # Повертає чистий bool
    return bool(config_manager.get("warnings", False))


def toggle_warnings():
    current = get_warnings()
    config_manager.set("warnings", not current)


def init_logger():
    # Ваша поточна функція логера (залишається без змін)
    logger_root = logging.getLogger()
    logger_root.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(message)s')

    appdata_dir = os.getenv('APPDATA') if sys.platform == 'win32' else os.path.expanduser('~/.config')
    log_dir = os.path.join(appdata_dir, 'EON', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file_path = os.path.join(log_dir, 'app.log')

    file_handler = logging.handlers.RotatingFileHandler(
        log_file_path, maxBytes=1024 * 1024, backupCount=3, encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger_root.addHandler(file_handler)