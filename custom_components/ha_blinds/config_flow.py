"""
Patch for config_flow.py – add async_step_reconfigure to HABlindsConfigFlow.

Paste this block INSIDE the HABlindsConfigFlow class, right after async_step_user
(or wherever your other step handlers live).

It mirrors the exact same 5-step flow used during initial setup but pre-fills
every field with the current saved values so the user only changes what they want.
"""

# ── In config_flow.py, add this import if not already present ──────────────
# from homeassistant.config_entries import ConfigEntry   # already imported normally

# ── Add CONF_ENABLED to your const.py imports ──────────────────────────────
# from .const import (DOMAIN, CONF_ENABLED, CONF_COVER, CONF_LUX_SENSOR,
#     CONF_TEMP_SENSOR, CONF_AZIMUTH, CONF_VIEW_LEFT, CONF_VIEW_RIGHT,
#     CONF_TICK_MINUTES, CONF_MAX_STEP, CONF_DEBOUNCE_MINUTES,
#     CONF_LUX_CLOSE_SUMMER, CONF_LUX_OPEN_SUMMER,
#     CONF_LUX_CLOSE_WINTER, CONF_LUX_OPEN_WINTER,
#     CONF_HEAT_START_HOUR, CONF_HEAT_END_HOUR,
#     CONF_HEAT_POSITION, CONF_TEMP_THRESHOLD,
#     CONF_WINTER_PRIVACY_HOUR, CONF_SUMMER_PRIVACY_HOUR,
#     CONF_MANUAL_OVERRIDE_MINUTES,
#     DEFAULT_TICK, DEFAULT_MAX_STEP, DEFAULT_DEBOUNCE,
#     DEFAULT_LUX_CLOSE_SUMMER, DEFAULT_LUX_OPEN_SUMMER,
#     DEFAULT_LUX_CLOSE_WINTER, DEFAULT_LUX_OPEN_WINTER,
#     DEFAULT_HEAT_START, DEFAULT_HEAT_END, DEFAULT_HEAT_POSITION,
#     DEFAULT_TEMP_THRESHOLD, DEFAULT_WINTER_PRIVACY, DEFAULT_SUMMER_PRIVACY,
#     DEFAULT_MANUAL_OVERRIDE)

# ═══════════════════════════════════════════════════════════════════════════════
#  RECONFIGURE – mirrors the 5-step initial setup, pre-filled with saved values
# ═══════════════════════════════════════════════════════════════════════════════

    async def async_step_reconfigure(
        self, user_input: dict | None = None
    ):
        """Entry point called when user clicks Reconfigure in Settings → Devices & Services."""
        # Merge existing data + options so we always have defaults to fall back on
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        self._current_data = {**entry.data, **entry.options}
        return await self.async_step_reconfigure_entities(user_input=None)

    # ── Step 1: Entities ──────────────────────────────────────────────────────
    async def async_step_reconfigure_entities(
        self, user_input: dict | None = None
    ):
        errors: dict[str, str] = {}
        cur = self._current_data

        if user_input is not None:
            self._reconfigure_partial = {**user_input}
            return await self.async_step_reconfigure_orientation(user_input=None)

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_COVER,
                    default=cur.get(CONF_COVER, vol.UNDEFINED),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="cover")
                ),
                vol.Required(
                    CONF_LUX_SENSOR,
                    default=cur.get(CONF_LUX_SENSOR, vol.UNDEFINED),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(
                    CONF_TEMP_SENSOR,
                    default=cur.get(CONF_TEMP_SENSOR, vol.UNDEFINED),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
            }
        )
        return self.async_show_form(
            step_id="reconfigure_entities",
            data_schema=schema,
            errors=errors,
            description_placeholders={"step": "1 / 5"},
        )

    # ── Step 2: Window Orientation ────────────────────────────────────────────
    async def async_step_reconfigure_orientation(
        self, user_input: dict | None = None
    ):
        errors: dict[str, str] = {}
        cur = self._current_data

        if user_input is not None:
            self._reconfigure_partial.update(user_input)
            return await self.async_step_reconfigure_lux(user_input=None)

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_AZIMUTH,
                    default=cur.get(CONF_AZIMUTH, 180),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=359, step=1, mode="box")
                ),
                vol.Required(
                    CONF_VIEW_LEFT,
                    default=cur.get(CONF_VIEW_LEFT, 90),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=180, step=1, mode="box")
                ),
                vol.Required(
                    CONF_VIEW_RIGHT,
                    default=cur.get(CONF_VIEW_RIGHT, 90),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=180, step=1, mode="box")
                ),
            }
        )
        return self.async_show_form(
            step_id="reconfigure_orientation",
            data_schema=schema,
            errors=errors,
            description_placeholders={"step": "2 / 5"},
        )

    # ── Step 3: Lux Thresholds ────────────────────────────────────────────────
    async def async_step_reconfigure_lux(
        self, user_input: dict | None = None
    ):
        errors: dict[str, str] = {}
        cur = self._current_data

        if user_input is not None:
            self._reconfigure_partial.update(user_input)
            return await self.async_step_reconfigure_heat(user_input=None)

        schema = vol.Schema(
            {
                vol.Required(CONF_LUX_CLOSE_SUMMER, default=cur.get(CONF_LUX_CLOSE_SUMMER, DEFAULT_LUX_CLOSE_SUMMER)): selector.NumberSelector(selector.NumberSelectorConfig(min=1000, max=120000, step=500, mode="box")),
                vol.Required(CONF_LUX_OPEN_SUMMER,  default=cur.get(CONF_LUX_OPEN_SUMMER,  DEFAULT_LUX_OPEN_SUMMER )):  selector.NumberSelector(selector.NumberSelectorConfig(min=500,  max=120000, step=500, mode="box")),
                vol.Required(CONF_LUX_CLOSE_WINTER, default=cur.get(CONF_LUX_CLOSE_WINTER, DEFAULT_LUX_CLOSE_WINTER)): selector.NumberSelector(selector.NumberSelectorConfig(min=500,  max=120000, step=500, mode="box")),
                vol.Required(CONF_LUX_OPEN_WINTER,  default=cur.get(CONF_LUX_OPEN_WINTER,  DEFAULT_LUX_OPEN_WINTER )):  selector.NumberSelector(selector.NumberSelectorConfig(min=500,  max=120000, step=500, mode="box")),
            }
        )
        return self.async_show_form(
            step_id="reconfigure_lux",
            data_schema=schema,
            errors=errors,
            description_placeholders={"step": "3 / 5"},
        )

    # ── Step 4: Heat Protection ───────────────────────────────────────────────
    async def async_step_reconfigure_heat(
        self, user_input: dict | None = None
    ):
        errors: dict[str, str] = {}
        cur = self._current_data

        if user_input is not None:
            self._reconfigure_partial.update(user_input)
            return await self.async_step_reconfigure_timing(user_input=None)

        schema = vol.Schema(
            {
                vol.Required(CONF_HEAT_START_HOUR,  default=cur.get(CONF_HEAT_START_HOUR,  DEFAULT_HEAT_START    )): selector.NumberSelector(selector.NumberSelectorConfig(min=0, max=23, step=1, mode="box")),
                vol.Required(CONF_HEAT_END_HOUR,    default=cur.get(CONF_HEAT_END_HOUR,    DEFAULT_HEAT_END      )): selector.NumberSelector(selector.NumberSelectorConfig(min=0, max=23, step=1, mode="box")),
                vol.Required(CONF_HEAT_POSITION,    default=cur.get(CONF_HEAT_POSITION,    DEFAULT_HEAT_POSITION )): selector.NumberSelector(selector.NumberSelectorConfig(min=0, max=100, step=1, mode="box")),
                vol.Required(CONF_TEMP_THRESHOLD,   default=cur.get(CONF_TEMP_THRESHOLD,   DEFAULT_TEMP_THRESHOLD)): selector.NumberSelector(selector.NumberSelectorConfig(min=10, max=40, step=0.5, mode="box")),
            }
        )
        return self.async_show_form(
            step_id="reconfigure_heat",
            data_schema=schema,
            errors=errors,
            description_placeholders={"step": "4 / 5"},
        )

    # ── Step 5: Timing & Privacy ──────────────────────────────────────────────
    async def async_step_reconfigure_timing(
        self, user_input: dict | None = None
    ):
        errors: dict[str, str] = {}
        cur = self._current_data

        if user_input is not None:
            self._reconfigure_partial.update(user_input)
            # All 5 steps done – save and reload
            return await self._async_finish_reconfigure(self._reconfigure_partial)

        schema = vol.Schema(
            {
                vol.Required(CONF_TICK_MINUTES,           default=cur.get(CONF_TICK_MINUTES,           DEFAULT_TICK            )): selector.NumberSelector(selector.NumberSelectorConfig(min=1,  max=30,  step=1,  mode="box")),
                vol.Required(CONF_MAX_STEP,               default=cur.get(CONF_MAX_STEP,               DEFAULT_MAX_STEP        )): selector.NumberSelector(selector.NumberSelectorConfig(min=1,  max=50,  step=1,  mode="box")),
                vol.Required(CONF_DEBOUNCE_MINUTES,       default=cur.get(CONF_DEBOUNCE_MINUTES,       DEFAULT_DEBOUNCE        )): selector.NumberSelector(selector.NumberSelectorConfig(min=1,  max=30,  step=1,  mode="box")),
                vol.Required(CONF_WINTER_PRIVACY_HOUR,    default=cur.get(CONF_WINTER_PRIVACY_HOUR,    DEFAULT_WINTER_PRIVACY  )): selector.NumberSelector(selector.NumberSelectorConfig(min=0,  max=23,  step=1,  mode="box")),
                vol.Required(CONF_SUMMER_PRIVACY_HOUR,    default=cur.get(CONF_SUMMER_PRIVACY_HOUR,    DEFAULT_SUMMER_PRIVACY  )): selector.NumberSelector(selector.NumberSelectorConfig(min=0,  max=23,  step=1,  mode="box")),
                vol.Required(CONF_MANUAL_OVERRIDE_MINUTES,default=cur.get(CONF_MANUAL_OVERRIDE_MINUTES,DEFAULT_MANUAL_OVERRIDE )): selector.NumberSelector(selector.NumberSelectorConfig(min=5,  max=240, step=5,  mode="box")),
            }
        )
        return self.async_show_form(
            step_id="reconfigure_timing",
            data_schema=schema,
            errors=errors,
            description_placeholders={"step": "5 / 5"},
        )

    # ── Finish: persist and reload ────────────────────────────────────────────
    async def _async_finish_reconfigure(self, data: dict):
        """Save all reconfigured values back to the config entry and reload."""
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])

        # Split: entity/orientation keys go to entry.data, tuning keys go to options
        _DATA_KEYS = {CONF_COVER, CONF_LUX_SENSOR, CONF_TEMP_SENSOR,
                      CONF_AZIMUTH, CONF_VIEW_LEFT, CONF_VIEW_RIGHT}
        new_data    = {k: v for k, v in data.items() if k in _DATA_KEYS}
        new_options = {k: v for k, v in data.items() if k not in _DATA_KEYS}

        # Preserve the enabled flag so a reconfigure doesn't reset it
        new_options[CONF_ENABLED] = entry.options.get(CONF_ENABLED, True)

        self.hass.config_entries.async_update_entry(
            entry,
            data={**entry.data, **new_data},
            options={**entry.options, **new_options},
        )
        await self.hass.config_entries.async_reload(entry.entry_id)
        return self.async_abort(reason="reconfigure_successful")
