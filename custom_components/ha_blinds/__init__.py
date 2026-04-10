"""HA Blinds integration entrypoint."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import (
    ATTR_ENTRY_ID,
    ATTR_MINUTES,
    DOMAIN,
    SERVICE_EVALUATE_NOW,
    SERVICE_PAUSE,
    SERVICE_RESUME,
)
from .coordinator import HaBlindsController

SERVICE_SCHEMA_ENTRY = vol.Schema({vol.Optional(ATTR_ENTRY_ID): cv.string})
SERVICE_SCHEMA_PAUSE = vol.Schema(
    {
        vol.Optional(ATTR_ENTRY_ID): cv.string,
        vol.Optional(ATTR_MINUTES): vol.Coerce(int),
    }
)


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up integration domain."""
    hass.data.setdefault(DOMAIN, {})

    def _iter_targets(call: ServiceCall) -> list[HaBlindsController]:
        controllers = list(hass.data.get(DOMAIN, {}).values())
        entry_id = call.data.get(ATTR_ENTRY_ID)
        if not entry_id:
            return controllers
        target = hass.data.get(DOMAIN, {}).get(entry_id)
        return [target] if target else []

    async def _handle_pause(call: ServiceCall) -> None:
        minutes = call.data.get(ATTR_MINUTES)
        for controller in _iter_targets(call):
            await controller.async_pause(minutes)

    async def _handle_resume(call: ServiceCall) -> None:
        for controller in _iter_targets(call):
            await controller.async_resume()

    async def _handle_evaluate(call: ServiceCall) -> None:
        for controller in _iter_targets(call):
            await controller.async_evaluate_now()

    if not hass.services.has_service(DOMAIN, SERVICE_PAUSE):
        hass.services.async_register(
            DOMAIN,
            SERVICE_PAUSE,
            _handle_pause,
            schema=SERVICE_SCHEMA_PAUSE,
        )
        hass.services.async_register(
            DOMAIN,
            SERVICE_RESUME,
            _handle_resume,
            schema=SERVICE_SCHEMA_ENTRY,
        )
        hass.services.async_register(
            DOMAIN,
            SERVICE_EVALUATE_NOW,
            _handle_evaluate,
            schema=SERVICE_SCHEMA_ENTRY,
        )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up HA Blinds from a config entry."""
    controller = HaBlindsController(hass, entry)
    await controller.async_start()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = controller
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    controller: HaBlindsController | None = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    if controller:
        await controller.async_stop()
    return True


async def _async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
