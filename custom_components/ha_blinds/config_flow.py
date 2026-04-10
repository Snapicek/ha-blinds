"""Config flow for HA Blinds."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector as sel

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
    schema = {
        vol.Required(CONF_COVER_ENTITY): sel.EntitySelector(
            sel.EntitySelectorConfig(domain="cover")
        ),
        vol.Required(CONF_LUX_SENSOR): sel.EntitySelector(
            sel.EntitySelectorConfig(domain="sensor")
        ),
        vol.Optional(CONF_TEMP_SENSOR): sel.EntitySelector(
            sel.EntitySelectorConfig(domain="sensor")
        ),
        vol.Required(
            CONF_WINDOW_AZIMUTH,
            default=int(defaults.get(CONF_WINDOW_AZIMUTH, DEFAULTS[CONF_WINDOW_AZIMUTH])),
        ): vol.All(vol.Coerce(int), vol.Range(min=0, max=359)),
        vol.Required(
            CONF_WINDOW_VIEW_LEFT,
            default=int(defaults.get(CONF_WINDOW_VIEW_LEFT, DEFAULTS[CONF_WINDOW_VIEW_LEFT])),
        ): vol.All(vol.Coerce(int), vol.Range(min=0, max=180)),
        vol.Required(
            CONF_WINDOW_VIEW_RIGHT,
            default=int(defaults.get(CONF_WINDOW_VIEW_RIGHT, DEFAULTS[CONF_WINDOW_VIEW_RIGHT])),
        ): vol.All(vol.Coerce(int), vol.Range(min=0, max=180)),
    }

    if CONF_COVER_ENTITY in defaults:
        schema[vol.Required(CONF_COVER_ENTITY, default=defaults[CONF_COVER_ENTITY])] = schema.pop(vol.Required(CONF_COVER_ENTITY))
    if CONF_LUX_SENSOR in defaults:
        schema[vol.Required(CONF_LUX_SENSOR, default=defaults[CONF_LUX_SENSOR])] = schema.pop(vol.Required(CONF_LUX_SENSOR))
    if CONF_TEMP_SENSOR in defaults:
        schema[vol.Optional(CONF_TEMP_SENSOR, description={"suggested_value": defaults[CONF_TEMP_SENSOR]})] = schema.pop(vol.Optional(CONF_TEMP_SENSOR))

    return vol.Schema(schema)


def _options_schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_LUX_CLOSE_SUMMER, default=int(defaults.get(CONF_LUX_CLOSE_SUMMER, DEFAULTS[CONF_LUX_CLOSE_SUMMER]))): vol.All(vol.Coerce(int), vol.Range(min=1000, max=120000)),
            vol.Required(CONF_LUX_OPEN_SUMMER, default=int(defaults.get(CONF_LUX_OPEN_SUMMER, DEFAULTS[CONF_LUX_OPEN_SUMMER]))): vol.All(vol.Coerce(int), vol.Range(min=500, max=120000)),
            vol.Required(CONF_LUX_CLOSE_WINTER, default=int(defaults.get(CONF_LUX_CLOSE_WINTER, DEFAULTS[CONF_LUX_CLOSE_WINTER]))): vol.All(vol.Coerce(int), vol.Range(min=500, max=120000)),
            vol.Required(CONF_LUX_OPEN_WINTER, default=int(defaults.get(CONF_LUX_OPEN_WINTER, DEFAULTS[CONF_LUX_OPEN_WINTER]))): vol.All(vol.Coerce(int), vol.Range(min=500, max=120000)),
            vol.Required(CONF_DEBOUNCE_MINUTES, default=int(defaults.get(CONF_DEBOUNCE_MINUTES, DEFAULTS[CONF_DEBOUNCE_MINUTES]))): vol.All(vol.Coerce(int), vol.Range(min=1, max=30)),
            vol.Required(CONF_TICK_MINUTES, default=int(defaults.get(CONF_TICK_MINUTES, DEFAULTS[CONF_TICK_MINUTES]))): vol.All(vol.Coerce(int), vol.Range(min=1, max=30)),
            vol.Required(CONF_MAX_STEP_PER_TICK, default=int(defaults.get(CONF_MAX_STEP_PER_TICK, DEFAULTS[CONF_MAX_STEP_PER_TICK]))): vol.All(vol.Coerce(int), vol.Range(min=1, max=50)),
            vol.Required(CONF_HEAT_START_HOUR, default=int(defaults.get(CONF_HEAT_START_HOUR, DEFAULTS[CONF_HEAT_START_HOUR]))): vol.All(vol.Coerce(int), vol.Range(min=0, max=23)),
            vol.Required(CONF_HEAT_END_HOUR, default=int(defaults.get(CONF_HEAT_END_HOUR, DEFAULTS[CONF_HEAT_END_HOUR]))): vol.All(vol.Coerce(int), vol.Range(min=0, max=23)),
            vol.Required(CONF_HEAT_POSITION, default=int(defaults.get(CONF_HEAT_POSITION, DEFAULTS[CONF_HEAT_POSITION]))): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
            vol.Required(CONF_TEMP_THRESHOLD, default=float(defaults.get(CONF_TEMP_THRESHOLD, DEFAULTS[CONF_TEMP_THRESHOLD]))): vol.All(vol.Coerce(float), vol.Range(min=10, max=40)),
            vol.Required(CONF_WINTER_PRIVACY_HOUR, default=int(defaults.get(CONF_WINTER_PRIVACY_HOUR, DEFAULTS[CONF_WINTER_PRIVACY_HOUR]))): vol.All(vol.Coerce(int), vol.Range(min=0, max=23)),
            vol.Required(CONF_SUMMER_PRIVACY_HOUR, default=int(defaults.get(CONF_SUMMER_PRIVACY_HOUR, DEFAULTS[CONF_SUMMER_PRIVACY_HOUR]))): vol.All(vol.Coerce(int), vol.Range(min=0, max=23)),
            vol.Required(CONF_MANUAL_OVERRIDE_MINUTES, default=int(defaults.get(CONF_MANUAL_OVERRIDE_MINUTES, DEFAULTS[CONF_MANUAL_OVERRIDE_MINUTES]))): vol.All(vol.Coerce(int), vol.Range(min=5, max=240)),
        }
    )


class HaBlindsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HA Blinds."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_COVER_ENTITY])
            self._abort_if_unique_id_configured()
            self.context["user_data"] = user_input
            return await self.async_step_options()

        return self.async_show_form(step_id="user", data_schema=_entry_schema({}), errors={})

    async def async_step_options(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            data = dict(self.context.get("user_data", {}))
            if not data:
                return self.async_abort(reason="unknown")
            if not user_input.get(CONF_TEMP_SENSOR):
                user_input.pop(CONF_TEMP_SENSOR, None)
            return self.async_create_entry(
                title=f"HA Blinds ({data[CONF_COVER_ENTITY]})",
                data=data,
                options=user_input,
            )

        return self.async_show_form(step_id="options", data_schema=_options_schema(DEFAULTS), errors={})

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return HaBlindsOptionsFlow(config_entry)


class HaBlindsOptionsFlow(config_entries.OptionsFlow):
    """Options flow for HA Blinds."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        super().__init__(config_entry)

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            if not user_input.get(CONF_TEMP_SENSOR):
                user_input.pop(CONF_TEMP_SENSOR, None)
            return self.async_create_entry(title="", data=user_input)

        defaults = {**DEFAULTS, **self.config_entry.options}
        return self.async_show_form(step_id="init", data_schema=_options_schema(defaults), errors={})
