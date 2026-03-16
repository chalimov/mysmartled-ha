"""Coordinator for MySmartLed BLE integration — manages persistent connection."""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import timedelta

from bleak import BleakClient, BleakError

from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

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

RECONNECT_INTERVAL = timedelta(seconds=30)
CONNECT_TIMEOUT = 15


@dataclass
class MySmartLedState:
    """Current device state."""

    connected: bool = False
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


class MySmartLedCoordinator(DataUpdateCoordinator[MySmartLedState]):
    """Manages BLE connection and command sending for a YX_LED device."""

    def __init__(self, hass: HomeAssistant, address: str, name: str) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"MySmartLed {name}",
            update_interval=RECONNECT_INTERVAL,
        )
        self.address = address
        self.device_name = name
        self.data = MySmartLedState()
        self._client: BleakClient | None = None
        self._connecting = False
        self.enabled = True
        self._setup_complete = False
        self._write_lock = asyncio.Lock()

    async def _async_update_data(self) -> MySmartLedState:
        """Periodic reconnection if disconnected and enabled."""
        if (
            self._setup_complete
            and self.enabled
            and not self._client
            and not self._connecting
        ):
            await self._connect()
        return self.data

    @callback
    def handle_bluetooth_event(
        self,
        service_info: bluetooth.BluetoothServiceInfoBleak,
        change: bluetooth.BluetoothChange,
    ) -> None:
        """Handle BLE advertisement — trigger connection if needed."""
        if (
            self._setup_complete
            and self.enabled
            and not self._client
            and not self._connecting
        ):
            self.hass.async_create_task(self._connect())

    async def _connect(self) -> None:
        """Connect to the YX_LED device."""
        if self._connecting:
            return
        self._connecting = True
        try:
            device = bluetooth.async_ble_device_from_address(
                self.hass, self.address, connectable=True
            )
            if not device:
                _LOGGER.debug("Device %s not available", self.address)
                return

            _LOGGER.info("Connecting to %s (%s)", self.device_name, self.address)
            client = BleakClient(
                device,
                disconnected_callback=self._on_disconnect,
                timeout=CONNECT_TIMEOUT,
            )
            await client.connect()

            if not self.enabled or not client.is_connected:
                if client.is_connected:
                    await client.disconnect()
                return

            self._client = client
            self.data.connected = True
            _LOGGER.info("Connected to %s (%s)", self.device_name, self.address)
            self.async_set_updated_data(self.data)

        except Exception as err:
            _LOGGER.debug("Failed to connect to %s: %s", self.address, err)
        finally:
            self._connecting = False

    @callback
    def _on_disconnect(self, client: BleakClient) -> None:
        """Handle unexpected BLE disconnect."""
        _LOGGER.info("Disconnected from %s (%s)", self.device_name, self.address)
        self._client = None
        self.data.connected = False
        self.async_set_updated_data(self.data)

    async def async_disconnect(self) -> None:
        """Disconnect (called on switch-off or unload)."""
        client = self._client
        self._client = None
        if client:
            try:
                await client.disconnect()
            except BleakError:
                pass
        self.data.connected = False
        self.async_set_updated_data(self.data)

    async def async_request_connect(self) -> None:
        """Public: trigger a connection attempt."""
        if not self._client and not self._connecting:
            await self._connect()

    def _build_command(self) -> bytes:
        """Build the 20-byte command from current state."""
        s = self.data
        return bytes([
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

    async def async_send_command(self) -> bool:
        """Send the current state to the device over persistent connection."""
        cmd = self._build_command()
        _LOGGER.debug("Sending to %s: %s", self.address, cmd.hex())

        async with self._write_lock:
            client = self._client
            if not client or not client.is_connected:
                _LOGGER.warning("Not connected to %s, attempting reconnect", self.address)
                await self._connect()
                client = self._client
                if not client or not client.is_connected:
                    _LOGGER.error("Cannot send to %s: not connected", self.address)
                    return False

            for attempt in range(1, 4):
                try:
                    try:
                        await client.write_gatt_char(UUID_WRITE, cmd, response=False)
                    except Exception:
                        await client.write_gatt_char(HANDLE_WRITE, cmd, response=False)
                    _LOGGER.debug("Write OK to %s", self.address)
                    return True
                except Exception as e:
                    _LOGGER.warning(
                        "Write attempt %d/3 to %s failed: %s", attempt, self.address, e
                    )
                    if attempt < 3:
                        await asyncio.sleep(1)

        _LOGGER.error("Failed to write to %s", self.address)
        return False

    async def async_turn_on(
        self,
        brightness: int | None = None,
        rgb: tuple[int, int, int] | None = None,
        effect: str | None = None,
    ) -> bool:
        """Turn on with optional params."""
        self.data.power = True

        if brightness is not None:
            self.data.brightness = max(0, min(100, brightness))

        if rgb is not None:
            r, g, b = rgb
            self.data.mode = MODE_COLOR
            self.data.mode_enable = 0x00
            if r == 255 and g == 255 and b == 255:
                self.data.red = self.data.green = self.data.blue = 0
                self.data.white = True
            else:
                self.data.red, self.data.green, self.data.blue = r, g, b
                self.data.white = False

        if effect is not None:
            from .const import EFFECT_LIST
            if effect in EFFECT_LIST:
                idx = EFFECT_LIST.index(effect)
                self.data.mode = 0x06
                self.data.sub_param1 = idx & 0xFF
                self.data.sub_param2 = self.data.effect_speed
                self.data.mode_enable = 0x00

        result = await self.async_send_command()
        self.async_set_updated_data(self.data)
        return result

    async def async_turn_off(self) -> bool:
        """Turn off the light."""
        self.data.power = False
        result = await self.async_send_command()
        self.async_set_updated_data(self.data)
        return result
