import os
import sys


def resource_path(relative_path):
    """
    Отримує абсолютний шлях до ресурсу, враховуючи упаковку в .exe (PyInstaller).
    """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


import json

DELETING_TIME = None


def get_deleting_time():
    global DELETING_TIME
    try:
        with open("conf.json", "r", encoding="utf-8") as file:
            config = json.load(file)
            DELETING_TIME = config.get("deleting_time")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Помилка завантаження конфігурації: {e}")
        DELETING_TIME = 10
    return DELETING_TIME


def set_deleting_time(new_time):
    """Оновлює значення часу видалення у глобальній змінній та записує його у файл conf.json."""
    global DELETING_TIME
    DELETING_TIME = new_time

    try:
        try:
            with open("conf.json", "r", encoding="utf-8") as file:
                config = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            config = {}

        config["deleting_time"] = new_time

        with open("conf.json", "w", encoding="utf-8") as file:
            json.dump(config, file, indent=4)

    except Exception as e:
        print(f"Помилка запису конфігурації: {e}")
