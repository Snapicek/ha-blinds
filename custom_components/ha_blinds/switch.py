"""Switch platform for HA Blinds – provides an Enable/Disable toggle under the device."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_ENABLED

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
        HABlindsEnabledSwitch(hass, entry),
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
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.entry.entry_id)},
            name="HA Blinds",
            manufacturer="HA Blinds",
        )

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
        return "Automation Active"

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


class HABlindsEnabledSwitch(SwitchEntity):
    """Switch that enables or disables the blind automation for this entry."""

    _attr_has_entity_name = True
    _attr_name = "Automation Enabled"
    _attr_icon = "mdi:motion-play-outline"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self._hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_enabled"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info so this switch appears under the blind's device."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
        )

    @property
    def is_on(self) -> bool:
        """Return True when automation is enabled."""
        return self._entry.options.get(CONF_ENABLED, True)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable the automation."""
        await self._set_enabled(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable the automation."""
        await self._set_enabled(False)

    async def _set_enabled(self, value: bool) -> None:
        new_options = {**self._entry.options, CONF_ENABLED: value}
        self._hass.config_entries.async_update_entry(self._entry, options=new_options)
        self.async_write_ha_state()
        _LOGGER.debug("HA Blinds [%s] automation enabled: %s", self._entry.title, value)
