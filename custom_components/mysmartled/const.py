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
BLE_ON = 0xFF
BLE_OFF = 0x00

# Modes
MODE_COLOR = 0x01
MODE_COLOR_TEMPERATURE = 0x02
MODE_COLOR_MONOCHROME = 0x03
MODE_EFFECT = 0x06

# LED effect presets — 20 modes from the app (mode_type=0x06, 0-based index)
# Extracted from APK string resources in DateCenter.initFromCache
EFFECT_LIST = [
    "Seven Color Fade",       # 0
    "RGB Fade",               # 1
    "Seven Color Breathe",    # 2
    "RGB Breathe",            # 3
    "Red & Green Fade",       # 4
    "Red & Blue Fade",        # 5
    "Green & Blue Fade",      # 6
    "Seven Color Jump",       # 7
    "RGB Jump",               # 8
    "Seven Color Flash",      # 9
    "RGB Flash",              # 10
    "Red Flash",              # 11
    "Green Flash",            # 12
    "Blue Flash",             # 13
    "Yellow Flash",           # 14
    "Purple Flash",           # 15
    "Cyan Flash",             # 16
    "White Flash",            # 17
    "Yellow & Purple Flash",  # 18
    "Purple & Cyan Flash",    # 19
]

# Twinkle (machine-layer flashing) constants
TWINKLE_SPEED_MIN = 1
TWINKLE_SPEED_MAX = 255

# Meteor (machine-layer chase) constants
METEOR_SPEED_MIN = 1
METEOR_SPEED_MAX = 255
METEOR_PATTERNS = ["Pattern 1", "Pattern 2", "Pattern 3"]
