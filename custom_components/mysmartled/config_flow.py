"""Config flow for My SmartLed integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_ADDRESS, CONF_NAME

from .const import DEVICE_NAME_PREFIX, DOMAIN

_LOGGER = logging.getLogger(__name__)


class MySmartLedConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for My SmartLed."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovered_devices: dict[str, BluetoothServiceInfoBleak] = {}

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> ConfigFlowResult:
        """Handle the bluetooth discovery step."""
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        self._discovered_devices[discovery_info.address] = discovery_info
        name = discovery_info.name or discovery_info.address
        self.context["title_placeholders"] = {"name": name}

        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm bluetooth discovery."""
        if user_input is not None:
            return self.async_create_entry(
                title=user_input.get(CONF_NAME, "YX_LED"),
                data={
                    CONF_ADDRESS: self.unique_id,
                    CONF_NAME: user_input.get(CONF_NAME, "YX_LED"),
                },
            )

        return self.async_show_form(
            step_id="bluetooth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_NAME, default="YX_LED fiber light"
                    ): str,
                }
            ),
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the user step — manual setup or pick from discovered."""
        errors = {}

        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(address)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=user_input.get(CONF_NAME, address),
                data=user_input,
            )

        # Try to find devices via HA bluetooth
        discovered = async_discovered_service_info(self.hass, connectable=True)
        for info in discovered:
            name = info.name or ""
            if name.startswith(DEVICE_NAME_PREFIX):
                self._discovered_devices[info.address] = info

        if self._discovered_devices:
            addresses = {
                addr: f"{info.name} ({addr})"
                for addr, info in self._discovered_devices.items()
            }
            schema = vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): vol.In(addresses),
                    vol.Optional(CONF_NAME, default="YX_LED fiber light"): str,
                }
            )
        else:
            schema = vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): str,
                    vol.Optional(CONF_NAME, default="YX_LED fiber light"): str,
                }
            )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )
