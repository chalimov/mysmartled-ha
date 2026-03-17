"""Switch entity for MySmartLed — controls BLE connection."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import CONF_ADDRESS, CONF_NAME
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN
from .coordinator import MySmartLedCoordinator


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator: MySmartLedCoordinator = hass.data[DOMAIN][entry.entry_id]
    address = entry.data[CONF_ADDRESS]
    name = entry.data[CONF_NAME]
    async_add_entities([MySmartLedConnectionSwitch(coordinator, address, name)])


class MySmartLedConnectionSwitch(RestoreEntity, SwitchEntity):
    """Switch to enable/disable BLE connection."""

    _attr_has_entity_name = True
    _attr_name = "Connection"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:bluetooth-connect"

    def __init__(
        self,
        coordinator: MySmartLedCoordinator,
        address: str,
        name: str,
    ) -> None:
        self._coordinator = coordinator
        self._attr_unique_id = f"{address}_connect"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, address)},
            name=name,
            manufacturer="QJSMARTLED",
            model="YX_LED fiber light",
        )

    async def async_added_to_hass(self) -> None:
        """Restore previous state on restart."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is not None and last_state.state == "off":
            self._coordinator.enabled = False

    @property
    def is_on(self) -> bool:
        return self._coordinator.enabled

    async def async_turn_on(self, **kwargs) -> None:
        self._coordinator.enabled = True
        self.async_write_ha_state()
        await self._coordinator.async_request_connect()

    async def async_turn_off(self, **kwargs) -> None:
        self._coordinator.enabled = False
        await self._coordinator.async_disconnect()
        self.async_write_ha_state()
