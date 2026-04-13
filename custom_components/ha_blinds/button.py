"""Button entities for HA Blinds."""

from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
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
    """Set up button entities."""
    from .coordinator import HaBlindsController

    coordinator: HaBlindsController = hass.data[DOMAIN][entry.entry_id]

    entities = [
        HaBlindsEvaluateNowButton(coordinator, entry),
    ]

    async_add_entities(entities)


class HaBlindsBaseButton(ButtonEntity):
    """Base button."""

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


class HaBlindsEvaluateNowButton(HaBlindsBaseButton):
    """Evaluate now button."""

    @property
    def unique_id(self) -> str:
        return f"{self.entry.entry_id}_evaluate_now"

    @property
    def name(self) -> str:
        return "Evaluate Now"

    @property
    def icon(self) -> str:
        return "mdi:refresh"

    async def async_press(self) -> None:
        """Press the button."""
        await self.coordinator.async_evaluate_now()

