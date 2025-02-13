class RegisterMap:
    SDM120 = {
        "line_voltage_1": {"register": 0, "type": "input", "format": "float", "units": "Volts"},
        "current_1": {"register": 6, "type": "input", "format": "float", "units": "Amps"},
        "active_power_1": {"register": 12, "type": "input", "format": "float", "units": "Watts"},
        "power_1": {"register": 18, "type": "input", "format": "float", "units": "VA"},
        "reactive_power_1": {"register": 24, "type": "input", "format": "float", "units": "VAr"},
        "power_factor_1": {"register": 30, "type": "input", "format": "float", "units": ""},
        "frequency_1": {"register": 70, "type": "input", "format": "float", "units": "Hz"},
        "import_active_energy_1": {"register": 72, "type": "input", "format": "float", "units": "kWh"},
        "export_active_energy_1": {"register": 74, "type": "input", "format": "float", "units": "kWh"},
        "total_active_energy": {"register": 342, "type": "input", "format": "float", "units": "kWh"},
        "total_reactive_energy": {"register": 344, "type": "input", "format": "float", "units": "kWh"},
    }

    SDM630 = {
        "line_voltage_1": {
            "register": 0,
            "type": "input",
            "format": "float",
            "units": "Volts"
        },
        "line_voltage_2": {
            "register": 2,
            "type": "input",
            "format": "float",
            "units": "Volts"
        },
        "line_voltage_3": {
            "register": 4,
            "type": "input",
            "format": "float",
            "units": "Volts"
        },
        "current_1": {
            "register": 6,
            "type": "input",
            "format": "float",
            "units": "Amps"
        },
        "current_2": {
            "register": 8,
            "type": "input",
            "format": "float",
            "units": "Amps"
        },
        "current_3": {
            "register": 10,
            "type": "input",
            "format": "float",
            "units": "Amps"
        },
        "power_1": {
            "register": 12,
            "type": "input",
            "format": "float",
            "units": "Watts"
        },
        "power_2": {
            "register": 14,
            "type": "input",
            "format": "float",
            "units": "Watts"
        },
        "power_3": {
            "register": 16,
            "type": "input",
            "format": "float",
            "units": "Watts"
        },
        "power_factor_1": {
            "register": 30,
            "type": "input",
            "format": "float",
            "units": ""
        },
        "power_factor_2": {
            "register": 32,
            "type": "input",
            "format": "float",
            "units": ""
        },
        "power_factor_3": {
            "register": 34,
            "type": "input",
            "format": "float",
            "units": ""
        },
        "total_system_power": {
            "register": 52,
            "type": "input",
            "format": "float",
            "units": "Watts"
        },
        "total_system_VA": {
            "register": 56,
            "type": "input",
            "format": "float",
            "units": "Watts"
        },
        "total_system_VAr": {
            "register": 60,
            "type": "input",
            "format": "float",
            "units": "Watts"
        },
        "total_system_power_factor": {
            "register": 62,
            "type": "input",
            "format": "float",
            "units": ""
        },
        "total_import_kwh": {
            "register": 72,
            "type": "input",
            "format": "float",
            "units": "kWh"
        },
        "total_export_kwh": {
            "register": 74,
            "type": "input",
            "format": "float",
            "units": "kWh"
        },
        "total_import_kVAh": {
            "register": 76,
            "type": "input",
            "format": "float",
            "units": "kVAh"
        },
        "total_export_kVAh": {
            "register": 78,
            "type": "input",
            "format": "float",
            "units": "kVAh"
        },
        "total_kVAh": {
            "register": 80,
            "type": "input",
            "format": "float",
            "units": "kVAh"
        },
        "_1_to_2_voltage": {
            "register": 200,
            "type": "input",
            "format": "float",
            "units": "Volts"
        },
        "_2_to_3_voltage": {
            "register": 202,
            "type": "input",
            "format": "float",
            "units": "Volts"
        },
        "_3_to_1_voltage": {
            "register": 204,
            "type": "input",
            "format": "float",
            "units": "Volts"
        },
        "neutral_current": {
            "register": 224,
            "type": "input",
            "format": "float",
            "units": "Amps"
        },
        "line_voltage_THD_1": {
            "register": 234,
            "type": "input",
            "format": "float",
            "units": "%"
        },
        "line_voltage_THD_2": {
            "register": 236,
            "type": "input",
            "format": "float",
            "units": "%"
        },
        "line_voltage_THD_3": {
            "register": 238,
            "type": "input",
            "format": "float",
            "units": "%"
        },
        "line_current_THD_1": {
            "register": 240,
            "type": "input",
            "format": "float",
            "units": "%"
        },
        "line_current_THD_2": {
            "register": 242,
            "type": "input",
            "format": "float",
            "units": "%"
        },
        "line_current_THD_3": {
            "register": 244,
            "type": "input",
            "format": "float",
            "units": "%"
        },
        "current_demand_1": {
            "register": 258,
            "type": "input",
            "format": "float",
            "units": "Amps"
        },
        "current_demand_2": {
            "register": 260,
            "type": "input",
            "format": "float",
            "units": "Amps"
        },
        "current_demand_3": {
            "register": 262,
            "type": "input",
            "format": "float",
            "units": "Amps"
        },
        "phase_voltage_THD_1": {
            "register": 334,
            "type": "input",
            "format": "float",
            "units": "%"
        },
        "phase_voltage_THD_2": {
            "register": 336,
            "type": "input",
            "format": "float",
            "units": "%"
        },
        "phase_voltage_THD_3": {
            "register": 338,
            "type": "input",
            "format": "float",
            "units": "%"
        },
        "average_line_to_line_voltage_THD": {
            "register": 340,
            "type": "input",
            "format": "float",
            "units": "%"
        },
        "total_kWh": {
            "register": 342,
            "type": "input",
            "format": "float",
            "units": "kWh"
        },
        "total_kVArh": {
            "register": 344,
            "type": "input",
            "format": "float",
            "units": "kVArh"
        },
        "import_kWh_1": {
            "register": 346,
            "type": "input",
            "format": "float",
            "units": "kWh"
        },
        "import_kWh_2": {
            "register": 348,
            "type": "input",
            "format": "float",
            "units": "kWh"
        },
        "import_kWh_3": {
            "register": 350,
            "type": "input",
            "format": "float",
            "units": "kWh"
        },
        "export_kWh_1": {
            "register": 352,
            "type": "input",
            "format": "float",
            "units": "kWh"
        },
        "export_kWh_2": {
            "register": 354,
            "type": "input",
            "format": "float",
            "units": "kWh"
        },
        "export_kWh_3": {
            "register": 356,
            "type": "input",
            "format": "float",
            "units": "kWh"
        },
        "total_kWh_1": {
            "register": 358,
            "type": "input",
            "format": "float",
            "units": "kWh"
        },
        "total_kWh_2": {
            "register": 360,
            "type": "input",
            "format": "float",
            "units": "kWh"
        },
        "total_kWh_3": {
            "register": 362,
            "type": "input",
            "format": "float",
            "units": "kWh"
        },
        "import_kVArh_1": {
            "register": 364,
            "type": "input",
            "format": "float",
            "units": "kWh"
        },
        "import_kVArh_2": {
            "register": 366,
            "type": "input",
            "format": "float",
            "units": "kWh"
        },
        "import_kVArh_3": {
            "register": 368,
            "type": "input",
            "format": "float",
            "units": "kWh"
        },
        "export_kVArh_1": {
            "register": 370,
            "type": "input",
            "format": "float",
            "units": "kVArh"
        },
        "export_kVArh_2": {
            "register": 372,
            "type": "input",
            "format": "float",
            "units": "kVArh"
        },
        "export_kVArh_3": {
            "register": 374,
            "type": "input",
            "format": "float",
            "units": "kVArh"
        },
        "total_kVArh_1": {
            "register": 376,
            "type": "input",
            "format": "float",
            "units": "kVArh"
        },
        "total_kVArh_2": {
            "register": 378,
            "type": "input",
            "format": "float",
            "units": "kVArh"
        },
        "total_kVArh_3": {
            "register": 380,
            "type": "input",
            "format": "float",
            "units": "kVArh"
        }
    }

    SDM72D = {
        "line_voltage_1": {
            "register": 0,
            "type": "input",
            "format": "float",
            "units": "Volts"
        },
        "line_voltage_2": {
            "register": 2,
            "type": "input",
            "format": "float",
            "units": "Volts"
        },
        "line_voltage_3": {
            "register": 4,
            "type": "input",
            "format": "float",
            "units": "Volts"
        },
        "current_1": {
            "register": 6,
            "type": "input",
            "format": "float",
            "units": "Amps"
        },
        "current_2": {
            "register": 8,
            "type": "input",
            "format": "float",
            "units": "Amps"
        },
        "current_3": {
            "register": 10,
            "type": "input",
            "format": "float",
            "units": "Amps"
        },
        "active_power_1": {
            "register": 12,
            "type": "input",
            "format": "float",
            "units": "Watts"
        },
        "active_power_2": {
            "register": 14,
            "type": "input",
            "format": "float",
            "units": "Watts"
        },
        "active_power_3": {
            "register": 16,
            "type": "input",
            "format": "float",
            "units": "Watts"
        },
        "power_1": {
            "register": 18,
            "type": "input",
            "format": "float",
            "units": "Watts"
        },
        "power_2": {
            "register": 20,
            "type": "input",
            "format": "float",
            "units": "Watts"
        },
        "power_3": {
            "register": 22,
            "type": "input",
            "format": "float",
            "units": "Watts"
        },
        "reactive_power_1": {
            "register": 12,
            "type": "input",
            "format": "float",
            "units": "Watts"
        },
        "reactive_power_2": {
            "register": 14,
            "type": "input",
            "format": "float",
            "units": "Watts"
        },
        "reactive_power_3": {
            "register": 16,
            "type": "input",
            "format": "float",
            "units": "Watts"
        },
        "power_factor_1": {
            "register": 30,
            "type": "input",
            "format": "float",
            "units": ""
        },
        "power_factor_2": {
            "register": 32,
            "type": "input",
            "format": "float",
            "units": ""
        },
        "power_factor_3": {
            "register": 34,
            "type": "input",
            "format": "float",
            "units": ""
        },
        "total_system_power": {
            "register": 52,
            "type": "input",
            "format": "float",
            "units": "Watts"
        },
        "total_system_VA": {
            "register": 56,
            "type": "input",
            "format": "float",
            "units": "VA"
        },
        "total_system_VAr": {
            "register": 60,
            "type": "input",
            "format": "float",
            "units": "VAr"
        },
        "total_system_power_factor": {
            "register": 62,
            "type": "input",
            "format": "float",
            "units": ""
        },
        "total_import_kwh": {
            "register": 72,
            "type": "input",
            "format": "float",
            "units": "kWh"
        },
        "total_export_kwh": {
            "register": 74,
            "type": "input",
            "format": "float",
            "units": "kWh"
        },
        "_1_to_2_voltage": {
            "register": 200,
            "type": "input",
            "format": "float",
            "units": "Volts"
        },
        "_2_to_3_voltage": {
            "register": 202,
            "type": "input",
            "format": "float",
            "units": "Volts"
        },
        "_3_to_1_voltage": {
            "register": 204,
            "type": "input",
            "format": "float",
            "units": "Volts"
        },
        "neutral_current": {
            "register": 224,
            "type": "input",
            "format": "float",
            "units": "Amps"
        },
        "total_kWh": {
            "register": 342,
            "type": "input",
            "format": "float",
            "units": "kWh"
        },
        "total_kVArh": {
            "register": 344,
            "type": "input",
            "format": "float",
            "units": "kVArh"
        },
        "total_import_active_power": {
            "register": 1280,
            "type": "input",
            "format": "float",
            "units": "W"
        },
        "total_export_active_power": {
            "register": 1282,
            "type": "input",
            "format": "float",
            "units": "W"
        }
    }

    MAPS = {
        "SDM120": SDM120,
        "SDM630": SDM630,
        "SDM72D": SDM72D
    }

    @classmethod
    def get_register_map(cls, device_name):
        return cls.MAPS.get(device_name, {})

    @classmethod
    def get_columns_with_units(cls, register_map):
        columns_with_units = {}
        for parameter, specs in register_map.items():
            columns_with_units[parameter] = specs.get("units", "")
        return columns_with_units

    @classmethod
    def get_columns(cls, device_name):
        """
        Повертає список усіх доступних параметрів для заданого пристрою.
        """
        return list(cls.get_register_map(device_name).keys())
