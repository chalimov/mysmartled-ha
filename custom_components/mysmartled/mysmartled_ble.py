"""BLE communication for MySmartLed (YX_LED fiber light) devices."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from bleak import BleakClient
from bleak.backends.device import BLEDevice

from .const import (
    CMD_HEADER,
    HANDLE_WRITE,
    MODE_COLOR,
    POWER_OFF,
    POWER_ON,
    RESERVED_BYTE,
    UUID_WRITE,
)

_LOGGER = logging.getLogger(__name__)

RETRY_COUNT = 5
CONNECT_TIMEOUT = 15.0

# Global lock — ESP32 BLE proxy can only handle one connection at a time
_ble_lock = asyncio.Lock()


@dataclass
class MySmartLedState:
    """Represents the current state of a YX_LED device."""

    power: bool = True
    red: int = 0
    green: int = 0
    blue: int = 0
    white: bool = True
    brightness: int = 100  # 0-100
    mode: int = MODE_COLOR
    effect_index: int = 0
    effect_speed: int = 50
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
        self._address = address
        self._name = name
        self._state = MySmartLedState()

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
            CMD_HEADER,
            POWER_ON if s.power else POWER_OFF,
            s.mode & 0xFF,
            s.sub_param1 & 0xFF,
            s.sub_param2 & 0xFF,
            s.red & 0xFF,
            s.green & 0xFF,
            s.blue & 0xFF,
            0xFF if s.white else 0x00,
            min(s.brightness, 100) & 0xFF,
            s.mode_enable & 0xFF,
            s.voice_pattern & 0xFF,
            s.voice_sensitivity & 0xFF,
            s.flashing_switch & 0xFF,
            s.flashing_speed & 0xFF,
            s.meteor_switch & 0xFF,
            s.meteor_value & 0xFF,
            s.meteor_speed & 0xFF,
            s.light_type & 0xFF,
            RESERVED_BYTE,
        ])

    async def _write_ble(self, client: BleakClient, cmd: bytes) -> None:
        """Try writing command via UUID, then handle fallback."""
        try:
            await client.write_gatt_char(UUID_WRITE, cmd, response=False)
        except Exception as uuid_err:
            _LOGGER.debug("UUID write failed (%s), trying handle 0x%04X", uuid_err, HANDLE_WRITE)
            await client.write_gatt_char(HANDLE_WRITE, cmd, response=False)

    async def _send_command(self, ble_device: BLEDevice | None = None) -> bool:
        """Send the current state as a BLE command.

        Uses a global lock to serialize BLE connections — the ESP32
        proxy can only handle one connection at a time.
        """
        cmd = bytes(self._build_command())
        _LOGGER.debug("Sending to %s: %s", self._address, cmd.hex())

        async with _ble_lock:
            for attempt in range(1, RETRY_COUNT + 1):
                try:
                    target = ble_device if ble_device else self._address
                    client = BleakClient(target, timeout=CONNECT_TIMEOUT)
                    await client.connect()
                    try:
                        await self._write_ble(client, cmd)
                        _LOGGER.debug("Write OK to %s (attempt %d)", self._address, attempt)
                        return True
                    finally:
                        try:
                            await client.disconnect()
                        except Exception:
                            pass

                except Exception as e:
                    _LOGGER.warning(
                        "Send attempt %d/%d to %s failed: %s",
                        attempt, RETRY_COUNT, self._address, e,
                    )
                    if attempt < RETRY_COUNT:
                        await asyncio.sleep(3)

        _LOGGER.error("Failed to send command to %s after %d attempts", self._address, RETRY_COUNT)
        return False

    async def turn_on(
        self,
        ble_device: BLEDevice | None = None,
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
                self._state.mode = 0x06
                self._state.sub_param1 = idx & 0xFF
                self._state.sub_param2 = self._state.effect_speed
                self._state.mode_enable = 0x00

        if effect_speed is not None:
            self._state.effect_speed = max(0, min(255, effect_speed))
            self._state.sub_param2 = self._state.effect_speed

        return await self._send_command(ble_device)

    async def turn_off(
        self, ble_device: BLEDevice | None = None
    ) -> bool:
        """Turn off the light."""
        self._state.power = False
        return await self._send_command(ble_device)

    async def set_color(
        self,
        r: int, g: int, b: int,
        brightness: int | None = None,
        ble_device: BLEDevice | None = None,
    ) -> bool:
        return await self.turn_on(ble_device=ble_device, rgb=(r, g, b), brightness=brightness)

    async def set_brightness(
        self,
        brightness: int,
        ble_device: BLEDevice | None = None,
    ) -> bool:
        return await self.turn_on(ble_device=ble_device, brightness=brightness)

    async def set_effect(
        self,
        effect: str,
        speed: int = 50,
        ble_device: BLEDevice | None = None,
    ) -> bool:
        return await self.turn_on(ble_device=ble_device, effect=effect, effect_speed=speed)
