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

# Effect presets — 20 modes from the app (mode_type=0x06, 1-based index)
# Extracted from APK string resources in DateCenter.initFromCache
EFFECT_LIST = [
    "Seven Color Fade",       # 1
    "RGB Fade",               # 2
    "Seven Color Breathe",    # 3
    "RGB Breathe",            # 4
    "Red & Green Fade",       # 5
    "Red & Blue Fade",        # 6
    "Green & Blue Fade",      # 7
    "Seven Color Jump",       # 8
    "RGB Jump",               # 9
    "Seven Color Flash",      # 10
    "RGB Flash",              # 11
    "Red Flash",              # 12
    "Green Flash",            # 13
    "Blue Flash",             # 14
    "Yellow Flash",           # 15
    "Purple Flash",           # 16
    "Cyan Flash",             # 17
    "White Flash",            # 18
    "Yellow & Purple Flash",  # 19
    "Purple & Cyan Flash",    # 20
    # Strobe overlay (uses flashing_switch byte, not mode byte)
    "Strobe Slow",
    "Strobe Medium",
    "Strobe Fast",
    # Meteor overlay (uses meteor_switch byte, not mode byte)
    "Meteor 1",
    "Meteor 2",
    "Meteor 3",
    "Meteor Slow",
    "Meteor Fast",
]

# Number of real mode effects (not overlays)
MODE_EFFECT_COUNT = 20
