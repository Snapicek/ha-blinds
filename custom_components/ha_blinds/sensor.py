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
        HaBlindsTargetPositionSensor(coordinator, entry),
        HaBlindsLastDecisionSensor(coordinator, entry),
        HaBlindsErrorCountSensor(coordinator, entry),
        HaBlindsSunAtWindowSensor(coordinator, entry),
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


class HaBlindsTargetPositionSensor(HaBlindsBaseSensor):
    """Target position sensor."""

    @property
    def unique_id(self) -> str:
        return f"{self.entry.entry_id}_target_position"

    @property
    def name(self) -> str:
        return "Target Position"

    @property
    def state(self) -> int | None:
        return self.coordinator._runtime.last_target

    @property
    def icon(self) -> str:
        return "mdi:arrow-up-down"

    @property
    def unit_of_measurement(self) -> str:
        return "%"


class HaBlindsLastDecisionSensor(HaBlindsBaseSensor):
    """Last decision sensor."""

    @property
    def unique_id(self) -> str:
        return f"{self.entry.entry_id}_last_decision"

    @property
    def name(self) -> str:
        return "Last Decision"

    @property
    def state(self) -> str | None:
        if self.coordinator._runtime.last_decision_time:
            return self.coordinator._runtime.last_decision_time.isoformat()
        return None

    @property
    def icon(self) -> str:
        return "mdi:check-circle"


class HaBlindsErrorCountSensor(HaBlindsBaseSensor):
    """Error count sensor."""

    @property
    def unique_id(self) -> str:
        return f"{self.entry.entry_id}_error_count"

    @property
    def name(self) -> str:
        return "Error Count"

    @property
    def state(self) -> int:
        return self.coordinator._runtime.error_count

    @property
    def icon(self) -> str:
        return "mdi:alert-circle"

    @property
    def unit_of_measurement(self) -> str:
        return "errors"


class HaBlindsSunAtWindowSensor(HaBlindsBaseSensor):
    """Sun at window sensor."""

    @property
    def unique_id(self) -> str:
        return f"{self.entry.entry_id}_sun_at_window"

    @property
    def name(self) -> str:
        return "Sun at Window"

    @property
    def state(self) -> bool:
        return self.coordinator._runtime.sun_at_window

    @property
    def icon(self) -> str:
        return "mdi:sunglasses"
