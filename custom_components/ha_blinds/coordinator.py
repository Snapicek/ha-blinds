"""Runtime controller for HA Blinds."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from typing import Any, Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.dispatcher import async_dispatcher_send, async_dispatcher_connect

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
from .logic import DecisionConfig, DecisionEngine, DecisionInputs

_LOGGER = logging.getLogger(__name__)


@dataclass
class _RuntimeState:
    paused_until: datetime | None = None
    privacy_entered_at: datetime | None = None  # Track when privacy hour was first triggered
    high_lux_since: datetime | None = None  # Track when high lux was first detected
    low_lux_since: datetime | None = None   # Track when low lux was first detected
    last_reason: str = "startup"
    last_target: int | None = None
    last_decision_time: datetime | None = None
    error_count: int = 0
    sun_at_window: bool = False


class HaBlindsController:
    """Main runtime object per config entry."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._runtime = _RuntimeState()
        self._unsub_interval = None
        self._engine = DecisionEngine(self._decision_config())
        self._device_id = None
        self._signal = f"{DOMAIN}_{self.entry.entry_id}_update"

    async def async_start(self) -> None:
        """Start periodic evaluation and create device."""
        self._setup_device()
        tick = int(self._cfg(CONF_TICK_MINUTES))
        self._unsub_interval = async_track_time_interval(
            self.hass,
            self._async_handle_tick,
            timedelta(minutes=max(1, tick)),
        )
        await self.async_evaluate_now()
        _LOGGER.info("HA Blinds controller started for %s", self.entry.entry_id)

    async def async_stop(self) -> None:
        """Stop periodic evaluation."""
        if self._unsub_interval is not None:
            self._unsub_interval()
            self._unsub_interval = None
        _LOGGER.info("HA Blinds controller stopped for %s", self.entry.entry_id)

    def _setup_device(self) -> None:
        """Create device entry in Home Assistant device registry."""
        from homeassistant.helpers import device_registry as dr

        device_registry = dr.async_get(self.hass)
        cover_entity = str(self._cfg(CONF_COVER_ENTITY))

        self._device_id = device_registry.async_get_or_create(
            config_entry_id=self.entry.entry_id,
            identifiers={(DOMAIN, self.entry.entry_id)},
            name=f"HA Blinds - {cover_entity}",
            manufacturer="HA Blinds",
            model="Automation Controller",
        ).id
        _LOGGER.debug("Device created: %s", self._device_id)

    async def async_pause(self, minutes: int | None = None) -> None:
        """Pause automation for given minutes or configured default."""
        duration = minutes if minutes and minutes > 0 else int(self._cfg(CONF_MANUAL_OVERRIDE_MINUTES))
        self._runtime.paused_until = dt_util.now() + timedelta(minutes=duration)
        _LOGGER.info("HA Blinds paused for %s minutes on entry %s", duration, self.entry.entry_id)
        self._update_state_attributes()

    async def async_resume(self) -> None:
        """Resume automation immediately."""
        self._runtime.paused_until = None
        _LOGGER.info("HA Blinds resumed on entry %s", self.entry.entry_id)
        self._update_state_attributes()

    async def async_evaluate_now(self) -> None:
        """Force immediate re-evaluation."""
        await self._async_evaluate()

    async def _async_handle_tick(self, _now: datetime) -> None:
        await self._async_evaluate()

    async def _async_evaluate(self) -> None:
        try:
            now = dt_util.now()

            cover_entity = str(self._cfg(CONF_COVER_ENTITY))
            cover_state = self.hass.states.get(cover_entity)
            sun_state = self.hass.states.get("sun.sun")
            if cover_state is None or sun_state is None:
                self._runtime.error_count += 1
                _LOGGER.warning("Missing state: cover=%s, sun=%s (error #%d)",
                              cover_state is not None, sun_state is not None, self._runtime.error_count)
                if self._runtime.error_count > 10:
                    _LOGGER.error("Too many errors, check if cover and sun entities exist")
                return

            self._runtime.error_count = 0
            self._engine.config = self._decision_config()

            current_position = int(cover_state.attributes.get("current_position", 75))
            sun_azimuth = float(sun_state.attributes.get("azimuth", 0.0))
            sun_elevation = float(sun_state.attributes.get("elevation", -90.0))

            lux = self._float_state(str(self._cfg(CONF_LUX_SENSOR)))
            temp_entity = self._cfg(CONF_TEMP_SENSOR)
            temperature = self._float_state(str(temp_entity)) if temp_entity else None

            # Get sunrise and sunset times with offsets
            sunrise_time = self._get_sunrise_time(now)
            sunset_time = self._get_sunset_time(now)

            paused = bool(self._runtime.paused_until and now < self._runtime.paused_until)
            if self._runtime.paused_until and now >= self._runtime.paused_until:
                self._runtime.paused_until = None

            inputs = DecisionInputs(
                now=now,
                sun_azimuth=sun_azimuth,
                sun_elevation=sun_elevation,
                lux=lux,
                temperature=temperature,
                current_position=current_position,
                paused=paused,
                sunrise_time=sunrise_time,
                sunset_time=sunset_time,
                privacy_entered_at=self._runtime.privacy_entered_at,
                high_lux_since=self._runtime.high_lux_since,
                low_lux_since=self._runtime.low_lux_since,
            )
            result = self._engine.evaluate(inputs)
            self._runtime.last_reason = result.reason
            self._runtime.last_decision_time = now
            self._runtime.sun_at_window = result.sun_at_window

            # Track when privacy hour was entered
            is_winter = now.month in (11, 12, 1, 2, 3)
            enable_privacy_hour = bool(self._cfg(CONF_ENABLE_PRIVACY_HOUR))
            enable_high_lux = bool(self._cfg(CONF_ENABLE_HIGH_LUX_PROTECTION))
            enable_low_lux = bool(self._cfg(CONF_ENABLE_LOW_LUX_REOPEN))

            # If privacy hour is disabled, clear the tracking
            if not enable_privacy_hour:
                self._runtime.privacy_entered_at = None
            elif result.reason == "privacy_hour" and self._runtime.privacy_entered_at is None:
                # Just entered privacy hour
                self._runtime.privacy_entered_at = now
            elif result.reason != "privacy_hour" and self._runtime.privacy_entered_at is not None:
                # Left privacy hour (time-based, not duration-based)
                privacy_hour = int(self._cfg(CONF_WINTER_PRIVACY_HOUR)) if is_winter else int(self._cfg(CONF_SUMMER_PRIVACY_HOUR))
                if now.hour < privacy_hour:
                    # Reset only if we're before privacy hour time
                    self._runtime.privacy_entered_at = None

            # If high/low lux features are disabled, clear their tracking
            if not enable_high_lux:
                self._runtime.high_lux_since = None
            if not enable_low_lux:
                self._runtime.low_lux_since = None

            # Update lux tracking based on thresholds
            is_winter = now.month in (11, 12, 1, 2, 3)
            close_threshold = float(self._cfg(CONF_LUX_CLOSE_WINTER if is_winter else CONF_LUX_CLOSE_SUMMER))
            open_threshold = float(self._cfg(CONF_LUX_OPEN_WINTER if is_winter else CONF_LUX_OPEN_SUMMER))

            if lux is not None and (enable_high_lux or enable_low_lux):
                if lux >= close_threshold and enable_high_lux:
                    self._runtime.high_lux_since = self._runtime.high_lux_since or now
                else:
                    self._runtime.high_lux_since = None

                if lux <= open_threshold and enable_low_lux:
                    self._runtime.low_lux_since = self._runtime.low_lux_since or now
                else:
                    self._runtime.low_lux_since = None
            else:
                self._runtime.high_lux_since = None
                self._runtime.low_lux_since = None

            if not result.should_move:
                self._update_state_attributes()
                return

            step = max(1, int(self._cfg(CONF_MAX_STEP_PER_TICK)))
            target = result.target_position
            if target > current_position:
                target = min(target, current_position + step)
            else:
                target = max(target, current_position - step)

            # Apply Zigbee delay to avoid overwhelming network
            zigbee_delay = float(self._cfg(CONF_ZIGBEE_DELAY_SECONDS))
            if zigbee_delay > 0:
                await asyncio.sleep(zigbee_delay)

            await self.hass.services.async_call(
                "cover",
                "set_cover_position",
                {
                    "entity_id": cover_entity,
                    "position": target,
                },
                blocking=False,
            )
            self._runtime.last_target = target
            _LOGGER.debug(
                "HA Blinds entry=%s reason=%s current=%s target=%s sun_at_window=%s lux=%s temp=%s",
                self.entry.entry_id,
                result.reason,
                current_position,
                target,
                result.sun_at_window,
                lux,
                temperature,
            )
            self._update_state_attributes()
        except Exception as err:
            self._runtime.error_count += 1
            _LOGGER.error("Error in _async_evaluate: %s (error #%d)", err, self._runtime.error_count)
            if self._runtime.error_count <= 3:
                # Only log full traceback for first few errors
                _LOGGER.debug("Error traceback:", exc_info=True)

    def _update_state_attributes(self) -> None:
        """Notify entities to refresh from runtime state."""
        async_dispatcher_send(self.hass, self._signal)

    def _cfg(self, key: str) -> Any:
        if key in self.entry.options:
            return self.entry.options[key]
        if key in self.entry.data:
            return self.entry.data[key]
        return DEFAULTS.get(key)

    def _decision_config(self) -> DecisionConfig:
        return DecisionConfig(
            window_azimuth=int(self._cfg(CONF_WINDOW_AZIMUTH)),
            window_view_left=int(self._cfg(CONF_WINDOW_VIEW_LEFT)),
            window_view_right=int(self._cfg(CONF_WINDOW_VIEW_RIGHT)),
            lux_close_summer=float(self._cfg(CONF_LUX_CLOSE_SUMMER)),
            lux_open_summer=float(self._cfg(CONF_LUX_OPEN_SUMMER)),
            lux_close_winter=float(self._cfg(CONF_LUX_CLOSE_WINTER)),
            lux_open_winter=float(self._cfg(CONF_LUX_OPEN_WINTER)),
            debounce_minutes=int(self._cfg(CONF_DEBOUNCE_MINUTES)),
            heat_start_hour=int(self._cfg(CONF_HEAT_START_HOUR)),
            heat_end_hour=int(self._cfg(CONF_HEAT_END_HOUR)),
            heat_position=int(self._cfg(CONF_HEAT_POSITION)),
            temp_threshold=float(self._cfg(CONF_TEMP_THRESHOLD)),
            winter_privacy_hour=int(self._cfg(CONF_WINTER_PRIVACY_HOUR)),
            summer_privacy_hour=int(self._cfg(CONF_SUMMER_PRIVACY_HOUR)),
            privacy_duration_minutes=int(self._cfg(CONF_PRIVACY_DURATION_MINUTES)),
            night_close_position=int(self._cfg(CONF_NIGHT_CLOSE_POSITION)),
            enable_heat_protection=bool(self._cfg(CONF_ENABLE_HEAT_PROTECTION)),
            enable_high_lux_protection=bool(self._cfg(CONF_ENABLE_HIGH_LUX_PROTECTION)),
            enable_low_lux_reopen=bool(self._cfg(CONF_ENABLE_LOW_LUX_REOPEN)),
            enable_privacy_hour=bool(self._cfg(CONF_ENABLE_PRIVACY_HOUR)),
            enable_sun_elevation_tracking=bool(self._cfg(CONF_ENABLE_SUN_ELEVATION_TRACKING)),
            enable_sunset_closing=bool(self._cfg(CONF_ENABLE_SUNSET_CLOSING)),
            sunrise_offset_minutes=int(self._cfg(CONF_SUNRISE_OFFSET_MINUTES)),
            sunset_offset_minutes=int(self._cfg(CONF_SUNSET_OFFSET_MINUTES)),
        )

    def _float_state(self, entity_id: str) -> float | None:
        state = self.hass.states.get(entity_id)
        if state is None or state.state in ("unknown", "unavailable"):
            return None
        try:
            return float(state.state)
        except ValueError:
            return None

    def _get_time_attribute(self, attribute: str) -> datetime | None:
        """Get a datetime attribute from sun.sun entity."""
        state = self.hass.states.get("sun.sun")
        if state is None:
            return None

        time_str = state.attributes.get(attribute)
        if not time_str:
            return None

        try:
            # Parse ISO format datetime string
            if isinstance(time_str, str):
                # Handle both ISO format with and without timezone
                if time_str.endswith('+00:00'):
                    return datetime.fromisoformat(time_str)
                elif 'T' in time_str:
                    return datetime.fromisoformat(time_str)
            elif isinstance(time_str, datetime):
                return time_str
        except (ValueError, AttributeError):
            pass

        return None

    def _get_sunset_time(self, now: datetime) -> datetime | None:
        """Get sunset time with offset applied."""
        sunset_time = self._get_time_attribute("next_sunset")

        if sunset_time is None:
            return None

        offset_minutes = int(self._cfg(CONF_SUNSET_OFFSET_MINUTES))
        if offset_minutes != 0:
            sunset_time = sunset_time + timedelta(minutes=offset_minutes)

        return sunset_time

    def _get_sunrise_time(self, now: datetime) -> datetime | None:
        """Get sunrise time with offset applied."""
        sunrise_time = self._get_time_attribute("next_rising")

        if sunrise_time is None:
            return None

        offset_minutes = int(self._cfg(CONF_SUNRISE_OFFSET_MINUTES))
        if offset_minutes != 0:
            sunrise_time = sunrise_time + timedelta(minutes=offset_minutes)

        return sunrise_time

    @property
    def device_id(self) -> str | None:
        """Return the device ID."""
        return self._device_id

    def get_status_dict(self) -> dict[str, Any]:
        """Return status information for diagnostics."""
        return {
            "entry_id": self.entry.entry_id,
            "cover_entity": str(self._cfg(CONF_COVER_ENTITY)),
            "last_reason": self._runtime.last_reason,
            "last_target": self._runtime.last_target,
            "paused_until": self._runtime.paused_until.isoformat() if self._runtime.paused_until else None,
            "last_decision_time": self._runtime.last_decision_time.isoformat() if self._runtime.last_decision_time else None,
            "error_count": self._runtime.error_count,
            "sun_at_window": self._runtime.sun_at_window,
        }

    def async_add_listener(self, callback) -> Callable:
        """Add state update listener for sensors."""
        return async_dispatcher_connect(self.hass, self._signal, callback)
