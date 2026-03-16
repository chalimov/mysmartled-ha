"""BLE communication for MySmartLed (YX_LED fiber light) devices."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field

from bleak import BleakClient
from bleak_retry_connector import establish_connection, BleakClientWithServiceCache

from homeassistant.components.bluetooth import BluetoothServiceInfoBleak

from .const import (
    CMD_HEADER,
    HANDLE_WRITE,
    MODE_COLOR,
    MODE_COLOR_MONOCHROME,
    MODE_COLOR_TEMPERATURE,
    POWER_OFF,
    POWER_ON,
    RESERVED_BYTE,
    UUID_NOTIFY,
    UUID_SERVICE,
    UUID_WRITE,
)

_LOGGER = logging.getLogger(__name__)

RETRY_COUNT = 3


@dataclass
class MySmartLedState:
    """Represents the current state of a YX_LED device."""

    power: bool = True
    red: int = 0
    green: int = 0
    blue: int = 0
    white: bool = True  # White flag
    brightness: int = 100  # 0-100
    mode: int = MODE_COLOR
    effect_index: int = 0
    effect_speed: int = 50
    # Retained fields (from real traffic defaults)
    sub_param1: int = 0x13
    sub_param2: int = 0x05
    mode_enable: int = 0x00
    voice_pattern: int = 0xFF
    voice_sensitivity: int = 0x05
    flashing_switch: int = 0xFF
    flashing_speed: int = 0x01
    meteor_switch: int = 0xFF
    meteor_value: int = 0x01
    meteor_speed: int = 0x05
    light_type: int = 0x00


class MySmartLedDevice:
    """Controls a YX_LED fiber light via BLE."""

    def __init__(self, address: str, name: str = "YX_LED") -> None:
        """Initialize the device."""
        self._address = address
        self._name = name
        self._state = MySmartLedState()
        self._client: BleakClient | None = None

    @property
    def address(self) -> str:
        return self._address

    @property
    def name(self) -> str:
        return self._name

    @property
    def state(self) -> MySmartLedState:
        return self._state

    def _build_command(self) -> bytearray:
        """Build the 20-byte command from current state."""
        s = self._state
        return bytearray([
            CMD_HEADER,                             # [0]  Header A5
            POWER_ON if s.power else POWER_OFF,     # [1]  Power
            s.mode & 0xFF,                          # [2]  Mode type
            s.sub_param1 & 0xFF,                    # [3]  Sub-param 1
            s.sub_param2 & 0xFF,                    # [4]  Sub-param 2
            s.red & 0xFF,                           # [5]  Red
            s.green & 0xFF,                         # [6]  Green
            s.blue & 0xFF,                          # [7]  Blue
            0xFF if s.white else 0x00,              # [8]  White flag
            min(s.brightness, 100) & 0xFF,          # [9]  Brightness
            s.mode_enable & 0xFF,                   # [10] Mode enable
            s.voice_pattern & 0xFF,                 # [11] Voice pattern
            s.voice_sensitivity & 0xFF,             # [12] Voice sensitivity
            s.flashing_switch & 0xFF,               # [13] Flashing switch
            s.flashing_speed & 0xFF,                # [14] Flashing speed
            s.meteor_switch & 0xFF,                 # [15] Meteor switch
            s.meteor_value & 0xFF,                  # [16] Meteor value
            s.meteor_speed & 0xFF,                  # [17] Meteor speed
            s.light_type & 0xFF,                    # [18] Light type
            RESERVED_BYTE,                          # [19] Reserved (AA)
        ])

    async def _send_command(self, service_info: BluetoothServiceInfoBleak | None = None) -> bool:
        """Send the current state as a BLE command."""
        cmd = self._build_command()
        _LOGGER.debug(
            "Sending to %s: %s",
            self._address,
            cmd.hex(),
        )

        for attempt in range(1, RETRY_COUNT + 1):
            try:
                if service_info:
                    client = await establish_connection(
                        BleakClientWithServiceCache,
                        service_info.device,
                        self._name,
                        max_attempts=2,
                    )
                else:
                    client = BleakClient(self._address, timeout=15.0)
                    await client.connect()

                try:
                    # Try by UUID first, fall back to handle
                    try:
                        await client.write_gatt_char(
                            UUID_WRITE, bytes(cmd), response=False
                        )
                    except Exception:
                        await client.write_gatt_char(
                            HANDLE_WRITE, bytes(cmd), response=False
                        )
                    _LOGGER.debug("Write OK to %s (attempt %d)", self._address, attempt)
                    return True
                finally:
                    await client.disconnect()

            except Exception as e:
                _LOGGER.warning(
                    "Send attempt %d/%d to %s failed: %s",
                    attempt, RETRY_COUNT, self._address, e,
                )
                if attempt < RETRY_COUNT:
                    await asyncio.sleep(1)

        _LOGGER.error("Failed to send command to %s after %d attempts", self._address, RETRY_COUNT)
        return False

    async def turn_on(
        self,
        service_info: BluetoothServiceInfoBleak | None = None,
        brightness: int | None = None,
        rgb: tuple[int, int, int] | None = None,
        white: bool | None = None,
        effect: str | None = None,
        effect_speed: int | None = None,
    ) -> bool:
        """Turn on the light with optional parameters."""
        self._state.power = True

        if brightness is not None:
            self._state.brightness = max(0, min(100, brightness))

        if rgb is not None:
            r, g, b = rgb
            self._state.mode = MODE_COLOR
            self._state.mode_enable = 0x00
            if r == 255 and g == 255 and b == 255:
                self._state.red = 0
                self._state.green = 0
                self._state.blue = 0
                self._state.white = True
            else:
                self._state.red = r
                self._state.green = g
                self._state.blue = b
                self._state.white = False

        if white is not None:
            self._state.white = white
            if white:
                self._state.mode = MODE_COLOR
                self._state.red = 0
                self._state.green = 0
                self._state.blue = 0

        if effect is not None:
            from .const import EFFECT_LIST
            if effect in EFFECT_LIST:
                idx = EFFECT_LIST.index(effect)
                self._state.mode = 0x06  # Effect mode type
                self._state.sub_param1 = idx & 0xFF  # 0-based index
                self._state.sub_param2 = self._state.effect_speed
                self._state.mode_enable = 0x00

        if effect_speed is not None:
            self._state.effect_speed = max(0, min(255, effect_speed))
            self._state.sub_param2 = self._state.effect_speed

        return await self._send_command(service_info)

    async def turn_off(
        self, service_info: BluetoothServiceInfoBleak | None = None
    ) -> bool:
        """Turn off the light."""
        self._state.power = False
        return await self._send_command(service_info)

    async def set_color(
        self,
        r: int, g: int, b: int,
        brightness: int | None = None,
        service_info: BluetoothServiceInfoBleak | None = None,
    ) -> bool:
        """Set RGB color."""
        return await self.turn_on(
            service_info=service_info,
            rgb=(r, g, b),
            brightness=brightness,
        )

    async def set_brightness(
        self,
        brightness: int,
        service_info: BluetoothServiceInfoBleak | None = None,
    ) -> bool:
        """Set brightness (0-100)."""
        return await self.turn_on(
            service_info=service_info,
            brightness=brightness,
        )

    async def set_effect(
        self,
        effect: str,
        speed: int = 50,
        service_info: BluetoothServiceInfoBleak | None = None,
    ) -> bool:
        """Set an effect by name."""
        return await self.turn_on(
            service_info=service_info,
            effect=effect,
            effect_speed=speed,
        )
