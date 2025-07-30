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
        "total_reactive_energy": {"register": 344, "type": "input", "format": "float", "units": "kVArh"},
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

    SDM72 = {
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

    IME96HDLe = {
        "line_voltage_1": {
            "register": 4096,
            "type": "holding",
            "format": "UD_WORD",
            "units": "Volts",
            "divider": 1000
        },
        "line_voltage_2": {
            "register": 4098,
            "type": "holding",
            "format": "UD_WORD",
            "units": "Volts",
            "divider": 1000
        },
        "line_voltage_3": {
            "register": 4100,
            "type": "holding",
            "format": "UD_WORD",
            "units": "Volts",
            "divider": 1000
        },
        "current_1": {
            "register": 4102,
            "type": "holding",
            "format": "UD_WORD",
            "units": "Amps",
            "divider": 1000
        },
        "current_2": {
            "register": 4104,
            "type": "holding",
            "format": "UD_WORD",
            "units": "Amps",
            "divider": 1000
        },
        "current_3": {
            "register": 4106,
            "type": "holding",
            "format": "UD_WORD",
            "units": "Amps",
            "divider": 1000
        },
        "neutral_current": {
            "register": 4108,  # 0x100c
            "type": "input",
            "format": "UD_WORD",
            "units": "Amps",
            "divider": 1000.0
        },
        "_1_to_2_voltage": {
            "register": 4110,  # 0x100e
            "type": "input",
            "format": "UD_WORD",
            "units": "Volts",
            "divider": 1000.0
        },
        "_2_to_3_voltage": {
            "register": 4112,  # 0x1010
            "type": "input",
            "format": "UD_WORD",
            "units": "Volts",
            "divider": 1000.0
        },
        "_3_to_1_voltage": {
            "register": 4114,  # 0x1012
            "type": "input",
            "format": "UD_WORD",
            "units": "Volts",
            "divider": 1000.0
        },
        "total_active_power": {
            "register": 4116,  # 0x1014
            "type": "input",
            "format": "UD_WORD",
            "units": "Watts",
            "divider": 1.0
        },
        "total_reactive_power": {
            "register": 4118,  # 0x1016
            "type": "input",
            "format": "UD_WORD",
            "units": "VAr",
            "divider": 1.0
        },
        "total_apparent_power": {
            "register": 4120,  # 0x1018
            "type": "input",
            "format": "UD_WORD",
            "units": "VA",
            "divider": 1.0
        },
        "total_phase_sign_of_active_power": {
            "register": 4122,  # 0x101a
            "type": "input",
            "format": "U_WORD",
            "units": "",
            "divider": 1.0
        },
        "total_sign_of_reactive_power": {
            "register": 4123,  # 0x101b
            "type": "input",
            "format": "U_WORD",
            "units": "",
            "divider": 1.0
        },
        "total_positive_active_energy": {
            "register": 4124,  # 0x101c
            "type": "input",
            "format": "UD_WORD",
            "units": "kWh",
            "divider": 100.0
        },
        "total_positive_reactive_energy": {
            "register": 4126,  # 0x101e
            "type": "input",
            "format": "UD_WORD",
            "units": "kVArh",
            "divider": 100.0
        },
        "total_negative_active_energy": {
            "register": 4128,  # 0x1020
            "type": "input",
            "format": "UD_WORD",
            "units": "kWh",
            "divider": 100.0
        },
        "total_negative_reactive_energy": {
            "register": 4130,  # 0x1022
            "type": "input",
            "format": "UD_WORD",
            "units": "kVArh",
            "divider": 100.0
        },
        "total_power_factor": {
            "register": 4132,  # 0x1024
            "type": "input",
            "format": "S_WORD",
            "units": "",
            "divider": 100.0
        },
        "total_sector_of_power_factor": {
            "register": 4133,  # 0x1025
            "type": "input",
            "format": "U_WORD",
            "units": "",
            "divider": 1.0
        },
        "frequency": {
            "register": 4134,  # 0x1026
            "type": "input",
            "format": "U_WORD",
            "units": "Hz",
            "divider": 10.0
        },
        "total_average_power": {
            "register": 4135,  # 0x1027
            "type": "input",
            "format": "U_WORD",
            "units": "Watts",
            "divider": 1.0
        },
        "total_peak_maximum_demand": {
            "register": 4136,  # 0x1028
            "type": "input",
            "format": "UD_WORD",
            "units": "Watts",
            "divider": 1.0
        },
        "time_counter_for_average_power": {
            "register": 4138,  # 0x102a
            "type": "input",
            "format": "UD_WORD",
            "units": "minutes",
            "divider": 1.0
        },
        "phase_1_active_power": {
            "register": 4140,  # 0x102c
            "type": "input",
            "format": "UD_WORD",
            "units": "Watts",
            "divider": 1.0
        },
        "phase_2_active_power": {
            "register": 4142,  # 0x102e
            "type": "input",
            "format": "UD_WORD",
            "units": "Watts",
            "divider": 1.0
        },
        "phase_3_active_power": {
            "register": 4144,  # 0x1030
            "type": "input",
            "format": "UD_WORD",
            "units": "Watts",
            "divider": 1.0
        },
        "phase_1_sign_of_active_power": {
            "register": 4146,  # 0x1032
            "type": "input",
            "format": "U_WORD",
            "units": "",
            "divider": 1.0
        },
        "phase_2_sign_of_active_power": {
            "register": 4147,  # 0x1033
            "type": "input",
            "format": "U_WORD",
            "units": "",
            "divider": 1.0
        },
        "phase_3_sign_of_active_power": {
            "register": 4148,  # 0x1034
            "type": "input",
            "format": "U_WORD",
            "units": "",
            "divider": 1.0
        },
        "phase_1_reactive_power": {
            "register": 4149,  # 0x1035
            "type": "input",
            "format": "UD_WORD",
            "units": "VAr",
            "divider": 1.0
        },
        "phase_2_reactive_power": {
            "register": 4151,  # 0x1037
            "type": "input",
            "format": "UD_WORD",
            "units": "VAr",  # (3)
            "divider": 1.0
        },
        "phase_3_reactive_power": {
            "register": 4153,  # 0x1039
            "type": "input",
            "format": "UD_WORD",
            "units": "VAr",  # (3)
            "divider": 1.0
        },
        "phase_1_sign_of_reactive_power": {
            "register": 4155,  # 0x103b
            "type": "input",
            "format": "U_WORD",  # (6)
            "units": "",
            "divider": 1.0
        },
        "phase_2_sign_of_reactive_power": {
            "register": 4156,  # 0x103c
            "type": "input",
            "format": "U_WORD",  # (6)
            "units": "",
            "divider": 1.0
        },
        "phase_3_sign_of_reactive_power": {
            "register": 4157,  # 0x103d
            "type": "input",
            "format": "U_WORD",  # (6)
            "units": "",
            "divider": 1.0
        },
        "power_1": {
            "register": 4158,  # 0x103e
            "type": "input",
            "format": "UD_WORD",
            "units": "VA",  # (3)
            "divider": 1.0
        },
        "power_2": {
            "register": 4160,  # 0x1040
            "type": "input",
            "format": "UD_WORD",
            "units": "VA",  # (3)
            "divider": 1.0
        },
        "power_3": {
            "register": 4162,  # 0x1042
            "type": "input",
            "format": "UD_WORD",
            "units": "VA",  # (3)
            "divider": 1.0
        },
        "power_factor_1": {
            "register": 4164,  # 0x1044
            "type": "input",
            "format": "S_WORD",
            "units": "",  # 1/100 signed
            "divider": 100.0
        },
        "power_factor_2": {
            "register": 4165,  # 0x1045
            "type": "input",
            "format": "S_WORD",
            "units": "",  # 1/100 signed
            "divider": 100.0
        },
        "power_factor_3": {
            "register": 4166,  # 0x1046
            "type": "input",
            "format": "S_WORD",
            "units": "",  # 1/100 signed
            "divider": 100.0
        },
        "phase_1_power_factor_sector": {
            "register": 4167,  # 0x1047
            "type": "input",
            "format": "U_WORD",
            "units": "",  # 0:PF=1, 1:ind, 2:cap
            "divider": 1.0
        },
        "phase_2_power_factor_sector": {
            "register": 4168,  # 0x1048
            "type": "input",
            "format": "U_WORD",
            "units": "",  # 0:PF=1, 1:ind, 2:cap
            "divider": 1.0
        },
        "phase_3_power_factor_sector": {
            "register": 4169,  # 0x1049
            "type": "input",
            "format": "U_WORD",
            "units": "",  # 0:PF=1, 1:ind, 2:cap
            "divider": 1.0
        },
        "phase_1_THD_V1": {
            "register": 4170,  # 0x104a
            "type": "input",
            "format": "U_WORD",
            "units": "%",  # 1/10 %
            "divider": 10.0
        },
        "phase_2_THD_V2": {
            "register": 4171,  # 0x104b
            "type": "input",
            "format": "U_WORD",
            "units": "%",  # 1/10 %
            "divider": 10.0
        },
        "phase_3_THD_V3": {
            "register": 4172,  # 0x104c
            "type": "input",
            "format": "U_WORD",
            "units": "%",  # 1/10 %
            "divider": 10.0
        },
        "phase_1_THD_I1": {
            "register": 4173,  # 0x104d
            "type": "input",
            "format": "U_WORD",
            "units": "%",  # 1/10 %
            "divider": 10.0
        },
        "phase_2_THD_I2": {
            "register": 4174,  # 0x104e
            "type": "input",
            "format": "U_WORD",
            "units": "%",  # 1/10 %
            "divider": 10.0
        },
        "phase_3_THD_I3": {
            "register": 4175,  # 0x104f
            "type": "input",
            "format": "U_WORD",
            "units": "%",  # 1/10 %
            "divider": 10.0
        },
        "phase_1_I1_average": {
            "register": 4176,  # 0x1050
            "type": "input",
            "format": "UD_WORD",
            "units": "Amps",
            "divider": 1000.0  # mA -> A
        },
        "phase_2_I2_average": {
            "register": 4178,  # 0x1052
            "type": "input",
            "format": "UD_WORD",
            "units": "Amps",
            "divider": 1000.0
        },
        "phase_3_I3_average": {
            "register": 4180,  # 0x1054
            "type": "input",
            "format": "UD_WORD",
            "units": "Amps",
            "divider": 1000.0
        },
        "phase_1_I1_peak_maximum": {
            "register": 4182,  # 0x1056
            "type": "input",
            "format": "UD_WORD",
            "units": "Amps",
            "divider": 1000.0
        },
        "phase_2_I2_peak_maximum": {
            "register": 4184,  # 0x1058
            "type": "input",
            "format": "UD_WORD",
            "units": "Amps",
            "divider": 1000.0
        },
        "phase_3_I3_peak_maximum": {
            "register": 4186,  # 0x105a
            "type": "input",
            "format": "UD_WORD",
            "units": "Amps",
            "divider": 1000.0
        },
        "I1_I2_I3_average": {
            "register": 4188,  # 0x105c
            "type": "input",
            "format": "UD_WORD",
            "units": "Amps",
            "divider": 1000.0
        },
        "phase_1_V1_min": {
            "register": 4190,  # 0x105e
            "type": "input",
            "format": "UD_WORD",
            "units": "Volts",
            "divider": 1000.0  # mV -> V
        },
        "phase_2_V2_min": {
            "register": 4192,  # 0x1060
            "type": "input",
            "format": "UD_WORD",
            "units": "Volts",
            "divider": 1000.0
        },
        "phase_3_V3_min": {
            "register": 4194,  # 0x1062
            "type": "input",
            "format": "UD_WORD",
            "units": "Volts",
            "divider": 1000.0
        },
        "phase_1_V1_max": {
            "register": 4196,  # 0x1064
            "type": "input",
            "format": "UD_WORD",
            "units": "Volts",
            "divider": 1000.0
        },
        "phase_2_V2_max": {
            "register": 4198,  # 0x1066
            "type": "input",
            "format": "UD_WORD",
            "units": "Volts",
            "divider": 1000.0
        },
        "phase_3_V3_max": {
            "register": 4200,  # 0x1068
            "type": "input",
            "format": "UD_WORD",
            "units": "Volts",
            "divider": 1000.0
        },
        "total_active_partial_energy": {
            "register": 4202,  # 0x106a
            "type": "input",
            "format": "UD_WORD",
            "units": "kWh",  # (4)
            "divider": 100.0
        },
        "total_reactive_partial_energy": {
            "register": 4204,  # 0x106c
            "type": "input",
            "format": "UD_WORD",
            "units": "kVArh",  # (4)
            "divider": 100.0
        },
        "total_active_average_power": {
            "register": 4208,  # 0x1070
            "type": "input",
            "format": "UD_WORD",
            "units": "Watts",  # (3)
            "divider": 1.0
        },
        "total_reactive_average_power": {
            "register": 4210,  # 0x1072
            "type": "input",
            "format": "UD_WORD",
            "units": "VAr",  # (3)
            "divider": 1.0
        },
        "total_apparent_average_power": {
            "register": 4212,  # 0x1074
            "type": "input",
            "format": "UD_WORD",
            "units": "VA",  # (3)
            "divider": 1.0
        }
    }

    MAPS = {
        "SDM120": SDM120,
        "SDM630": SDM630,
        "SDM72": SDM72,
        "IME96HDLe": IME96HDLe,
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
        return list(cls.get_register_map(device_name).keys())