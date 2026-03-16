"""Light platform for My SmartLed (YX_LED BLE) integration."""
from __future__ import annotations

from typing import Any

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
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, EFFECT_LIST
from .coordinator import MySmartLedCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: MySmartLedCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([MySmartLedLight(coordinator, entry)])


class MySmartLedLight(CoordinatorEntity[MySmartLedCoordinator], LightEntity):
    """Representation of a YX_LED fiber light."""

    _attr_has_entity_name = True
    _attr_name = None  # Use device name
    _attr_supported_color_modes = {ColorMode.RGB}
    _attr_color_mode = ColorMode.RGB
    _attr_supported_features = LightEntityFeature.EFFECT
    _attr_effect_list = EFFECT_LIST

    def __init__(self, coordinator: MySmartLedCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        address = entry.data[CONF_ADDRESS]
        name = entry.data[CONF_NAME]
        self._attr_unique_id = f"{address}_light"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, address)},
            name=name,
            manufacturer="QJSMARTLED",
            model="YX_LED fiber light",
        )

    @property
    def available(self) -> bool:
        return self.coordinator.data.connected

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.power

    @property
    def brightness(self) -> int | None:
        return int(self.coordinator.data.brightness * 255 / 100)

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        s = self.coordinator.data
        if s.white:
            return (255, 255, 255)
        return (s.red, s.green, s.blue)

    @property
    def effect(self) -> str | None:
        if self.coordinator.data.mode == 0x06:
            idx = self.coordinator.data.sub_param1
            if 0 <= idx < len(EFFECT_LIST):
                return EFFECT_LIST[idx]
        return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        rgb = kwargs.get(ATTR_RGB_COLOR)
        effect = kwargs.get(ATTR_EFFECT)

        device_brightness = None
        if brightness is not None:
            device_brightness = max(1, int(brightness * 100 / 255))

        await self.coordinator.async_turn_on(
            brightness=device_brightness,
            rgb=rgb,
            effect=effect,
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_turn_off()
