"""Pure decision engine for HA Blinds.

This module stays Home-Assistant-independent so it can be unit-tested locally.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class DecisionConfig:
    window_azimuth: int
    window_view_left: int
    window_view_right: int
    lux_close_summer: float
    lux_open_summer: float
    lux_close_winter: float
    lux_open_winter: float
    debounce_minutes: int
    heat_start_hour: int
    heat_end_hour: int
    heat_position: int
    temp_threshold: float
    winter_privacy_hour: int
    summer_privacy_hour: int
    # Feature toggles
    enable_heat_protection: bool = True
    enable_high_lux_protection: bool = True
    enable_low_lux_reopen: bool = True
    enable_privacy_hour: bool = True
    enable_sun_elevation_tracking: bool = True


@dataclass
class DecisionInputs:
    now: datetime
    sun_azimuth: float
    sun_elevation: float
    lux: float | None
    temperature: float | None
    current_position: int
    paused: bool


@dataclass
class DecisionResult:
    should_move: bool
    target_position: int
    reason: str
    sun_at_window: bool


@dataclass
class EngineState:
    high_lux_since: datetime | None = None
    low_lux_since: datetime | None = None


class DecisionEngine:
    """Evaluate desired slat position using sun/lux/season rules."""

    def __init__(self, config: DecisionConfig) -> None:
        self.config = config
        self.state = EngineState()

    def evaluate(self, inputs: DecisionInputs) -> DecisionResult:
        is_winter = inputs.now.month in (11, 12, 1, 2, 3)
        sun_at_window = self._sun_at_window(inputs.sun_azimuth, inputs.sun_elevation)

        if inputs.paused:
            return DecisionResult(False, inputs.current_position, "paused", sun_at_window)

        # Privacy hour (if enabled)
        if self.config.enable_privacy_hour:
            privacy_hour = self.config.winter_privacy_hour if is_winter else self.config.summer_privacy_hour
            if inputs.now.hour >= privacy_hour:
                return self._result(inputs.current_position, 100, "privacy_hour", sun_at_window)

        # Night close (always active - safety feature)
        if inputs.sun_elevation < 0:
            return self._result(inputs.current_position, 100, "night_close", sun_at_window)

        close_threshold = self.config.lux_close_winter if is_winter else self.config.lux_close_summer
        open_threshold = self.config.lux_open_winter if is_winter else self.config.lux_open_summer
        self._update_debounce(inputs.now, inputs.lux, close_threshold, open_threshold)

        # High lux protection (if enabled)
        if self.config.enable_high_lux_protection and sun_at_window and self._debounced(self.state.high_lux_since, inputs.now):
            return self._result(inputs.current_position, 0, "direct_sun_high_lux", sun_at_window)

        # Heat protection (if enabled)
        if (
            self.config.enable_heat_protection
            and not is_winter
            and sun_at_window
            and self._hour_in_range(inputs.now.hour, self.config.heat_start_hour, self.config.heat_end_hour)
        ):
            return self._result(
                inputs.current_position,
                self.config.heat_position,
                "peak_heat_hours",
                sun_at_window,
            )

        # Low lux reopen (if enabled)
        if self.config.enable_low_lux_reopen and sun_at_window and self._debounced(self.state.low_lux_since, inputs.now):
            return self._result(inputs.current_position, 75, "low_lux_reopen", sun_at_window)

        # Sun elevation tracking (if enabled)
        if self.config.enable_sun_elevation_tracking:
            target = self._base_sun_target(inputs.sun_elevation)
            if inputs.temperature is not None and not is_winter and sun_at_window:
                if inputs.temperature >= self.config.temp_threshold:
                    # During heat protection, close more (reduce from current target toward 0%)
                    target = min(target, int(self.config.heat_position))

            return self._result(inputs.current_position, target, "sun_elevation_tracking", sun_at_window)
        
        # If sun tracking is disabled, maintain current position
        return DecisionResult(False, inputs.current_position, "sun_tracking_disabled", sun_at_window)

    def _result(
        self,
        current_position: int,
        target_position: int,
        reason: str,
        sun_at_window: bool,
    ) -> DecisionResult:
        target = max(0, min(100, int(target_position)))
        return DecisionResult(abs(target - current_position) >= 2, target, reason, sun_at_window)

    def _update_debounce(
        self,
        now: datetime,
        lux: float | None,
        close_threshold: float,
        open_threshold: float,
    ) -> None:
        if lux is None:
            self.state.high_lux_since = None
            self.state.low_lux_since = None
            return

        if lux >= close_threshold:
            self.state.high_lux_since = self.state.high_lux_since or now
        else:
            self.state.high_lux_since = None

        if lux <= open_threshold:
            self.state.low_lux_since = self.state.low_lux_since or now
        else:
            self.state.low_lux_since = None

    def _debounced(self, since: datetime | None, now: datetime) -> bool:
        if since is None:
            return False
        return now - since >= timedelta(minutes=self.config.debounce_minutes)

    @staticmethod
    def _hour_in_range(hour: int, start: int, end: int) -> bool:
        if start <= end:
            return start <= hour < end
        return hour >= start or hour < end

    def _sun_at_window(self, azimuth: float, elevation: float) -> bool:
        if elevation <= 0:
            return False
        left = (self.config.window_azimuth - self.config.window_view_left) % 360
        right = (self.config.window_azimuth + self.config.window_view_right) % 360
        if left <= right:
            return left <= azimuth <= right
        return azimuth >= left or azimuth <= right

    @staticmethod
    def _base_sun_target(elevation: float) -> int:
        """Calculate blind position based on sun elevation.
        
        Positions:
        - 0% and 100% = CLOSED (different directions)
        - 75% = MOST OPEN (horizontal slats - maximum light penetration)
        
        Strategy:
        - Low elevation sun (<25°): Direct hit at eye level → CLOSE (0% or 100%)
        - Medium elevation (25-50°): Sun angle less critical → MEDIUM OPEN (50-75%)
        - High elevation (>50°): Sun from above → OPEN (75%)
        """
        if elevation < 10:
            return 0  # Very low sun - close completely
        if elevation < 25:
            return 50  # Low sun angle - half open
        if elevation < 40:
            return 75  # Medium-high sun - open (sun not in eyes)
        return 75  # High sun angle - fully open (sun from above)

