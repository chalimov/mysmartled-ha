"""Light platform for My SmartLed (YX_LED BLE) integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.bluetooth import async_ble_device_from_address
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_EFFECT,
    ATTR_RGB_COLOR,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, EFFECT_LIST
from .mysmartled_ble import MySmartLedDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the light platform."""
    address = entry.data[CONF_ADDRESS]
    name = entry.data.get(CONF_NAME, "YX_LED fiber light")

    device = MySmartLedDevice(address, name)
    entity = MySmartLedLight(device, entry)
    async_add_entities([entity])


class MySmartLedLight(LightEntity):
    """Representation of a YX_LED fiber light."""

    _attr_has_entity_name = True
    _attr_supported_color_modes = {ColorMode.RGB}
    _attr_color_mode = ColorMode.RGB
    _attr_supported_features = LightEntityFeature.EFFECT
    _attr_effect_list = EFFECT_LIST

    def __init__(self, device: MySmartLedDevice, entry: ConfigEntry) -> None:
        """Initialize the light."""
        self._device = device
        self._entry = entry
        self._attr_unique_id = device.address.replace(":", "").lower()
        self._attr_name = entry.data.get(CONF_NAME, "YX_LED fiber light")

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._device.address)},
            "name": self._attr_name,
            "manufacturer": "QJSMARTLED",
            "model": "YX_LED fiber light",
        }

    @property
    def is_on(self) -> bool:
        """Return true if light is on."""
        return self._device.state.power

    @property
    def brightness(self) -> int | None:
        """Return the brightness (0-255 for HA)."""
        # Device uses 0-100, HA uses 0-255
        return int(self._device.state.brightness * 255 / 100)

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        """Return the RGB color."""
        s = self._device.state
        if s.white:
            return (255, 255, 255)
        return (s.red, s.green, s.blue)

    @property
    def effect(self) -> str | None:
        """Return the current effect."""
        if self._device.state.mode == 0x06:
            idx = self._device.state.sub_param1
            if 0 <= idx < len(EFFECT_LIST):
                return EFFECT_LIST[idx]
        return None

    def _get_service_info(self):
        """Get bluetooth service info for the device."""
        return async_ble_device_from_address(
            self.hass, self._device.address, connectable=True
        )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the light."""
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        rgb = kwargs.get(ATTR_RGB_COLOR)
        effect = kwargs.get(ATTR_EFFECT)

        # Convert HA brightness (0-255) to device brightness (0-100)
        device_brightness = None
        if brightness is not None:
            device_brightness = max(1, int(brightness * 100 / 255))

        service_info = self._get_service_info()

        await self._device.turn_on(
            service_info=service_info,
            brightness=device_brightness,
            rgb=rgb,
            effect=effect,
        )
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the light."""
        service_info = self._get_service_info()
        await self._device.turn_off(service_info=service_info)
        self.async_write_ha_state()
