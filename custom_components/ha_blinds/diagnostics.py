"""Diagnostics support for HA Blinds."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_COVER_ENTITY, CONF_LUX_SENSOR, CONF_TEMP_SENSOR


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    from .coordinator import HaBlindsController

    coordinator: HaBlindsController | None = hass.data.get(DOMAIN, {}).get(entry.entry_id)

    diagnostics = {
        "entry_id": entry.entry_id,
        "config_data": {k: str(v)[:50] for k, v in entry.data.items()},  # Redact sensitive info
        "options": {k: str(v)[:50] for k, v in entry.options.items()},
    }

    if coordinator:
        diagnostics["controller_status"] = coordinator.get_status_dict()

        # Get sensor states for debugging
        cover_entity = coordinator._cfg(CONF_COVER_ENTITY)
        lux_entity = coordinator._cfg(CONF_LUX_SENSOR)
        temp_entity = coordinator._cfg(CONF_TEMP_SENSOR)

        diagnostics["entity_states"] = {
            "cover": str(hass.states.get(cover_entity)),
            "lux_sensor": str(hass.states.get(lux_entity)),
            "temp_sensor": str(hass.states.get(temp_entity)) if temp_entity else None,
            "sun": str(hass.states.get("sun.sun")),
        }

    return diagnostics

