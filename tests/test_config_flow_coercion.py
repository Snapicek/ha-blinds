"""Tests for config_flow.py's pure coercion/normalization helpers.

These convert between UI selector formats (HH:MM dropdown strings,
"0 (Closed)" / "100 (Privacy Mode)" labels) and the plain ints/floats/bools
stored in the config entry, and tolerate malformed or legacy persisted
values so the options form never crashes when rendering
(`_show_schema_form` wraps schema building in a try/except precisely
because this has broken before). None of it needs a real HomeAssistant
instance — ha_stubs just lets config_flow.py's `voluptuous` /
`homeassistant.helpers.selector` imports resolve.
"""

from __future__ import annotations

import unittest

import ha_stubs

ha_stubs.install()

from custom_components.ha_blinds import config_flow as cf
from custom_components.ha_blinds.const import (
    CONF_EARLIEST_OPEN_HOUR,
    CONF_EARLIEST_OPEN_MINUTE,
    CONF_HEAT_END_HOUR,
    CONF_HEAT_START_HOUR,
    CONF_NIGHT_CLOSE_POSITION,
    CONF_SUMMER_PRIVACY_HOUR,
    CONF_WINTER_PRIVACY_HOUR,
    DEFAULTS,
)


def _defaults_with(**overrides):
    return {**DEFAULTS, **overrides}


class TestCoerceHourValue(unittest.TestCase):
    def test_int_in_range(self) -> None:
        self.assertEqual(cf._coerce_hour_value(14), 14)

    def test_hhmm_string(self) -> None:
        self.assertEqual(cf._coerce_hour_value("14:00"), 14)

    def test_bare_hour_string(self) -> None:
        self.assertEqual(cf._coerce_hour_value("07"), 7)

    def test_out_of_range_raises(self) -> None:
        with self.assertRaises(ValueError):
            cf._coerce_hour_value(24)
        with self.assertRaises(ValueError):
            cf._coerce_hour_value(-1)

    def test_non_numeric_string_raises(self) -> None:
        with self.assertRaises(ValueError):
            cf._coerce_hour_value("not-a-time")

    def test_unsupported_type_raises(self) -> None:
        with self.assertRaises(ValueError):
            cf._coerce_hour_value(None)
        with self.assertRaises(ValueError):
            cf._coerce_hour_value(14.0)

    def test_bool_is_accepted_as_int_quirk(self) -> None:
        """bool passes isinstance(value, int) in Python, so this slips through
        as hour 1 — unlike coordinator._coerce_int, which explicitly rejects
        bools. Pinning down current behavior, not endorsing it."""
        self.assertEqual(cf._coerce_hour_value(True), 1)


class TestCoerceNightClosePosition(unittest.TestCase):
    def test_valid_ints(self) -> None:
        self.assertEqual(cf._coerce_night_close_position(0), 0)
        self.assertEqual(cf._coerce_night_close_position(100), 100)

    def test_invalid_int_raises(self) -> None:
        with self.assertRaises(ValueError):
            cf._coerce_night_close_position(50)

    def test_labeled_strings(self) -> None:
        self.assertEqual(cf._coerce_night_close_position("0 (Closed)"), 0)
        self.assertEqual(cf._coerce_night_close_position("100 (Privacy Mode)"), 100)

    def test_invalid_labeled_string_raises(self) -> None:
        with self.assertRaises(ValueError):
            cf._coerce_night_close_position("50 (Half)")

    def test_unsupported_type_raises(self) -> None:
        with self.assertRaises(ValueError):
            cf._coerce_night_close_position(None)


class TestHourDefaultLabel(unittest.TestCase):
    def test_valid_value_formats_as_label(self) -> None:
        self.assertEqual(cf._hour_default_label(7, 0), "07:00")
        self.assertEqual(cf._hour_default_label("14:00", 0), "14:00")

    def test_invalid_value_falls_back(self) -> None:
        self.assertEqual(cf._hour_default_label("garbage", 10), "10:00")
        self.assertEqual(cf._hour_default_label(30, 10), "10:00")


class TestNightPositionDefaultLabel(unittest.TestCase):
    def test_valid_values(self) -> None:
        self.assertEqual(cf._night_position_default_label(0, 100), "0 (Closed)")
        self.assertEqual(cf._night_position_default_label(100, 0), "100 (Privacy Mode)")

    def test_invalid_value_falls_back(self) -> None:
        self.assertEqual(cf._night_position_default_label(50, 0), "0 (Closed)")
        self.assertEqual(cf._night_position_default_label(50, 100), "100 (Privacy Mode)")


class TestCoerceIntDefault(unittest.TestCase):
    def test_passthrough_and_legacy_strings(self) -> None:
        self.assertEqual(cf._coerce_int_default(35000, 0), 35000)
        self.assertEqual(cf._coerce_int_default("35000", 0), 35000)
        self.assertEqual(cf._coerce_int_default("35000 lux", 0), 35000)
        self.assertEqual(cf._coerce_int_default("14:00", 0), 14)

    def test_bool_and_garbage_use_fallback(self) -> None:
        self.assertEqual(cf._coerce_int_default(True, 9), 9)
        self.assertEqual(cf._coerce_int_default("nope", 9), 9)
        self.assertEqual(cf._coerce_int_default(None, 9), 9)


class TestCoerceFloatDefault(unittest.TestCase):
    def test_passthrough_and_string(self) -> None:
        self.assertEqual(cf._coerce_float_default(24, 0.0), 24.0)
        self.assertEqual(cf._coerce_float_default("22.5", 0.0), 22.5)

    def test_bool_and_garbage_use_fallback(self) -> None:
        self.assertEqual(cf._coerce_float_default(True, 18.0), 18.0)
        self.assertEqual(cf._coerce_float_default("warm", 18.0), 18.0)


class TestCoerceBoolDefault(unittest.TestCase):
    def test_bool_and_int(self) -> None:
        self.assertTrue(cf._coerce_bool_default(True, False))
        self.assertTrue(cf._coerce_bool_default(1, False))
        self.assertFalse(cf._coerce_bool_default(0, True))

    def test_legacy_strings(self) -> None:
        self.assertTrue(cf._coerce_bool_default("yes", False))
        self.assertFalse(cf._coerce_bool_default("off", True))

    def test_unrecognized_uses_fallback(self) -> None:
        self.assertTrue(cf._coerce_bool_default("maybe", True))


class TestConvertTimeInputs(unittest.TestCase):
    def test_converts_hh_mm_hour_keys(self) -> None:
        user_input = {CONF_HEAT_START_HOUR: "09:00", CONF_HEAT_END_HOUR: "17:00"}
        cf._convert_time_inputs(user_input)
        self.assertEqual(user_input[CONF_HEAT_START_HOUR], 9)
        self.assertEqual(user_input[CONF_HEAT_END_HOUR], 17)

    def test_missing_keys_are_skipped(self) -> None:
        user_input = {CONF_WINTER_PRIVACY_HOUR: "16:00"}
        cf._convert_time_inputs(user_input)
        self.assertEqual(user_input, {CONF_WINTER_PRIVACY_HOUR: 16})
        self.assertNotIn(CONF_SUMMER_PRIVACY_HOUR, user_input)

    def test_earliest_open_hh_mm_splits_into_hour_and_minute(self) -> None:
        user_input = {CONF_EARLIEST_OPEN_HOUR: "07:30"}
        cf._convert_time_inputs(user_input)
        self.assertEqual(user_input[CONF_EARLIEST_OPEN_HOUR], 7)
        self.assertEqual(user_input[CONF_EARLIEST_OPEN_MINUTE], 30)

    def test_earliest_open_plain_hour_does_not_touch_minute(self) -> None:
        user_input = {CONF_EARLIEST_OPEN_HOUR: 9}
        cf._convert_time_inputs(user_input)
        self.assertEqual(user_input[CONF_EARLIEST_OPEN_HOUR], 9)
        self.assertNotIn(CONF_EARLIEST_OPEN_MINUTE, user_input)


class TestConvertNightClosePosition(unittest.TestCase):
    def test_converts_labeled_string(self) -> None:
        user_input = {CONF_NIGHT_CLOSE_POSITION: "100 (Privacy Mode)"}
        cf._convert_night_close_position(user_input)
        self.assertEqual(user_input[CONF_NIGHT_CLOSE_POSITION], 100)

    def test_missing_key_is_skipped(self) -> None:
        user_input = {}
        cf._convert_night_close_position(user_input)
        self.assertEqual(user_input, {})


class TestSanitizeOptionDefaults(unittest.TestCase):
    def test_all_defaults_pass_through_unchanged(self) -> None:
        sanitized = cf._sanitize_option_defaults(_defaults_with())
        self.assertEqual(sanitized[CONF_HEAT_START_HOUR], DEFAULTS[CONF_HEAT_START_HOUR])
        self.assertEqual(sanitized[CONF_NIGHT_CLOSE_POSITION], DEFAULTS[CONF_NIGHT_CLOSE_POSITION])

    def test_legacy_int_string_with_units(self) -> None:
        from custom_components.ha_blinds.const import CONF_LUX_CLOSE_SUMMER

        sanitized = cf._sanitize_option_defaults(_defaults_with(**{CONF_LUX_CLOSE_SUMMER: "35000 lux"}))
        self.assertEqual(sanitized[CONF_LUX_CLOSE_SUMMER], 35000)

    def test_legacy_temp_threshold_string(self) -> None:
        from custom_components.ha_blinds.const import CONF_TEMP_THRESHOLD

        sanitized = cf._sanitize_option_defaults(_defaults_with(**{CONF_TEMP_THRESHOLD: "22.5"}))
        self.assertEqual(sanitized[CONF_TEMP_THRESHOLD], 22.5)

    def test_legacy_bool_string(self) -> None:
        from custom_components.ha_blinds.const import CONF_ENABLE_PRIVACY_HOUR

        sanitized = cf._sanitize_option_defaults(_defaults_with(**{CONF_ENABLE_PRIVACY_HOUR: "no"}))
        self.assertFalse(sanitized[CONF_ENABLE_PRIVACY_HOUR])

    def test_hour_selector_string_normalized(self) -> None:
        sanitized = cf._sanitize_option_defaults(_defaults_with(**{CONF_HEAT_START_HOUR: "09:00"}))
        self.assertEqual(sanitized[CONF_HEAT_START_HOUR], 9)

    def test_garbage_hour_falls_back_to_hard_default(self) -> None:
        sanitized = cf._sanitize_option_defaults(_defaults_with(**{CONF_HEAT_START_HOUR: "not-a-time"}))
        self.assertEqual(sanitized[CONF_HEAT_START_HOUR], DEFAULTS[CONF_HEAT_START_HOUR])

    def test_out_of_range_hour_falls_back_to_hard_default(self) -> None:
        sanitized = cf._sanitize_option_defaults(_defaults_with(**{CONF_WINTER_PRIVACY_HOUR: 27}))
        self.assertEqual(sanitized[CONF_WINTER_PRIVACY_HOUR], DEFAULTS[CONF_WINTER_PRIVACY_HOUR])

    def test_night_close_position_legacy_label(self) -> None:
        sanitized = cf._sanitize_option_defaults(_defaults_with(**{CONF_NIGHT_CLOSE_POSITION: "100 (Privacy Mode)"}))
        self.assertEqual(sanitized[CONF_NIGHT_CLOSE_POSITION], 100)

    def test_night_close_position_invalid_falls_back(self) -> None:
        sanitized = cf._sanitize_option_defaults(_defaults_with(**{CONF_NIGHT_CLOSE_POSITION: 42}))
        self.assertEqual(sanitized[CONF_NIGHT_CLOSE_POSITION], DEFAULTS[CONF_NIGHT_CLOSE_POSITION])

    def test_missing_keys_fall_back_to_hard_defaults(self) -> None:
        """A partial dict (not pre-merged with DEFAULTS) must not crash."""
        sanitized = cf._sanitize_option_defaults({CONF_HEAT_START_HOUR: "09:00"})
        self.assertEqual(sanitized[CONF_HEAT_END_HOUR], DEFAULTS[CONF_HEAT_END_HOUR])
        self.assertEqual(sanitized[CONF_NIGHT_CLOSE_POSITION], DEFAULTS[CONF_NIGHT_CLOSE_POSITION])


if __name__ == "__main__":
    unittest.main()
