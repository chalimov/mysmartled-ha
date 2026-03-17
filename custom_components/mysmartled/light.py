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
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, EFFECT_LIST, MODE_COLOR, MODE_EFFECT
from .coordinator import MySmartLedCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: MySmartLedCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([MySmartLedLight(coordinator, entry)])


class MySmartLedLight(
    CoordinatorEntity[MySmartLedCoordinator], RestoreEntity, LightEntity
):
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

    async def async_added_to_hass(self) -> None:
        """Restore full device state from last known values."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is None:
            return

        attrs = last_state.attributes
        s = self.coordinator.data

        # Restore power
        s.power = last_state.state == "on"

        # Restore LED state
        s.brightness = attrs.get("device_brightness", s.brightness)
        s.red = attrs.get("device_red", s.red)
        s.green = attrs.get("device_green", s.green)
        s.blue = attrs.get("device_blue", s.blue)
        s.white = attrs.get("device_white", s.white)
        s.mode = attrs.get("device_mode", s.mode)
        s.effect_speed = attrs.get("device_effect_speed", s.effect_speed)
        s.sub_param1 = attrs.get("device_sub_param1", s.sub_param1)
        s.sub_param2 = attrs.get("device_sub_param2", s.sub_param2)
        s.mode_enable = attrs.get("device_mode_enable", s.mode_enable)

        # Restore machine layer
        s.flashing_switch = attrs.get("device_flashing_switch", s.flashing_switch)
        s.flashing_speed = attrs.get("device_flashing_speed", s.flashing_speed)
        s.meteor_switch = attrs.get("device_meteor_switch", s.meteor_switch)
        s.meteor_value = attrs.get("device_meteor_value", s.meteor_value)
        s.meteor_speed = attrs.get("device_meteor_speed", s.meteor_speed)

        self.coordinator.async_set_updated_data(s)

    @property
    def available(self) -> bool:
        return self.coordinator.enabled

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
        if self.coordinator.data.mode == MODE_EFFECT:
            idx = self.coordinator.data.sub_param1
            if 0 <= idx < len(EFFECT_LIST):
                return EFFECT_LIST[idx]
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Persist full device state for restore after reboot."""
        s = self.coordinator.data
        return {
            "device_brightness": s.brightness,
            "device_red": s.red,
            "device_green": s.green,
            "device_blue": s.blue,
            "device_white": s.white,
            "device_mode": s.mode,
            "device_effect_speed": s.effect_speed,
            "device_sub_param1": s.sub_param1,
            "device_sub_param2": s.sub_param2,
            "device_mode_enable": s.mode_enable,
            "device_flashing_switch": s.flashing_switch,
            "device_flashing_speed": s.flashing_speed,
            "device_meteor_switch": s.meteor_switch,
            "device_meteor_value": s.meteor_value,
            "device_meteor_speed": s.meteor_speed,
        }

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
