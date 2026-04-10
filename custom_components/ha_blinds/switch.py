"""Switch entities for HA Blinds."""

from __future__ import annotations

import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up switch entities."""
    from .coordinator import HaBlindsController

    coordinator: HaBlindsController = hass.data[DOMAIN][entry.entry_id]

    entities = [
        HaBlindsAutomationSwitch(coordinator, entry),
    ]

    async_add_entities(entities)


class HaBlindsBaseSwitch(SwitchEntity):
    """Base switch."""

    def __init__(self, coordinator, entry: ConfigEntry):
        self.coordinator = coordinator
        self.entry = entry

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.entry.entry_id)},
            "name": "HA Blinds",
            "manufacturer": "HA Blinds",
        }

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )


class HaBlindsAutomationSwitch(HaBlindsBaseSwitch):
    """Automation switch."""

    @property
    def unique_id(self) -> str:
        return f"{self.entry.entry_id}_automation"

    @property
    def name(self) -> str:
        return "Automation Enabled"

    @property
    def is_on(self) -> bool:
        return not bool(self.coordinator._runtime.paused_until)

    @property
    def icon(self) -> str:
        return "mdi:play" if self.is_on else "mdi:pause"

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        await self.coordinator.async_resume()

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        await self.coordinator.async_pause()
