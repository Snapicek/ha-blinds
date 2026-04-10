"""Config flow for HA Blinds."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.selector import EntitySelector, EntitySelectorConfig, NumberSelector, NumberSelectorConfig, NumberSelectorMode

from .const import (
    CONF_COVER_ENTITY,
    CONF_DEBOUNCE_MINUTES,
    CONF_HEAT_END_HOUR,
    CONF_HEAT_POSITION,
    CONF_HEAT_START_HOUR,
    CONF_LUX_CLOSE_SUMMER,
    CONF_LUX_CLOSE_WINTER,
    CONF_LUX_OPEN_SUMMER,
    CONF_LUX_OPEN_WINTER,
    CONF_LUX_SENSOR,
    CONF_MANUAL_OVERRIDE_MINUTES,
    CONF_MAX_STEP_PER_TICK,
    CONF_SUMMER_PRIVACY_HOUR,
    CONF_TEMP_SENSOR,
    CONF_TEMP_THRESHOLD,
    CONF_TICK_MINUTES,
    CONF_WINDOW_AZIMUTH,
    CONF_WINDOW_VIEW_LEFT,
    CONF_WINDOW_VIEW_RIGHT,
    CONF_WINTER_PRIVACY_HOUR,
    DEFAULTS,
    DOMAIN,
)


def _entry_schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(
                CONF_COVER_ENTITY,
                default=defaults.get(CONF_COVER_ENTITY),
            ): EntitySelector(EntitySelectorConfig(domain="cover")),
            vol.Required(
                CONF_LUX_SENSOR,
                default=defaults.get(CONF_LUX_SENSOR),
            ): EntitySelector(EntitySelectorConfig(domain="sensor")),
            vol.Optional(
                CONF_TEMP_SENSOR,
                default=defaults.get(CONF_TEMP_SENSOR),
            ): EntitySelector(EntitySelectorConfig(domain="sensor")),
            vol.Required(
                CONF_WINDOW_AZIMUTH,
                default=defaults.get(CONF_WINDOW_AZIMUTH, DEFAULTS[CONF_WINDOW_AZIMUTH]),
            ): NumberSelector(NumberSelectorConfig(min=0, max=359, mode=NumberSelectorMode.BOX, step=1)),
            vol.Required(
                CONF_WINDOW_VIEW_LEFT,
                default=defaults.get(CONF_WINDOW_VIEW_LEFT, DEFAULTS[CONF_WINDOW_VIEW_LEFT]),
            ): NumberSelector(NumberSelectorConfig(min=0, max=180, mode=NumberSelectorMode.BOX, step=1)),
            vol.Required(
                CONF_WINDOW_VIEW_RIGHT,
                default=defaults.get(CONF_WINDOW_VIEW_RIGHT, DEFAULTS[CONF_WINDOW_VIEW_RIGHT]),
            ): NumberSelector(NumberSelectorConfig(min=0, max=180, mode=NumberSelectorMode.BOX, step=1)),
        }
    )


def _options_schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_LUX_CLOSE_SUMMER, default=defaults.get(CONF_LUX_CLOSE_SUMMER, DEFAULTS[CONF_LUX_CLOSE_SUMMER])): NumberSelector(NumberSelectorConfig(min=1000, max=120000, step=500, mode=NumberSelectorMode.BOX)),
            vol.Required(CONF_LUX_OPEN_SUMMER, default=defaults.get(CONF_LUX_OPEN_SUMMER, DEFAULTS[CONF_LUX_OPEN_SUMMER])): NumberSelector(NumberSelectorConfig(min=500, max=120000, step=500, mode=NumberSelectorMode.BOX)),
            vol.Required(CONF_LUX_CLOSE_WINTER, default=defaults.get(CONF_LUX_CLOSE_WINTER, DEFAULTS[CONF_LUX_CLOSE_WINTER])): NumberSelector(NumberSelectorConfig(min=500, max=120000, step=500, mode=NumberSelectorMode.BOX)),
            vol.Required(CONF_LUX_OPEN_WINTER, default=defaults.get(CONF_LUX_OPEN_WINTER, DEFAULTS[CONF_LUX_OPEN_WINTER])): NumberSelector(NumberSelectorConfig(min=500, max=120000, step=500, mode=NumberSelectorMode.BOX)),
            vol.Required(CONF_DEBOUNCE_MINUTES, default=defaults.get(CONF_DEBOUNCE_MINUTES, DEFAULTS[CONF_DEBOUNCE_MINUTES])): NumberSelector(NumberSelectorConfig(min=1, max=30, step=1, mode=NumberSelectorMode.BOX)),
            vol.Required(CONF_TICK_MINUTES, default=defaults.get(CONF_TICK_MINUTES, DEFAULTS[CONF_TICK_MINUTES])): NumberSelector(NumberSelectorConfig(min=1, max=30, step=1, mode=NumberSelectorMode.BOX)),
            vol.Required(CONF_MAX_STEP_PER_TICK, default=defaults.get(CONF_MAX_STEP_PER_TICK, DEFAULTS[CONF_MAX_STEP_PER_TICK])): NumberSelector(NumberSelectorConfig(min=1, max=50, step=1, mode=NumberSelectorMode.BOX)),
            vol.Required(CONF_HEAT_START_HOUR, default=defaults.get(CONF_HEAT_START_HOUR, DEFAULTS[CONF_HEAT_START_HOUR])): NumberSelector(NumberSelectorConfig(min=0, max=23, step=1, mode=NumberSelectorMode.BOX)),
            vol.Required(CONF_HEAT_END_HOUR, default=defaults.get(CONF_HEAT_END_HOUR, DEFAULTS[CONF_HEAT_END_HOUR])): NumberSelector(NumberSelectorConfig(min=0, max=23, step=1, mode=NumberSelectorMode.BOX)),
            vol.Required(CONF_HEAT_POSITION, default=defaults.get(CONF_HEAT_POSITION, DEFAULTS[CONF_HEAT_POSITION])): NumberSelector(NumberSelectorConfig(min=0, max=100, step=1, mode=NumberSelectorMode.BOX)),
            vol.Required(CONF_TEMP_THRESHOLD, default=defaults.get(CONF_TEMP_THRESHOLD, DEFAULTS[CONF_TEMP_THRESHOLD])): NumberSelector(NumberSelectorConfig(min=10, max=40, step=0.5, mode=NumberSelectorMode.BOX)),
            vol.Required(CONF_WINTER_PRIVACY_HOUR, default=defaults.get(CONF_WINTER_PRIVACY_HOUR, DEFAULTS[CONF_WINTER_PRIVACY_HOUR])): NumberSelector(NumberSelectorConfig(min=0, max=23, step=1, mode=NumberSelectorMode.BOX)),
            vol.Required(CONF_SUMMER_PRIVACY_HOUR, default=defaults.get(CONF_SUMMER_PRIVACY_HOUR, DEFAULTS[CONF_SUMMER_PRIVACY_HOUR])): NumberSelector(NumberSelectorConfig(min=0, max=23, step=1, mode=NumberSelectorMode.BOX)),
            vol.Required(CONF_MANUAL_OVERRIDE_MINUTES, default=defaults.get(CONF_MANUAL_OVERRIDE_MINUTES, DEFAULTS[CONF_MANUAL_OVERRIDE_MINUTES])): NumberSelector(NumberSelectorConfig(min=5, max=240, step=5, mode=NumberSelectorMode.BOX)),
        }
    )


class HaBlindsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HA Blinds."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_COVER_ENTITY])
            self._abort_if_unique_id_configured()
            self.context["user_data"] = user_input
            return await self.async_step_options()

        return self.async_show_form(step_id="user", data_schema=_entry_schema({}), errors=errors)

    async def async_step_options(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            data = dict(self.context.get("user_data", {}))
            return self.async_create_entry(
                title=f"HA Blinds ({data[CONF_COVER_ENTITY]})",
                data=data,
                options=user_input,
            )

        return self.async_show_form(step_id="options", data_schema=_options_schema(DEFAULTS))

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return HaBlindsOptionsFlow(config_entry)


class HaBlindsOptionsFlow(config_entries.OptionsFlow):
    """Options flow for HA Blinds."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        defaults = {**DEFAULTS, **self.config_entry.options}
        return self.async_show_form(step_id="init", data_schema=_options_schema(defaults))

