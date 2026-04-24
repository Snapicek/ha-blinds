"""Config flow for HA Blinds."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector as sel

from .const import (
    CONF_COVER_ENTITY,
    CONF_DEBOUNCE_MINUTES,
    CONF_ENABLE_HEAT_PROTECTION,
    CONF_ENABLE_HIGH_LUX_PROTECTION,
    CONF_ENABLE_LOW_LUX_REOPEN,
    CONF_ENABLE_PRIVACY_HOUR,
    CONF_ENABLE_SUN_ELEVATION_TRACKING,
    CONF_ENABLE_SUNSET_CLOSING,
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
    CONF_NIGHT_CLOSE_POSITION,
    CONF_PRIVACY_DURATION_MINUTES,
    CONF_SUMMER_PRIVACY_HOUR,
    CONF_SUNRISE_OFFSET_MINUTES,
    CONF_SUNSET_OFFSET_MINUTES,
    CONF_TEMP_SENSOR,
    CONF_TEMP_THRESHOLD,
    CONF_TICK_MINUTES,
    CONF_WINDOW_AZIMUTH,
    CONF_WINDOW_VIEW_LEFT,
    CONF_WINDOW_VIEW_RIGHT,
    CONF_WINTER_PRIVACY_HOUR,
    CONF_ZIGBEE_DELAY_SECONDS,
    DEFAULTS,
    DOMAIN,
)


def _convert_time_inputs(user_input: dict[str, Any]) -> None:
    """Convert HH:MM time strings to integer hours in-place."""
    for time_key in [CONF_HEAT_START_HOUR, CONF_HEAT_END_HOUR, CONF_WINTER_PRIVACY_HOUR, CONF_SUMMER_PRIVACY_HOUR]:
        if time_key in user_input and isinstance(user_input[time_key], str):
            user_input[time_key] = int(user_input[time_key].split(":")[0])


def _convert_night_close_position(user_input: dict[str, Any]) -> None:
    """Convert night close position string to integer in-place."""
    if CONF_NIGHT_CLOSE_POSITION in user_input and isinstance(user_input[CONF_NIGHT_CLOSE_POSITION], str):
        # Extract the numeric value from "0 (Closed)" or "100 (Privacy Mode)"
        user_input[CONF_NIGHT_CLOSE_POSITION] = int(user_input[CONF_NIGHT_CLOSE_POSITION].split()[0])


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
            vol.Required(CONF_PRIVACY_DURATION_MINUTES, default=int(defaults.get(CONF_PRIVACY_DURATION_MINUTES, DEFAULTS[CONF_PRIVACY_DURATION_MINUTES]))): vol.All(vol.Coerce(int), vol.Range(min=60, max=1440)),
            vol.Required(CONF_MANUAL_OVERRIDE_MINUTES, default=int(defaults.get(CONF_MANUAL_OVERRIDE_MINUTES, DEFAULTS[CONF_MANUAL_OVERRIDE_MINUTES]))): vol.All(vol.Coerce(int), vol.Range(min=5, max=240)),
            vol.Required(CONF_NIGHT_CLOSE_POSITION, default=int(defaults.get(CONF_NIGHT_CLOSE_POSITION, DEFAULTS[CONF_NIGHT_CLOSE_POSITION]))): sel.SelectSelector(sel.SelectSelectorConfig(options=["0 (Closed)", "100 (Privacy Mode)"], mode="dropdown")),
            vol.Required(CONF_ZIGBEE_DELAY_SECONDS, default=int(defaults.get(CONF_ZIGBEE_DELAY_SECONDS, DEFAULTS[CONF_ZIGBEE_DELAY_SECONDS]))): vol.All(vol.Coerce(int), vol.Range(min=0, max=10)),
            # Sunset/Sunrise feature - uses sun.sun entity
            vol.Required(CONF_ENABLE_SUNSET_CLOSING, default=bool(defaults.get(CONF_ENABLE_SUNSET_CLOSING, DEFAULTS[CONF_ENABLE_SUNSET_CLOSING]))): bool,
            vol.Required(CONF_SUNSET_OFFSET_MINUTES, default=int(defaults.get(CONF_SUNSET_OFFSET_MINUTES, DEFAULTS[CONF_SUNSET_OFFSET_MINUTES]))): vol.All(vol.Coerce(int), vol.Range(min=-120, max=120)),
            vol.Required(CONF_SUNRISE_OFFSET_MINUTES, default=int(defaults.get(CONF_SUNRISE_OFFSET_MINUTES, DEFAULTS[CONF_SUNRISE_OFFSET_MINUTES]))): vol.All(vol.Coerce(int), vol.Range(min=-120, max=120)),
            # Feature toggles
            vol.Required(CONF_ENABLE_PRIVACY_HOUR, default=bool(defaults.get(CONF_ENABLE_PRIVACY_HOUR, DEFAULTS[CONF_ENABLE_PRIVACY_HOUR]))): bool,
            vol.Required(CONF_ENABLE_HIGH_LUX_PROTECTION, default=bool(defaults.get(CONF_ENABLE_HIGH_LUX_PROTECTION, DEFAULTS[CONF_ENABLE_HIGH_LUX_PROTECTION]))): bool,
            vol.Required(CONF_ENABLE_HEAT_PROTECTION, default=bool(defaults.get(CONF_ENABLE_HEAT_PROTECTION, DEFAULTS[CONF_ENABLE_HEAT_PROTECTION]))): bool,
            vol.Required(CONF_ENABLE_LOW_LUX_REOPEN, default=bool(defaults.get(CONF_ENABLE_LOW_LUX_REOPEN, DEFAULTS[CONF_ENABLE_LOW_LUX_REOPEN]))): bool,
            vol.Required(CONF_ENABLE_SUN_ELEVATION_TRACKING, default=bool(defaults.get(CONF_ENABLE_SUN_ELEVATION_TRACKING, DEFAULTS[CONF_ENABLE_SUN_ELEVATION_TRACKING]))): bool,
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
            _convert_night_close_position(user_input)
            return self.async_create_entry(
                title=f"HA Blinds ({data[CONF_COVER_ENTITY]})",
                data=data,
                options=user_input,
            )

        return self.async_show_form(step_id="options", data_schema=_options_schema(DEFAULTS), errors={})

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None):
        """Reconfigure step - just for updating entity IDs, not for editing settings."""
        config_entry = self._get_reconfigure_entry()
        
        if user_input is not None:
            if not user_input.get(CONF_TEMP_SENSOR):
                user_input.pop(CONF_TEMP_SENSOR, None)
            
            # Check for unique ID collision if cover entity changed
            new_cover = user_input.get(CONF_COVER_ENTITY)
            if new_cover and new_cover != config_entry.data.get(CONF_COVER_ENTITY):
                await self.async_set_unique_id(new_cover)
                self._abort_if_unique_id_configured()
            
            # Update only entity and window orientation data
            return self.async_update_reload_and_abort(
                config_entry,
                data={
                    **config_entry.data,
                    CONF_COVER_ENTITY: user_input.get(CONF_COVER_ENTITY, config_entry.data.get(CONF_COVER_ENTITY)),
                    CONF_LUX_SENSOR: user_input.get(CONF_LUX_SENSOR, config_entry.data.get(CONF_LUX_SENSOR)),
                    CONF_TEMP_SENSOR: user_input.get(CONF_TEMP_SENSOR, config_entry.data.get(CONF_TEMP_SENSOR)),
                    CONF_WINDOW_AZIMUTH: user_input.get(CONF_WINDOW_AZIMUTH, config_entry.data.get(CONF_WINDOW_AZIMUTH)),
                    CONF_WINDOW_VIEW_LEFT: user_input.get(CONF_WINDOW_VIEW_LEFT, config_entry.data.get(CONF_WINDOW_VIEW_LEFT)),
                    CONF_WINDOW_VIEW_RIGHT: user_input.get(CONF_WINDOW_VIEW_RIGHT, config_entry.data.get(CONF_WINDOW_VIEW_RIGHT)),
                },
                reason="reconfigure_successful",
            )
        
        defaults = config_entry.data
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_entry_schema(defaults),
        )

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return HaBlindsOptionsFlow()


class HaBlindsOptionsFlow(config_entries.OptionsFlow):
    """Options flow for HA Blinds."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Show main options menu."""
        return self.async_show_menu(
            step_id="init",
            menu_options={
                "thresholds": "🎚️ Adjust Thresholds (Lux, Heat, Privacy)",
                "timing": "⏱️ Adjust Timing (Tick, Debounce, Step)",
                "sunset": "🌅 Sunset/Sunrise Settings",
                "features": "⚙️ Enable/Disable Features",
                "entities": "🔧 Reconfigure Entities (Cover, Sensor)",
            },
            description_placeholders={
                "info": "Choose what to configure",
            },
        )


    async def async_step_thresholds(self, user_input: dict[str, Any] | None = None):
        """Threshold configuration."""
        if user_input is not None:
            if not user_input.get(CONF_TEMP_SENSOR):
                user_input.pop(CONF_TEMP_SENSOR, None)
            _convert_time_inputs(user_input)
            _convert_night_close_position(user_input)
            # Merge with existing options
            options = dict(self.config_entry.options)
            options.update(user_input)
            return self.async_create_entry(title="", data=options)

        defaults = {**DEFAULTS, **self.config_entry.options}
        schema_dict = {
            vol.Required(CONF_LUX_CLOSE_SUMMER, default=int(defaults.get(CONF_LUX_CLOSE_SUMMER, DEFAULTS[CONF_LUX_CLOSE_SUMMER]))): vol.All(vol.Coerce(int), vol.Range(min=1000, max=120000)),
            vol.Required(CONF_LUX_OPEN_SUMMER, default=int(defaults.get(CONF_LUX_OPEN_SUMMER, DEFAULTS[CONF_LUX_OPEN_SUMMER]))): vol.All(vol.Coerce(int), vol.Range(min=500, max=120000)),
            vol.Required(CONF_LUX_CLOSE_WINTER, default=int(defaults.get(CONF_LUX_CLOSE_WINTER, DEFAULTS[CONF_LUX_CLOSE_WINTER]))): vol.All(vol.Coerce(int), vol.Range(min=500, max=120000)),
            vol.Required(CONF_LUX_OPEN_WINTER, default=int(defaults.get(CONF_LUX_OPEN_WINTER, DEFAULTS[CONF_LUX_OPEN_WINTER]))): vol.All(vol.Coerce(int), vol.Range(min=500, max=120000)),
            vol.Required(CONF_HEAT_START_HOUR, default=f"{int(defaults.get(CONF_HEAT_START_HOUR, DEFAULTS[CONF_HEAT_START_HOUR])):02d}:00"): sel.SelectSelector(sel.SelectSelectorConfig(options=[f"{i:02d}:00" for i in range(24)], mode="dropdown")),
            vol.Required(CONF_HEAT_END_HOUR, default=f"{int(defaults.get(CONF_HEAT_END_HOUR, DEFAULTS[CONF_HEAT_END_HOUR])):02d}:00"): sel.SelectSelector(sel.SelectSelectorConfig(options=[f"{i:02d}:00" for i in range(24)], mode="dropdown")),
            vol.Required(CONF_HEAT_POSITION, default=int(defaults.get(CONF_HEAT_POSITION, DEFAULTS[CONF_HEAT_POSITION]))): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
            vol.Required(CONF_TEMP_THRESHOLD, default=float(defaults.get(CONF_TEMP_THRESHOLD, DEFAULTS[CONF_TEMP_THRESHOLD]))): vol.All(vol.Coerce(float), vol.Range(min=10, max=40)),
            vol.Required(CONF_WINTER_PRIVACY_HOUR, default=f"{int(defaults.get(CONF_WINTER_PRIVACY_HOUR, DEFAULTS[CONF_WINTER_PRIVACY_HOUR])):02d}:00"): sel.SelectSelector(sel.SelectSelectorConfig(options=[f"{i:02d}:00" for i in range(24)], mode="dropdown")),
            vol.Required(CONF_SUMMER_PRIVACY_HOUR, default=f"{int(defaults.get(CONF_SUMMER_PRIVACY_HOUR, DEFAULTS[CONF_SUMMER_PRIVACY_HOUR])):02d}:00"): sel.SelectSelector(sel.SelectSelectorConfig(options=[f"{i:02d}:00" for i in range(24)], mode="dropdown")),
            vol.Required(CONF_NIGHT_CLOSE_POSITION, default=f"{int(defaults.get(CONF_NIGHT_CLOSE_POSITION, DEFAULTS[CONF_NIGHT_CLOSE_POSITION]))} (Closed)" if int(defaults.get(CONF_NIGHT_CLOSE_POSITION, DEFAULTS[CONF_NIGHT_CLOSE_POSITION])) == 0 else "100 (Privacy Mode)"): sel.SelectSelector(sel.SelectSelectorConfig(options=["0 (Closed)", "100 (Privacy Mode)"], mode="dropdown")),
        }
        return self.async_show_form(
            step_id="thresholds",
            data_schema=vol.Schema(schema_dict),
            description_placeholders={
                "help": "Adjust lux thresholds, heat protection, and privacy hours",
            },
        )

    async def async_step_timing(self, user_input: dict[str, Any] | None = None):
        """Timing configuration."""
        if user_input is not None:
            # Merge with existing options
            options = dict(self.config_entry.options)
            options.update(user_input)
            return self.async_create_entry(title="", data=options)

        defaults = {**DEFAULTS, **self.config_entry.options}
        schema_dict = {
            vol.Required(CONF_TICK_MINUTES, default=int(defaults.get(CONF_TICK_MINUTES, DEFAULTS[CONF_TICK_MINUTES]))): vol.All(vol.Coerce(int), vol.Range(min=1, max=30)),
            vol.Required(CONF_MAX_STEP_PER_TICK, default=int(defaults.get(CONF_MAX_STEP_PER_TICK, DEFAULTS[CONF_MAX_STEP_PER_TICK]))): vol.All(vol.Coerce(int), vol.Range(min=1, max=50)),
            vol.Required(CONF_DEBOUNCE_MINUTES, default=int(defaults.get(CONF_DEBOUNCE_MINUTES, DEFAULTS[CONF_DEBOUNCE_MINUTES]))): vol.All(vol.Coerce(int), vol.Range(min=1, max=30)),
            vol.Required(CONF_MANUAL_OVERRIDE_MINUTES, default=int(defaults.get(CONF_MANUAL_OVERRIDE_MINUTES, DEFAULTS[CONF_MANUAL_OVERRIDE_MINUTES]))): vol.All(vol.Coerce(int), vol.Range(min=5, max=240)),
        }
        return self.async_show_form(
            step_id="timing",
            data_schema=vol.Schema(schema_dict),
            description_placeholders={
                "help": "Adjust check frequency, movement speed, and response timing",
            },
        )


     async def async_step_sunset(self, user_input: dict[str, Any] | None = None):
         """Sunset/Sunrise configuration - uses built-in sun.sun entity."""
         if user_input is not None:
             # Merge with existing options
             options = dict(self.config_entry.options)
             options.update(user_input)
             return self.async_create_entry(title="", data=options)

         defaults = {**DEFAULTS, **self.config_entry.options}
         schema_dict = {
             vol.Required(CONF_ENABLE_SUNSET_CLOSING, default=bool(defaults.get(CONF_ENABLE_SUNSET_CLOSING, DEFAULTS[CONF_ENABLE_SUNSET_CLOSING]))): bool,
             vol.Required(CONF_SUNSET_OFFSET_MINUTES, default=int(defaults.get(CONF_SUNSET_OFFSET_MINUTES, DEFAULTS[CONF_SUNSET_OFFSET_MINUTES]))): vol.All(vol.Coerce(int), vol.Range(min=-120, max=120)),
             vol.Required(CONF_SUNRISE_OFFSET_MINUTES, default=int(defaults.get(CONF_SUNRISE_OFFSET_MINUTES, DEFAULTS[CONF_SUNRISE_OFFSET_MINUTES]))): vol.All(vol.Coerce(int), vol.Range(min=-120, max=120)),
         }
         return self.async_show_form(
             step_id="sunset",
             data_schema=vol.Schema(schema_dict),
             description_placeholders={
                 "help": "Configure sunset/sunrise offsets. Uses the built-in sun.sun entity (automatically detected).",
             },
         )

    async def async_step_features(self, user_input: dict[str, Any] | None = None):
        """Feature toggles configuration."""
        if user_input is not None:
            # Merge with existing options
            options = dict(self.config_entry.options)
            options.update(user_input)
            return self.async_create_entry(title="", data=options)

        defaults = {**DEFAULTS, **self.config_entry.options}
        schema_dict = {
            vol.Required(CONF_ENABLE_PRIVACY_HOUR, default=bool(defaults.get(CONF_ENABLE_PRIVACY_HOUR, DEFAULTS[CONF_ENABLE_PRIVACY_HOUR]))): bool,
            vol.Required(CONF_ENABLE_HIGH_LUX_PROTECTION, default=bool(defaults.get(CONF_ENABLE_HIGH_LUX_PROTECTION, DEFAULTS[CONF_ENABLE_HIGH_LUX_PROTECTION]))): bool,
            vol.Required(CONF_ENABLE_HEAT_PROTECTION, default=bool(defaults.get(CONF_ENABLE_HEAT_PROTECTION, DEFAULTS[CONF_ENABLE_HEAT_PROTECTION]))): bool,
            vol.Required(CONF_ENABLE_LOW_LUX_REOPEN, default=bool(defaults.get(CONF_ENABLE_LOW_LUX_REOPEN, DEFAULTS[CONF_ENABLE_LOW_LUX_REOPEN]))): bool,
            vol.Required(CONF_ENABLE_SUN_ELEVATION_TRACKING, default=bool(defaults.get(CONF_ENABLE_SUN_ELEVATION_TRACKING, DEFAULTS[CONF_ENABLE_SUN_ELEVATION_TRACKING]))): bool,
        }
        return self.async_show_form(
            step_id="features",
            data_schema=vol.Schema(schema_dict),
            description_placeholders={
                "help": "Enable or disable specific automation rules",
            },
        )


    async def async_step_entities(self, user_input: dict[str, Any] | None = None):
        """Reconfigure entities (cover, lux sensor)."""
        if user_input is not None:
            if not user_input.get(CONF_TEMP_SENSOR):
                user_input.pop(CONF_TEMP_SENSOR, None)
            _convert_time_inputs(user_input)
            # Merge with existing options
            new_options = dict(self.config_entry.options)
            new_options.update(user_input)
            return self.async_create_entry(title="", data=new_options)

        defaults = {**self.config_entry.data, **self.config_entry.options}
        schema_dict = {
            vol.Required(CONF_COVER_ENTITY, default=defaults.get(CONF_COVER_ENTITY)): sel.EntitySelector(
                sel.EntitySelectorConfig(domain="cover")
            ),
            vol.Required(CONF_LUX_SENSOR, default=defaults.get(CONF_LUX_SENSOR)): sel.EntitySelector(
                sel.EntitySelectorConfig(domain="sensor", device_class="illuminance")
            ),
            vol.Optional(CONF_TEMP_SENSOR, description={"suggested_value": defaults.get(CONF_TEMP_SENSOR, "")}): sel.EntitySelector(
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
        return self.async_show_form(
            step_id="entities",
            data_schema=vol.Schema(schema_dict),
            description_placeholders={
                "help": "Change cover/sensor entities or window orientation. Integration will reload.",
            },
        )
