"""Number entities for MySmartLed — twinkle speed and meteor speed."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    METEOR_SPEED_MAX,
    METEOR_SPEED_MIN,
    TWINKLE_SPEED_MAX,
    TWINKLE_SPEED_MIN,
)
from .coordinator import MySmartLedCoordinator


def _device_info(address: str, name: str) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, address)},
        name=name,
        manufacturer="QJSMARTLED",
        model="YX_LED fiber light",
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: MySmartLedCoordinator = hass.data[DOMAIN][entry.entry_id]
    address = entry.data[CONF_ADDRESS]
    name = entry.data[CONF_NAME]
    async_add_entities([
        MySmartLedTwinkleSpeed(coordinator, address, name),
        MySmartLedMeteorSpeed(coordinator, address, name),
    ])


class MySmartLedTwinkleSpeed(
    CoordinatorEntity[MySmartLedCoordinator], NumberEntity
):
    """Twinkle (flashing) speed control — byte [14]."""

    _attr_has_entity_name = True
    _attr_name = "Twinkle Speed"
    _attr_icon = "mdi:speedometer"
    _attr_native_min_value = TWINKLE_SPEED_MIN
    _attr_native_max_value = TWINKLE_SPEED_MAX
    _attr_native_step = 1
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator: MySmartLedCoordinator, address: str, name: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{address}_twinkle_speed"
        self._attr_device_info = _device_info(address, name)

    @property
    def available(self) -> bool:
        return self.coordinator.enabled

    @property
    def native_value(self) -> float:
        return float(self.coordinator.data.flashing_speed)

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_twinkle(speed=int(value))


class MySmartLedMeteorSpeed(
    CoordinatorEntity[MySmartLedCoordinator], NumberEntity
):
    """Meteor speed control — byte [17]."""

    _attr_has_entity_name = True
    _attr_name = "Meteor Speed"
    _attr_icon = "mdi:speedometer"
    _attr_native_min_value = METEOR_SPEED_MIN
    _attr_native_max_value = METEOR_SPEED_MAX
    _attr_native_step = 1
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator: MySmartLedCoordinator, address: str, name: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{address}_meteor_speed"
        self._attr_device_info = _device_info(address, name)

    @property
    def available(self) -> bool:
        return self.coordinator.enabled

    @property
    def native_value(self) -> float:
        return float(self.coordinator.data.meteor_speed)

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_meteor(speed=int(value))
