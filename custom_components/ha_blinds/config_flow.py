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
    CONF_ENABLED,
    DEFAULTS,
    DOMAIN,
)


def _convert_time_inputs(user_input: dict[str, Any]) -> None:
    """Convert HH:MM time strings to integer hours in-place."""
    for time_key in [CONF_HEAT_START_HOUR, CONF_HEAT_END_HOUR, CONF_WINTER_PRIVACY_HOUR, CONF_SUMMER_PRIVACY_HOUR]:
        if time_key in user_input and isinstance(user_input[time_key], str):
            user_input[time_key] = int(user_input[time_key].split(":")[0])


def _entry_schema(defaults: dict[str, Any]) -> vol.Schema:
    schema = {
        vol.Required(CONF_COVER_ENTITY): sel.EntitySelector(
            sel.EntitySelectorConfig(domain="cover")
        ),
        vol.Required(CONF_LUX_SENSOR): sel.EntitySelector(
            sel.EntitySelectorConfig(domain="sensor", device_class="illuminance")
        ),
        vol.Optional(CONF_TEMP_SENSOR): sel.EntitySelector(
            sel.EntitySelectorConfig(domain="sensor", device_class="temperature")
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
            vol.Required(CONF_HEAT_START_HOUR, default=f"{int(defaults.get(CONF_HEAT_START_HOUR, DEFAULTS[CONF_HEAT_START_HOUR])):02d}:00"): sel.SelectSelector(sel.SelectSelectorConfig(options=[f"{i:02d}:00" for i in range(24)], mode="dropdown")),
            vol.Required(CONF_HEAT_END_HOUR, default=f"{int(defaults.get(CONF_HEAT_END_HOUR, DEFAULTS[CONF_HEAT_END_HOUR])):02d}:00"): sel.SelectSelector(sel.SelectSelectorConfig(options=[f"{i:02d}:00" for i in range(24)], mode="dropdown")),
            vol.Required(CONF_HEAT_POSITION, default=int(defaults.get(CONF_HEAT_POSITION, DEFAULTS[CONF_HEAT_POSITION]))): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
            vol.Required(CONF_TEMP_THRESHOLD, default=float(defaults.get(CONF_TEMP_THRESHOLD, DEFAULTS[CONF_TEMP_THRESHOLD]))): vol.All(vol.Coerce(float), vol.Range(min=10, max=40)),
            vol.Required(CONF_WINTER_PRIVACY_HOUR, default=f"{int(defaults.get(CONF_WINTER_PRIVACY_HOUR, DEFAULTS[CONF_WINTER_PRIVACY_HOUR])):02d}:00"): sel.SelectSelector(sel.SelectSelectorConfig(options=[f"{i:02d}:00" for i in range(24)], mode="dropdown")),
            vol.Required(CONF_SUMMER_PRIVACY_HOUR, default=f"{int(defaults.get(CONF_SUMMER_PRIVACY_HOUR, DEFAULTS[CONF_SUMMER_PRIVACY_HOUR])):02d}:00"): sel.SelectSelector(sel.SelectSelectorConfig(options=[f"{i:02d}:00" for i in range(24)], mode="dropdown")),
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

        errors = {}
        return self.async_show_form(
            step_id="user",
            data_schema=_entry_schema({}),
            errors=errors,
            description_placeholders={
                "setup_info": "Select your blind cover entity, a lux sensor, and define your window orientation.",
            },
        )

    async def async_step_options(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            data = dict(self.context.get("user_data", {}))
            if not data:
                return self.async_abort(reason="unknown")
            if not user_input.get(CONF_TEMP_SENSOR):
                user_input.pop(CONF_TEMP_SENSOR, None)
            # Convert time strings back to integers
            _convert_time_inputs(user_input)
            return self.async_create_entry(
                title=f"HA Blinds ({data[CONF_COVER_ENTITY]})",
                data=data,
                options=user_input,
            )

        return self.async_show_form(step_id="options", data_schema=_options_schema(DEFAULTS), errors={})

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None):
        """Reconfigure step to update entities or window orientation."""
        config_entry = self._get_reconfigure_entry()
        
        if user_input is not None:
            if not user_input.get(CONF_TEMP_SENSOR):
                user_input.pop(CONF_TEMP_SENSOR, None)
            
            # Convert time strings back to integers
            _convert_time_inputs(user_input)
            
            # Extract entity/orientation data
            entity_fields = {k: v for k, v in user_input.items() if k in [
                CONF_COVER_ENTITY, CONF_LUX_SENSOR, CONF_TEMP_SENSOR, 
                CONF_WINDOW_AZIMUTH, CONF_WINDOW_VIEW_LEFT, CONF_WINDOW_VIEW_RIGHT
            ]}
            
            # Check for unique ID collision if cover entity changed
            new_cover = entity_fields.get(CONF_COVER_ENTITY)
            if new_cover and new_cover != config_entry.data.get(CONF_COVER_ENTITY):
                await self.async_set_unique_id(new_cover)
                self._abort_if_unique_id_configured()

            # Merge entity fields with old data
            new_data = {**config_entry.data, **entity_fields}
            
            # Put options in new options 
            new_options = {k: v for k, v in user_input.items() if k not in entity_fields}
            # Keep previously existing options (like CONF_ENABLED and other options not in reconfigure schema)
            new_options = {**config_entry.options, **new_options}
            
            return self.async_update_reload_and_abort(
                config_entry,
                data=new_data,
                reason="reconfigure_successful",
            )
        
        defaults = {**config_entry.data, **config_entry.options}
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_entry_schema(defaults),
            description_placeholders={
                "setup_info": "Update your blind cover entity, lux sensor, or window orientation.",
            },
        )

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return HaBlindsOptionsFlow(config_entry)


class HaBlindsOptionsFlow(config_entries.OptionsFlow):
    """Options flow for HA Blinds."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Manage the options."""
        if user_input is not None:
            _convert_time_inputs(user_input)
            # Merge with existing options (keeps our switch feature toggles intact)
            options = {**self.config_entry.options, **user_input}
            return self.async_create_entry(title="", data=options)

        defaults = {**DEFAULTS, **self.config_entry.options}
        return self.async_show_form(
            step_id="init",
            data_schema=_options_schema(defaults),
        )
