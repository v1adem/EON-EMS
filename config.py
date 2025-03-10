def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


import os
import sys
import json


def get_config_path():
    appdata_dir = os.getenv('APPDATA') if sys.platform == 'win32' else os.path.expanduser('~/.config')
    app_dir = os.path.join(appdata_dir, 'EON')
    os.makedirs(app_dir, exist_ok=True)
    return os.path.join(app_dir, 'conf.json')


DELETING_TIME = None


def get_deleting_time():
    global DELETING_TIME
    config_path = get_config_path()

    try:
        with open(config_path, "r", encoding="utf-8") as file:
            config = json.load(file)
            DELETING_TIME = config.get("deleting_time", 180)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Помилка завантаження конфігурації: {e}")
        DELETING_TIME = 180
    return DELETING_TIME


def set_deleting_time(new_time):
    global DELETING_TIME
    DELETING_TIME = new_time

    config_path = get_config_path()

    try:
        try:
            with open(config_path, "r", encoding="utf-8") as file:
                config = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            config = {}

        config["deleting_time"] = new_time

        with open(config_path, "w", encoding="utf-8") as file:
            json.dump(config, file, indent=4)

    except Exception as e:
        print(f"Помилка запису конфігурації: {e}")
