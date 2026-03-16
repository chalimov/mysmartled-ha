# MySmartLed - Home Assistant Integration

Custom Home Assistant integration for **YX_LED fiber light** BLE LED controllers (used by the "My SmartLed" Android app).

## Features

- Turn on/off
- RGB color control
- Brightness control (0-100%)
- Preset effects (Jump, Crossfade, Blink patterns)
- Auto-discovery via Bluetooth
- Supports multiple devices

## Requirements

- Home Assistant with Bluetooth support (built-in or via ESPHome BLE proxy)
- Linux-based HA installation (Raspberry Pi, NUC, etc.)
- **Note:** Windows Bluetooth is NOT supported for these devices

## Installation

### HACS (recommended)

1. Add this repository as a custom repository in HACS
2. Install "My SmartLed (YX_LED BLE)"
3. Restart Home Assistant

### Manual

1. Copy the `custom_components/mysmartled` folder to your HA `config/custom_components/` directory
2. Restart Home Assistant

## Setup

After installation, the integration will auto-discover YX_LED devices via Bluetooth. You can also add them manually:

1. Go to **Settings > Devices & Services > Add Integration**
2. Search for "My SmartLed"
3. Select your device or enter its BLE address

## Device Info

| Property | Value |
|---|---|
| **BLE Name** | `YX_LED fiber light` |
| **Service UUID** | `0000ffb0-0000-1000-8000-00805f9b34fb` |
| **Android App** | My SmartLed (`com.leguangqi.smartled`) |
| **Manufacturer** | QJSMARTLED |

## Protocol

See [PROTOCOL.md](PROTOCOL.md) for the full reverse-engineered BLE protocol documentation.

## Troubleshooting

- **Device not found:** Ensure your HA host has Bluetooth and the device is powered on
- **Connection fails:** These devices only support one BLE connection at a time. Close the phone app first
- **ESPHome BLE Proxy:** If your HA host doesn't have Bluetooth, use an ESP32 with ESPHome BLE proxy
