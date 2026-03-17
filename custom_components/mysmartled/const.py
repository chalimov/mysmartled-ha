"""Constants for the My SmartLed (YX_LED) integration."""

DOMAIN = "mysmartled"

# BLE UUIDs
UUID_SERVICE = "0000ffb0-0000-1000-8000-00805f9b34fb"
UUID_WRITE = "0000ffb1-0000-1000-8000-00805f9b34fb"
UUID_NOTIFY = "0000ffb2-0000-1000-8000-00805f9b34fb"

# GATT handles (confirmed via HCI snoop)
HANDLE_WRITE = 0x000D

# Device identification
DEVICE_NAME_PREFIX = "YX_LED"

# Protocol constants
CMD_HEADER = 0xA5
POWER_ON = 0xFF
POWER_OFF = 0x00
RESERVED_BYTE = 0xAA

# Modes
MODE_COLOR = 0x01
MODE_COLOR_TEMPERATURE = 0x02
MODE_COLOR_MONOCHROME = 0x03
MODE_EFFECT = 0x06

# Effect presets (indices into the mode_type=0x06 pattern list)
EFFECT_LIST = [
    "Jump RGB",
    "Jump RGBYCMW",
    "Crossfade RGB",
    "Crossfade RGBYCMW",
    "Crossfade Red",
    "Crossfade Green",
    "Crossfade Blue",
    "Crossfade Yellow",
    "Crossfade Cyan",
    "Crossfade Magenta",
    "Crossfade White",
    "Blink RGB",
    "Blink Red",
    "Blink Green",
    "Blink Blue",
    "Blink Yellow",
    "Blink Cyan",
    "Blink Magenta",
    "Blink White",
    # Strobe overlay effects
    "Strobe Slow",
    "Strobe Medium",
    "Strobe Fast",
    # Meteor overlay effects
    "Meteor 1",
    "Meteor 2",
    "Meteor 3",
    "Meteor Slow",
    "Meteor Fast",
]
