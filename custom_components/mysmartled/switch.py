"""Switch entities for MySmartLed — connection, twinkle, and meteor controls."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import BLE_ON, DOMAIN
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
        MySmartLedConnectionSwitch(coordinator, address, name),
        MySmartLedTwinkleSwitch(coordinator, address, name),
        MySmartLedMeteorSwitch(coordinator, address, name),
    ])


# ── Connection switch (controls BLE enabled/disabled) ────────────


class MySmartLedConnectionSwitch(RestoreEntity, SwitchEntity):
    """Switch to enable/disable BLE connection."""

    _attr_has_entity_name = True
    _attr_name = "Connection"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:bluetooth-connect"

    def __init__(self, coordinator: MySmartLedCoordinator, address: str, name: str) -> None:
        self._coordinator = coordinator
        self._attr_unique_id = f"{address}_connect"
        self._attr_device_info = _device_info(address, name)

    async def async_added_to_hass(self) -> None:
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


# ── Twinkle switch (machine-layer flashing, byte [13]) ───────────


class MySmartLedTwinkleSwitch(
    CoordinatorEntity[MySmartLedCoordinator], SwitchEntity
):
    """Switch to enable/disable twinkle (fiber flashing) effect."""

    _attr_has_entity_name = True
    _attr_name = "Twinkle"
    _attr_icon = "mdi:shimmer"

    def __init__(self, coordinator: MySmartLedCoordinator, address: str, name: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{address}_twinkle"
        self._attr_device_info = _device_info(address, name)

    @property
    def available(self) -> bool:
        return self.coordinator.enabled

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.flashing_switch == BLE_ON

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_set_twinkle(on=True)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_set_twinkle(on=False)


# ── Meteor switch (machine-layer chase, byte [15]) ───────────────


class MySmartLedMeteorSwitch(
    CoordinatorEntity[MySmartLedCoordinator], SwitchEntity
):
    """Switch to enable/disable meteor (chase) effect."""

    _attr_has_entity_name = True
    _attr_name = "Meteor"
    _attr_icon = "mdi:star-shooting"

    def __init__(self, coordinator: MySmartLedCoordinator, address: str, name: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{address}_meteor"
        self._attr_device_info = _device_info(address, name)

    @property
    def available(self) -> bool:
        return self.coordinator.enabled

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.meteor_switch == BLE_ON

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_set_meteor(on=True)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_set_meteor(on=False)
