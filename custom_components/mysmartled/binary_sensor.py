"""Binary sensor for MySmartLed — shows BLE connection status."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MySmartLedCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: MySmartLedCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([MySmartLedConnectionStatus(coordinator, entry)])


class MySmartLedConnectionStatus(
    CoordinatorEntity[MySmartLedCoordinator], BinarySensorEntity
):
    """Binary sensor showing BLE connection status."""

    _attr_has_entity_name = True
    _attr_name = "Connected"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self, coordinator: MySmartLedCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        address = entry.data[CONF_ADDRESS]
        name = entry.data[CONF_NAME]
        self._attr_unique_id = f"{address}_connected"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, address)},
            name=name,
            manufacturer="QJSMARTLED",
            model="YX_LED fiber light",
        )
        self._attr_is_on = coordinator.data.connected

    @property
    def available(self) -> bool:
        return True

    @callback
    def _handle_coordinator_update(self) -> None:
        self._attr_is_on = self.coordinator.data.connected
        super()._handle_coordinator_update()
