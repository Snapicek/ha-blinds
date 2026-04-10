"""Runtime controller for HA Blinds."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from homeassistant.helpers.event import async_track_time_interval

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
)
from .logic import DecisionConfig, DecisionEngine, DecisionInputs

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class _RuntimeState:
    paused_until: datetime | None = None
    last_reason: str = "startup"
    last_target: int | None = None


class HaBlindsController:
    """Main runtime object per config entry."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._runtime = _RuntimeState()
        self._unsub_interval = None
        self._engine = DecisionEngine(self._decision_config())

    async def async_start(self) -> None:
        """Start periodic evaluation."""
        tick = int(self._cfg(CONF_TICK_MINUTES))
        self._unsub_interval = async_track_time_interval(
            self.hass,
            self._async_handle_tick,
            timedelta(minutes=max(1, tick)),
        )
        await self.async_evaluate_now()

    async def async_stop(self) -> None:
        """Stop periodic evaluation."""
        if self._unsub_interval is not None:
            self._unsub_interval()
            self._unsub_interval = None

    async def async_pause(self, minutes: int | None = None) -> None:
        """Pause automation for given minutes or configured default."""
        duration = minutes if minutes and minutes > 0 else int(self._cfg(CONF_MANUAL_OVERRIDE_MINUTES))
        self._runtime.paused_until = dt_util.now() + timedelta(minutes=duration)
        _LOGGER.info("HA Blinds paused for %s minutes on entry %s", duration, self.entry.entry_id)

    async def async_resume(self) -> None:
        """Resume automation immediately."""
        self._runtime.paused_until = None
        _LOGGER.info("HA Blinds resumed on entry %s", self.entry.entry_id)

    async def async_evaluate_now(self) -> None:
        """Force immediate re-evaluation."""
        await self._async_evaluate()

    async def _async_handle_tick(self, _now: datetime) -> None:
        await self._async_evaluate()

    async def _async_evaluate(self) -> None:
        now = dt_util.now()

        cover_entity = str(self._cfg(CONF_COVER_ENTITY))
        cover_state = self.hass.states.get(cover_entity)
        sun_state = self.hass.states.get("sun.sun")
        if cover_state is None or sun_state is None:
            return

        self._engine.config = self._decision_config()

        current_position = int(cover_state.attributes.get("current_position", 75))
        sun_azimuth = float(sun_state.attributes.get("azimuth", 0.0))
        sun_elevation = float(sun_state.attributes.get("elevation", -90.0))

        lux = self._float_state(str(self._cfg(CONF_LUX_SENSOR)))
        temp_entity = self._cfg(CONF_TEMP_SENSOR)
        temperature = self._float_state(str(temp_entity)) if temp_entity else None

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
        )
        result = self._engine.evaluate(inputs)
        self._runtime.last_reason = result.reason

        if not result.should_move:
            return

        step = max(1, int(self._cfg(CONF_MAX_STEP_PER_TICK)))
        target = result.target_position
        if target > current_position:
            target = min(target, current_position + step)
        else:
            target = max(target, current_position - step)

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
            "HA Blinds entry=%s reason=%s current=%s target=%s sun_at_window=%s",
            self.entry.entry_id,
            result.reason,
            current_position,
            target,
            result.sun_at_window,
        )

    def _cfg(self, key: str) -> Any:
        if key in self.entry.options:
            return self.entry.options[key]
        if key in self.entry.data:
            return self.entry.data[key]
        return DEFAULTS[key]

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
        )

    def _float_state(self, entity_id: str) -> float | None:
        state = self.hass.states.get(entity_id)
        if state is None or state.state in ("unknown", "unavailable"):
            return None
        try:
            return float(state.state)
        except ValueError:
            return None
