"""Select entity for MySmartLed — meteor pattern selection."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, METEOR_PATTERNS
from .coordinator import MySmartLedCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: MySmartLedCoordinator = hass.data[DOMAIN][entry.entry_id]
    address = entry.data[CONF_ADDRESS]
    name = entry.data[CONF_NAME]
    async_add_entities([MySmartLedMeteorPattern(coordinator, address, name)])


class MySmartLedMeteorPattern(
    CoordinatorEntity[MySmartLedCoordinator], SelectEntity
):
    """Meteor pattern selector — byte [16]."""

    _attr_has_entity_name = True
    _attr_name = "Meteor Pattern"
    _attr_icon = "mdi:star-shooting"
    _attr_options = METEOR_PATTERNS

    def __init__(self, coordinator: MySmartLedCoordinator, address: str, name: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{address}_meteor_pattern"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, address)},
            name=name,
            manufacturer="QJSMARTLED",
            model="YX_LED fiber light",
        )

    @property
    def available(self) -> bool:
        return self.coordinator.enabled

    @property
    def current_option(self) -> str | None:
        val = self.coordinator.data.meteor_value
        if 1 <= val <= len(METEOR_PATTERNS):
            return METEOR_PATTERNS[val - 1]
        return METEOR_PATTERNS[0]

    async def async_select_option(self, option: str) -> None:
        if option in METEOR_PATTERNS:
            pattern_num = METEOR_PATTERNS.index(option) + 1
            await self.coordinator.async_set_meteor(pattern=pattern_num)
