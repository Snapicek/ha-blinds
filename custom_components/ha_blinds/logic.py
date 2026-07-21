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
    lux_close_winter: float
    debounce_minutes: int
    heat_start_hour: int
    heat_end_hour: int
    heat_position: int
    temp_threshold: float
    privacy_duration_minutes: int = 480
    night_close_position: int = 0
    daytime_open_position_summer: int = 60
    daytime_open_position_winter: int = 70
    privacy_lead_minutes: int = 60
    privacy_position: int = 100
    # Feature toggles
    enable_heat_protection: bool = True
    enable_high_lux_protection: bool = True
    enable_privacy_hour: bool = True
    enable_sun_elevation_tracking: bool = True
    # Sunset/Sunrise feature
    enable_sunset_closing: bool = False
    sunrise_offset_minutes: int = 0
    sunset_offset_minutes: int = 0
    # Earliest open time
    earliest_open_hour: int = 7
    earliest_open_minute: int = 30
    # Lux-driven daytime logic
    lux_low_threshold: float = 5000
    movement_threshold: int = 5
    min_position: int = 3
    # Lux-driven dusk closing
    dusk_lux_threshold: float = 1000
    dusk_window_minutes: int = 60


@dataclass
class DecisionInputs:
    now: datetime
    sun_azimuth: float
    sun_elevation: float
    lux: float | None
    temperature: float | None
    current_position: int
    paused: bool
    sunrise_time: datetime | None = None
    sunset_time: datetime | None = None
    privacy_entered_at: datetime | None = None
    high_lux_since: datetime | None = None


@dataclass
class DecisionResult:
    should_move: bool
    target_position: int
    reason: str
    sun_at_window: bool


class DecisionEngine:
    """Evaluate desired slat position using sun/lux/season rules."""

    def __init__(self, config: DecisionConfig) -> None:
        self.config = config

    def evaluate(self, inputs: DecisionInputs) -> DecisionResult:
        is_winter = inputs.now.month in (11, 12, 1, 2, 3)
        daytime_open_position = (
            self.config.daytime_open_position_winter if is_winter else self.config.daytime_open_position_summer
        )
        sun_at_window = self._sun_at_window(inputs.sun_azimuth, inputs.sun_elevation)

        if inputs.paused:
            return DecisionResult(False, inputs.current_position, "paused", sun_at_window)

        # Hard floor: do not open before earliest_open_time
        earliest = inputs.now.replace(
            hour=self.config.earliest_open_hour,
            minute=self.config.earliest_open_minute,
            second=0, microsecond=0,
        )
        if inputs.now < earliest:
            return self._result(inputs.current_position, self.config.night_close_position, "too_early", sun_at_window)

        # Dusk closing: lux-driven, so it feels natural for windows shaded early by
        # neighboring buildings — closes before the hard sunset cutoff once it's
        # actually getting dark, instead of waiting for the astronomical sunset time.
        if self.config.enable_sunset_closing and inputs.sunset_time is not None and inputs.lux is not None:
            dusk_start = inputs.sunset_time - timedelta(minutes=self.config.dusk_window_minutes)
            if dusk_start <= inputs.now < inputs.sunset_time and inputs.lux < self.config.dusk_lux_threshold:
                return self._result(inputs.current_position, self.config.night_close_position, "dusk_closing", sun_at_window)

        # Sunset closing — fallback/ceiling. Fires regardless of lux (missing sensor,
        # or light staying high past sunset) so blinds always close eventually.
        if self.config.enable_sunset_closing and inputs.sunset_time is not None:
            if inputs.now >= inputs.sunset_time:
                return self._result(inputs.current_position, self.config.night_close_position, "sunset_closing", sun_at_window)

        # Pre-sunrise: keep closed until sunrise + offset (sleep-in).
        # Only applies in the morning — the sunset offset window is always evening.
        if self.config.enable_sunset_closing and inputs.sunrise_time is not None:
            if inputs.now < inputs.sunrise_time and inputs.now.hour < 12:
                return self._result(inputs.current_position, self.config.night_close_position, "pre_sunrise_closing", sun_at_window)

        # Privacy hour: sunset-relative flip. `privacy_lead_minutes` before actual
        # sunset, flip to `privacy_position` (light passes through, but nobody can
        # see in). At actual sunset, close fully like every other closing rule.
        # `privacy_duration_minutes` is hysteresis: once entered, stays active even
        # if sunset_time later becomes unavailable (e.g. sun.sun glitch).
        if self.config.enable_privacy_hour and inputs.sunset_time is not None:
            privacy_start = inputs.sunset_time - timedelta(minutes=self.config.privacy_lead_minutes)
            still_in_hysteresis = inputs.privacy_entered_at is not None and inputs.now < (
                inputs.privacy_entered_at + timedelta(minutes=self.config.privacy_duration_minutes)
            )
            if inputs.now >= privacy_start or still_in_hysteresis:
                if inputs.now < inputs.sunset_time:
                    return self._result(inputs.current_position, self.config.privacy_position, "privacy_hour", sun_at_window)
                return self._result(inputs.current_position, self.config.night_close_position, "privacy_hour", sun_at_window)

        # Night close (safety) — suppressed during the sunset offset window so blinds
        # stay open between actual sunset and sunset + offset as configured.
        if inputs.sun_elevation < 0:
            in_sunset_offset_window = (
                self.config.enable_sunset_closing
                and inputs.sunset_time is not None
                and inputs.now < inputs.sunset_time
            )
            if not in_sunset_offset_window:
                return self._result(inputs.current_position, self.config.night_close_position, "night_close", sun_at_window)

        lux_is_low = inputs.lux is not None and inputs.lux < self.config.lux_low_threshold

        # Daytime: branch on whether sun is in front of the window
        if sun_at_window:
            # Lux gate: if lux sensor shows low light, sun is blocked by obstacle
            if lux_is_low:
                return self._result(inputs.current_position, daytime_open_position, "sun_blocked_by_obstacle", sun_at_window)

            # High lux protection: direct sun glare → close
            if self.config.enable_high_lux_protection and inputs.high_lux_since is not None:
                if self._debounced(inputs.high_lux_since, inputs.now):
                    return self._result(inputs.current_position, 0, "direct_sun_high_lux", sun_at_window)

            # Heat protection: reduce opening during peak hours
            if (
                self.config.enable_heat_protection
                and not is_winter
                and self._hour_in_range(inputs.now.hour, self.config.heat_start_hour, self.config.heat_end_hour)
                and (inputs.temperature is None or inputs.temperature >= self.config.temp_threshold)
            ):
                return self._result(inputs.current_position, self.config.heat_position, "peak_heat_hours", sun_at_window)

            # Sun elevation tracking: adjust slat angle based on sun height
            if self.config.enable_sun_elevation_tracking:
                target = self._base_sun_target(inputs.sun_elevation, daytime_open_position)
                return self._result(inputs.current_position, target, "sun_elevation_tracking", sun_at_window)

            # Elevation tracking disabled — hold
            return DecisionResult(False, inputs.current_position, "sun_tracking_disabled", sun_at_window)

        # Sun not at window — open to let in daylight
        return self._result(inputs.current_position, daytime_open_position, "daytime_open", sun_at_window)

    def _result(
        self,
        current_position: int,
        target_position: int,
        reason: str,
        sun_at_window: bool,
    ) -> DecisionResult:
        target = max(self.config.min_position, min(100, int(target_position)))
        threshold = self.config.movement_threshold
        return DecisionResult(abs(target - current_position) >= threshold, target, reason, sun_at_window)

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
    def _base_sun_target(elevation: float, daytime_open_position: int) -> int:
        """Slat position when sun is directly at the window.

        0% = closed, daytime_open_position = most open (horizontal slats).
        Low elevation = direct eye-level glare → close more. Never opens
        further than the configured daytime_open_position ceiling.
        """
        if elevation < 10:
            return 0   # Very low sun — close completely
        if elevation < 25:
            return min(50, daytime_open_position)  # Low sun — half open
        return daytime_open_position                # High sun — open to ceiling
