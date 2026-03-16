# MySmartLed (YX_LED) BLE Protocol Documentation

Reverse-engineered from the Android app **My SmartLed** v1.4.6
Package: `com.leguangqi.smartled` (Developer: QJSMARTLED)
Internal codebase namespace: `cn.imengduo.lanya`

---

## BLE Connection Details

| Parameter | Value |
|---|---|
| **Device Name** | `YX_LED fiber light` (scan filter: `YX_LED*`) |
| **Service UUID** | `0000ffb0-0000-1000-8000-00805f9b34fb` |
| **Write Characteristic** | `0000ffb1-0000-1000-8000-00805f9b34fb` |
| **Read Service UUID** | `0000ffb0-0000-1000-8000-00805f9b34fb` (same) |
| **Read/Notify Characteristic** | `0000ffb2-0000-1000-8000-00805f9b34fb` |
| **Advertised Service UUID** | `0000fff0-0000-1000-8000-00805f9b34fb` (in advertisements) |
| **BLE Library** | FastBLE (`com.clj.fastble`) |
| **Write Mode** | Write without response (ATT opcode `0x52`) |
| **GATT Handle (write)** | `0x000D` (confirmed via HCI snoop) |
| **GATT Handle (notify enable)** | `0x0010` (CCCD write `01 00`) |
| **Manufacturer ID** | `0x0A21` (2593) — data contains last 4 bytes of MAC |
| **Address Type** | Random (non-resolvable private) |

### Notes on Connectivity
- **Windows BLE**: Cannot connect (GATT service discovery fails with "Unreachable"). These devices are incompatible with the Windows BLE stack.
- **Android/iOS**: Works via FastBLE library
- **Linux (BlueZ)**: Expected to work — Home Assistant's bleak library handles these devices on Linux

---

## Command Frame Format

Every command is a **20-byte frame** (represented as a 40-character hex string, converted to raw bytes before writing to the BLE characteristic).

### Default Template

```
A5 FF 01 00 05 00 00 00 FF 64 00 00 05 FF 01 FF 01 01 00 00
```

### Byte Map

| Byte Index | Hex Char Index | Field | Description | Valid Range |
|---|---|---|---|---|
| 0 | [0:2] | Header | Always `A5` | `A5` |
| 1 | [2:4] | Power | `FF` = ON, `00` = OFF | `00`, `FF` |
| 2 | [4:6] | Mode Type | Selects the operating mode | See Mode Table |
| 3 | [6:8] | Sub-param 1 | Mode index (0-based in protocol, 1-based in UI) | `00`-`FF` |
| 4 | [8:10] | Sub-param 2 | Speed / sensitivity depending on mode | `00`-`FF` |
| 5 | [10:12] | Red / Cool | Red channel or cool white intensity | `00`-`FF` |
| 6 | [12:14] | Green / Warm | Green channel or warm white intensity | `00`-`FF` |
| 7 | [14:16] | Blue | Blue channel (or zero in non-RGB modes) | `00`-`FF` |
| 8 | [16:18] | White Flag | `FF` = white/monochrome mode, `00` = color mode | `00`, `FF` |
| 9 | [18:20] | Brightness | Brightness level (decimal 0-100) | `00`-`64` |
| 10 | [20:22] | Mode Enable | `FF` = voice/mic mode active, `00` = inactive | `00`, `FF` |
| 11 | [22:24] | Voice Pattern | Voice-reactive pattern number (0-indexed) | `00`-`FF` |
| 12 | [24:26] | Voice Sensitivity | Sound sensitivity for voice mode | `00`-`FF` |
| 13 | [26:28] | Flashing Switch | `FF` = flashing ON, `00` = OFF | `00`, `FF` |
| 14 | [28:30] | Flashing Speed | Flashing animation speed | `00`-`FF` |
| 15 | [30:32] | Meteor Switch | `FF` = meteor ON, `00` = OFF | `00`, `FF` |
| 16 | [32:34] | Meteor Pattern | Meteor animation pattern/direction | `00`-`FF` |
| 17 | [34:36] | Meteor Speed | Meteor animation speed | `00`-`FF` |
| 18 | [36:38] | Light Type | Hardware type selector (0-4) | `00`-`04` |
| 19 | [38:40] | Reserved | Normally `00`, `AA` in last-success template | `00`, `AA` |

---

## Operating Modes

### Mode Enum (from `DateCenter$Companion$Mode`)

| Enum Name | Ordinal | Switch Case | Description |
|---|---|---|---|
| `MODE_COLOR` | 0 | 1 | RGB color with brightness |
| `MODE_COLOR_TEMPERATURE` | 1 | 2 | Cool/warm white temperature |
| `MODE_COLOR_MONOCHROME` | 2 | 3 | Grayscale/white brightness only |
| `MODE_MODE` | 3 | 4 | Preset animation patterns |
| `MODE_MUSIC` | 4 | 6 | Music-reactive (from audio) |
| `MODE_MICROPHONE` | 5 | 7 | Microphone-reactive |
| `MODE_VOICE` | 6 | 5 | Voice-reactive patterns |
| `MODE_FLASHING` | 7 | 8 | Flashing/strobe effects |
| `MODE_METEOR` | 8 | 9 | Meteor/chase effects |

---

## Command Building by Mode

The app uses `generateCmd()` which starts from the current command state (base template) and patches specific byte positions based on the active mode. The full 20-byte command is always sent as a complete state update.

### Power ON/OFF

Modify byte 1 only:
```
Byte[1] = 0xFF  -> Power ON
Byte[1] = 0x00  -> Power OFF
```

Example (power ON, rest at defaults):
```
A5 FF 01 00 05 00 00 00 FF 64 00 00 05 FF 01 FF 01 01 00 00
```

Example (power OFF):
```
A5 00 01 00 05 00 00 00 FF 64 00 00 05 FF 01 FF 01 01 00 00
```

### MODE_COLOR (Case 1) — RGB Color

Sets a specific RGB color with brightness.

| Byte | Value | Notes |
|---|---|---|
| [2] | `01` | Mode type = COLOR |
| [5] | `RR` | Red (0-255) |
| [6] | `GG` | Green (0-255) |
| [7] | `BB` | Blue (0-255) |
| [8] | `00` | White flag OFF (color mode) |
| [9] | `00`-`64` | Brightness (0-100) |
| [10] | `00` | Mode enable = OFF |

**Special case: White color** (`FFFFFF`):
- Byte[8] = `FF` (white flag ON)
- Bytes[5:8] = `00 00 00` (RGB cleared)

Example (red at 80% brightness):
```
A5 FF 01 00 05 FF 00 00 00 50 00 00 05 FF 01 FF 01 01 00 00
```

Example (white at 100% brightness):
```
A5 FF 01 00 05 00 00 00 FF 64 00 00 05 FF 01 FF 01 01 00 00
```

### MODE_COLOR_TEMPERATURE (Case 2) — Cool/Warm White

Controls cool and warm white LEDs independently.

| Byte | Value | Notes |
|---|---|---|
| [2] | `02` | Mode type = COLOR_TEMPERATURE |
| [5] | `CC` | Cool white: `int(coolPercent / 100.0 * 255)` |
| [6] | `WW` | Warm white: `int(warmPercent / 100.0 * 255)` |
| [7] | `00` | Zeroed |
| [8] | `00` | Zeroed |
| [10] | `00` | Mode enable = OFF |

Example (50% cool, 50% warm):
```
A5 FF 02 00 05 80 80 00 00 64 00 00 05 FF 01 FF 01 01 00 00
```

### MODE_COLOR_MONOCHROME (Case 3) — Grayscale

Single white channel with adjustable brightness.

| Byte | Value | Notes |
|---|---|---|
| [2] | `03` | Mode type = MONOCHROME |
| [5] | `FF` | Fixed to 0xFF |
| [6] | `00` | Fixed to 0x00 |
| [7] | `00` | Fixed to 0x00 |
| [8] | `00` | Fixed to 0x00 |
| [9] | `VV` | Grayscale value (0-255 encoded as 0x00-0xFF) |
| [10] | `00` | Mode enable = OFF |

Example (grayscale at 50%):
```
A5 FF 03 00 05 FF 00 00 00 32 00 00 05 FF 01 FF 01 01 00 00
```

### MODE_MODE (Case 4) — Preset Animations

Plays built-in animation patterns.

| Byte | Value | Notes |
|---|---|---|
| [2] | `TT` | Mode type value (from mode list, e.g., `06`) |
| [3] | `II` | Pattern index: `(modeIndex - 1) & 0xFF` (0-based) |
| [4] | `SS` | Animation speed (0-255) |
| [10] | `00` | Mode enable = OFF |

Example (mode type 0x06, pattern 3, speed 50):
```
A5 FF 06 02 32 00 00 00 FF 64 00 00 05 FF 01 FF 01 01 00 00
```

### MODE_VOICE (Case 5) — Voice-Reactive

Sound-reactive lighting patterns.

| Byte | Value | Notes |
|---|---|---|
| [2] | `TT` | Voice type: `format("%02x", voiceType & 0xFF)` |
| [4] | `SS` | Speed (0-255) |
| [10] | `FF` | Mode enable = ON (voice active) |
| [11] | `VV` | Voice pattern: `(voiceIndex - 1) & 0xFF` |
| [12] | `NN` | Sensitivity (0-255) |

Example (voice type 0x04, pattern 2, speed 30, sensitivity 80):
```
A5 FF 04 00 1E 00 00 00 FF 64 FF 01 50 FF 01 FF 01 01 00 00
```

### MODE_MUSIC (Case 6) / MODE_MICROPHONE (Case 7) — Audio-Reactive

Both modes use the same protocol. Color and brightness are dynamically updated based on audio amplitude.

| Byte | Value | Notes |
|---|---|---|
| [2] | `01` | Mode type = COLOR (same as color mode) |
| [5] | `RR` | Red from music analysis |
| [6] | `GG` | Green from music analysis |
| [7] | `BB` | Blue from music analysis |
| [8] | `00`/`FF` | White flag (if color is white) |
| [9] | `LL` | Brightness from music amplitude |
| [10] | `00` | Mode enable = OFF |

These modes continuously send updated commands as the audio input changes.

### MODE_FLASHING (Case 8) — Strobe Effects

Controls the flashing/strobe overlay independently of other settings.

| Byte | Value | Notes |
|---|---|---|
| [13] | `FF`/`00` | Flashing switch: `FF`=ON, `00`=OFF |
| [14] | `SS` | Flashing speed (0-255) |

Example (flashing ON, speed 128):
```
A5 FF 01 00 05 FF 00 00 00 64 00 00 05 FF 80 FF 01 01 00 00
                                          ^^ ^^
                                          ON Speed
```

### MODE_METEOR (Case 9) — Chase Effects

Controls meteor/chase animation overlay.

| Byte | Value | Notes |
|---|---|---|
| [15] | `FF`/`00` | Meteor switch: `FF`=ON, `00`=OFF |
| [16] | `PP` | Meteor pattern/direction (0-255) |
| [17] | `SS` | Meteor speed (0-255) |

Example (meteor ON, pattern 2, speed 64):
```
A5 FF 01 00 05 FF 00 00 00 64 00 00 05 FF 01 FF 02 40 00 00
                                                  ^^ ^^ ^^
                                                  ON Pat Speed
```

---

## Light Type (Byte 18)

Selects the hardware variant/wiring configuration:

| Value | Meaning |
|---|---|
| `0x00` | Type 0 (default) |
| `0x01` | Type 1 |
| `0x02` | Type 2 |
| `0x03` | Type 3 |
| `0x04` | Type 4 |

This is set from a radio button group in the app's main activity.

---

## Data Flow in the App

1. UI fragment updates a `DateCenter` LiveData value (e.g., `currentColor`, `modeValue`, `flashingSwitch`)
2. `LightApplication.onCreate` has observers on all 18+ LiveData fields
3. Each observer calls `DeviceHelper.Companion.notifyCmdChangeAndSend()`
4. `notifyCmdChangeAndSend()` calls `generateCmd()` which builds the full 20-byte command by patching relevant byte positions in the base template
5. The hex string command is emitted into `DateCenter.commandFlow` (`MutableSharedFlow`)
6. For each connected BLE device, `handleDeviceCommands` collects from the flow and calls `sendMessageWithRetry(bleDevice, cmd, retries=3)`
7. `sendMessage()` converts the hex string to bytes via `HexUtil.hexStringToBytes()` and writes to `0000ffb1` characteristic

---

## Hardcoded Templates

```
Default (currentCmd):    A5 FF 01 00 05 00 00 00 FF 64 00 00 05 FF 01 FF 01 01 00 00
Last success template:   A5 FF 01 00 05 00 00 00 FF 64 00 01 05 FF 01 FF 01 01 00 AA
```

---

## Common Command Examples

### Turn ON with white at full brightness
```
A5 FF 01 00 05 00 00 00 FF 64 00 00 05 FF 01 FF 01 01 00 00
```

### Turn OFF
```
A5 00 01 00 05 00 00 00 FF 64 00 00 05 FF 01 FF 01 01 00 00
```

### Set solid red at 100% brightness
```
A5 FF 01 00 05 FF 00 00 00 64 00 00 05 FF 01 FF 01 01 00 00
```

### Set solid blue at 50% brightness
```
A5 FF 01 00 05 00 00 FF 00 32 00 00 05 FF 01 FF 01 01 00 00
```

### Set solid green at 75% brightness
```
A5 FF 01 00 05 00 FF 00 00 4B 00 00 05 FF 01 FF 01 01 00 00
```

### Set color temperature (80% cool, 20% warm)
```
A5 FF 02 00 05 CC 33 00 00 64 00 00 05 FF 01 FF 01 01 00 00
```

### Preset animation (type 0x06, pattern 1, speed 50)
```
A5 FF 06 00 32 00 00 00 FF 64 00 00 05 FF 01 FF 01 01 00 00
```

### Enable flashing (speed 100)
```
A5 FF 01 00 05 FF 00 00 00 64 00 00 05 FF 64 FF 01 01 00 00
```

### Enable meteor (pattern 1, speed 80)
```
A5 FF 01 00 05 FF 00 00 00 64 00 00 05 FF 01 FF 01 50 00 00
```

---

## HCI Snoop Log Verification

The protocol was verified by capturing live BLE traffic from the Android app via HCI snoop log.

### Captured Traffic Summary
- **45 ATT Write Commands** captured (opcode `0x52`)
- All writes to **GATT handle `0x000D`** (the `0000ffb1` write characteristic)
- All commands **20 bytes**, prefix `A5`
- Each command sent **twice** (once per connected device)
- Notification enable: ATT Write Request to handle `0x0010` with value `01 00`

### Real Traffic vs Default Template

The real traffic uses the "lastSuccessSendCmd" template, not the default:

| Byte | Default | Real Traffic | Notes |
|---|---|---|---|
| [3] | `00` | `13` | Sub-param 1 retains previous mode value |
| [11] | `00` | `FF` | Voice pattern field retained |
| [17] | `01` | `05` | Meteor speed field retained |
| [19] | `00` | `AA` | Reserved byte = `AA` in active state |

### Example Captured Commands (color changes)

```
a5ff011305 868cff 00 64 00ff05ff01ff010500aa  # R=134 G=140 B=255 (lavender)
a5ff011305 ff0000 00 64 00ff05ff01ff010500aa  # R=255 G=0   B=0   (red)
a5ff011305 00ff00 00 64 00ff05ff01ff010500aa  # R=0   G=255 B=0   (green)
a5ff011305 ffe76d 00 64 00ff05ff01ff010500aa  # R=255 G=231 B=109 (warm yellow)
```

## Notes

- The entire 20-byte state is sent with every command (no incremental updates)
- The app uses ATT Write Command (`0x52`, write-without-response) for low latency
- Connection uses 3 retries on failure
- Device scanning filters by local name prefix `YX_LED`
- The app caches the last successful command and restores state on reconnect
- Brightness is 0-100 (decimal), not 0-255
- Color values are standard 0-255 per channel
- Mode indices are 1-based in the UI but transmitted as 0-based (subtract 1)
- Byte[19] should be `0xAA` (not `0x00`) in production commands
- Bytes [3], [11], [17] retain their values from previous mode changes — they are not reset per-command
