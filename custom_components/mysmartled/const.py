"""Constants for the My SmartLed (YX_LED) integration."""

DOMAIN = "mysmartled"

# BLE UUIDs (from APK reverse engineering)
UUID_SERVICE = "0000ffb0-0000-1000-8000-00805f9b34fb"
UUID_WRITE = "0000ffb1-0000-1000-8000-00805f9b34fb"
UUID_NOTIFY = "0000ffb2-0000-1000-8000-00805f9b34fb"

# Advertised service UUID (different from data service)
UUID_ADVERTISED = "0000fff0-0000-1000-8000-00805f9b34fb"

# GATT handles (confirmed via HCI snoop)
HANDLE_WRITE = 0x000D
HANDLE_NOTIFY_CCCD = 0x0010

# Device identification
DEVICE_NAME_PREFIX = "YX_LED"
MANUFACTURER_ID = 0x0A21  # 2593

# Protocol constants
CMD_HEADER = 0xA5
POWER_ON = 0xFF
POWER_OFF = 0x00
RESERVED_BYTE = 0xAA  # Verified from real traffic

# Modes
MODE_COLOR = 0x01
MODE_COLOR_TEMPERATURE = 0x02
MODE_COLOR_MONOCHROME = 0x03

# Effect presets (mode_type, name)
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
]
