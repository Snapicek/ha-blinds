"""Sensor entities for HA Blinds."""

from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity
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
    """Set up sensor entities."""
    from .coordinator import HaBlindsController

    coordinator: HaBlindsController = hass.data[DOMAIN][entry.entry_id]

    entities = [
        HaBlindsStateSensor(coordinator, entry),
        HaBlindsLastReasonSensor(coordinator, entry),
    ]

    async_add_entities(entities)


class HaBlindsBaseSensor(SensorEntity):
    """Base sensor."""

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


class HaBlindsStateSensor(HaBlindsBaseSensor):
    """State sensor."""

    @property
    def unique_id(self) -> str:
        return f"{self.entry.entry_id}_state"

    @property
    def name(self) -> str:
        return "State"

    @property
    def state(self) -> str:
        if self.coordinator._runtime.paused_until:
            return "paused"
        return "active"

    @property
    def icon(self) -> str:
        return "mdi:pause" if self.state == "paused" else "mdi:play"


class HaBlindsLastReasonSensor(HaBlindsBaseSensor):
    """Last reason sensor."""

    @property
    def unique_id(self) -> str:
        return f"{self.entry.entry_id}_reason"

    @property
    def name(self) -> str:
        return "Last Reason"

    @property
    def state(self) -> str:
        return self.coordinator._runtime.last_reason

    @property
    def icon(self) -> str:
        return "mdi:information"



