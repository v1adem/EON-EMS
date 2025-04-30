import logging.handlers
import logging
logger = logging.getLogger(__name__)

import pytz
import sys
import json
import os

from rich.logging import Console
from rich.logging import RichHandler


_CONFIG = {}
_CONFIG_PATH = None
_LOG_DIR = None
LOG_FILE = 'app.log'
MAX_LOG_SIZE = 1024 * 1024  # 1 MB
BACKUP_COUNT = 3


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def get_config_path():
    global _CONFIG_PATH
    if _CONFIG_PATH is None:
        appdata_dir = os.getenv('APPDATA') if sys.platform == 'win32' else os.path.expanduser('~/.config')
        app_dir = os.path.join(appdata_dir, 'EON')
        os.makedirs(app_dir, exist_ok=True)
        _CONFIG_PATH = os.path.join(app_dir, 'conf.json')
    return _CONFIG_PATH


def get_log_dir():
    global _LOG_DIR
    if _LOG_DIR is None:
        config_dir = os.path.dirname(get_config_path())
        _LOG_DIR = os.path.join(config_dir, 'logs')
        os.makedirs(_LOG_DIR, exist_ok=True)
    return _LOG_DIR


def get_log_file_path():
    return os.path.join(get_log_dir(), LOG_FILE)


class TortoiseFilter(logging.Filter):
    def filter(self, record):
        return not record.name.startswith('tortoise')

def init_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(message)s')

    console = Console()
    console_handler = RichHandler(console=console, rich_tracebacks=True, show_path=False)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    log_file_path = get_log_file_path()
    file_handler = logging.handlers.RotatingFileHandler(
        log_file_path,
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    tortoise_filter = TortoiseFilter()
    file_handler.addFilter(tortoise_filter)

    logger.addHandler(file_handler)


def init_config():
    global _CONFIG
    config_path = get_config_path()
    default_config = {
        "deleting_time": 180,
        "timezone": "Europe/Kyiv"
    }
    try:
        with open(config_path, "r", encoding="utf-8") as file:
            _CONFIG = json.load(file)
            for key, value in default_config.items():
                if key not in _CONFIG:
                    _CONFIG[key] = value
                    _save_config()
    except (FileNotFoundError, json.JSONDecodeError):
        _CONFIG = default_config
        _save_config()
    except Exception as e:
        logger.error(f"Config initialization error: {e}")


def _save_config():
    config_path = get_config_path()
    try:
        with open(config_path, "w", encoding="utf-8") as file:
            json.dump(_CONFIG, file, indent=4)
    except Exception as e:
        logger.error(f"Config saving error: {e}")


def get_deleting_time():
    if not _CONFIG:
        init_config()
    return _CONFIG.get("deleting_time", 180)


def set_deleting_time(new_time):
    _CONFIG["deleting_time"] = new_time
    _save_config()


def get_timezone():
    if not _CONFIG:
        init_config()
    timezone_str = _CONFIG.get('timezone', 'Europe/Kyiv')
    try:
        return pytz.timezone(timezone_str)
    except pytz.exceptions.UnknownTimeZoneError:
        logger.warning(f"Invalid timezone: {timezone_str}. Using default: Europe/Kyiv")
        _CONFIG['timezone'] = 'Europe/Kyiv'
        _save_config()
        return pytz.timezone('Europe/Kyiv')


def set_timezone(new_timezone_str):
    _CONFIG['timezone'] = new_timezone_str
    _save_config()

