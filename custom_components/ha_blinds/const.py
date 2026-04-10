"""Constants for HA Blinds."""

from __future__ import annotations

DOMAIN = "ha_blinds"

CONF_COVER_ENTITY = "cover_entity"
CONF_LUX_SENSOR = "lux_sensor"
CONF_TEMP_SENSOR = "temp_sensor"
CONF_WINDOW_AZIMUTH = "window_azimuth"
CONF_WINDOW_VIEW_LEFT = "window_view_left"
CONF_WINDOW_VIEW_RIGHT = "window_view_right"

CONF_LUX_CLOSE_SUMMER = "lux_close_summer"
CONF_LUX_OPEN_SUMMER = "lux_open_summer"
CONF_LUX_CLOSE_WINTER = "lux_close_winter"
CONF_LUX_OPEN_WINTER = "lux_open_winter"
CONF_DEBOUNCE_MINUTES = "debounce_minutes"
CONF_TICK_MINUTES = "tick_minutes"
CONF_MAX_STEP_PER_TICK = "max_step_per_tick"
CONF_HEAT_START_HOUR = "heat_start_hour"
CONF_HEAT_END_HOUR = "heat_end_hour"
CONF_HEAT_POSITION = "heat_position"
CONF_TEMP_THRESHOLD = "temp_threshold"
CONF_WINTER_PRIVACY_HOUR = "winter_privacy_hour"
CONF_SUMMER_PRIVACY_HOUR = "summer_privacy_hour"
CONF_MANUAL_OVERRIDE_MINUTES = "manual_override_minutes"

SERVICE_PAUSE = "pause"
SERVICE_RESUME = "resume"
SERVICE_EVALUATE_NOW = "evaluate_now"

ATTR_ENTRY_ID = "entry_id"
ATTR_MINUTES = "minutes"

DEFAULTS: dict[str, int | float] = {
    CONF_WINDOW_AZIMUTH: 240,
    CONF_WINDOW_VIEW_LEFT: 60,
    CONF_WINDOW_VIEW_RIGHT: 60,
    CONF_LUX_CLOSE_SUMMER: 35000,
    CONF_LUX_OPEN_SUMMER: 20000,
    CONF_LUX_CLOSE_WINTER: 20000,
    CONF_LUX_OPEN_WINTER: 12000,
    CONF_DEBOUNCE_MINUTES: 5,
    CONF_TICK_MINUTES: 5,
    CONF_MAX_STEP_PER_TICK: 10,
    CONF_HEAT_START_HOUR: 10,
    CONF_HEAT_END_HOUR: 17,
    CONF_HEAT_POSITION: 20,
    CONF_TEMP_THRESHOLD: 24.0,
    CONF_WINTER_PRIVACY_HOUR: 16,
    CONF_SUMMER_PRIVACY_HOUR: 19,
    CONF_MANUAL_OVERRIDE_MINUTES: 45,
}

