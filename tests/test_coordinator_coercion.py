"""Tests for HaBlindsController._coerce_int/_coerce_float/_coerce_bool.

These tolerate legacy persisted config formats (selector labels like
"14:00" or "0 (Closed)", stringified numbers, etc.) so options forms
never crash on old data. They're static methods, called directly on the
class — no HomeAssistant instance needed.
"""

from __future__ import annotations

import unittest

import ha_stubs

ha_stubs.install()

from custom_components.ha_blinds.coordinator import HaBlindsController


class TestCoerceInt(unittest.TestCase):
    def test_int_passthrough(self) -> None:
        self.assertEqual(HaBlindsController._coerce_int(5, 0), 5)

    def test_bool_rejected_uses_fallback(self) -> None:
        """bool is a subclass of int in Python but is not a valid config value."""
        self.assertEqual(HaBlindsController._coerce_int(True, 3), 3)
        self.assertEqual(HaBlindsController._coerce_int(False, 3), 3)

    def test_float_truncates(self) -> None:
        self.assertEqual(HaBlindsController._coerce_int(5.9, 0), 5)

    def test_plain_numeric_string(self) -> None:
        self.assertEqual(HaBlindsController._coerce_int("42", 0), 42)

    def test_time_selector_string_uses_hour(self) -> None:
        self.assertEqual(HaBlindsController._coerce_int("14:00", 0), 14)

    def test_labeled_selector_string_uses_leading_number(self) -> None:
        self.assertEqual(HaBlindsController._coerce_int("0 (Closed)", 5), 0)
        self.assertEqual(HaBlindsController._coerce_int("100 (Privacy Mode)", 5), 100)

    def test_float_like_string(self) -> None:
        self.assertEqual(HaBlindsController._coerce_int("20.5", 0), 20)

    def test_garbage_string_uses_fallback(self) -> None:
        self.assertEqual(HaBlindsController._coerce_int("not-a-number", 7), 7)

    def test_none_uses_fallback(self) -> None:
        self.assertEqual(HaBlindsController._coerce_int(None, 7), 7)

    def test_unsupported_type_uses_fallback(self) -> None:
        self.assertEqual(HaBlindsController._coerce_int([1, 2], 7), 7)


class TestCoerceFloat(unittest.TestCase):
    def test_int_and_float_passthrough(self) -> None:
        self.assertEqual(HaBlindsController._coerce_float(5, 0.0), 5.0)
        self.assertEqual(HaBlindsController._coerce_float(5.5, 0.0), 5.5)

    def test_bool_rejected_uses_fallback(self) -> None:
        self.assertEqual(HaBlindsController._coerce_float(True, 1.5), 1.5)

    def test_numeric_string(self) -> None:
        self.assertEqual(HaBlindsController._coerce_float("24.5", 0.0), 24.5)

    def test_whitespace_stripped(self) -> None:
        self.assertEqual(HaBlindsController._coerce_float(" 24.5 ", 0.0), 24.5)

    def test_garbage_string_uses_fallback(self) -> None:
        self.assertEqual(HaBlindsController._coerce_float("hot", 18.0), 18.0)

    def test_none_uses_fallback(self) -> None:
        self.assertEqual(HaBlindsController._coerce_float(None, 18.0), 18.0)


class TestCoerceBool(unittest.TestCase):
    def test_bool_passthrough(self) -> None:
        self.assertTrue(HaBlindsController._coerce_bool(True, False))
        self.assertFalse(HaBlindsController._coerce_bool(False, True))

    def test_int_truthiness(self) -> None:
        self.assertFalse(HaBlindsController._coerce_bool(0, True))
        self.assertTrue(HaBlindsController._coerce_bool(1, False))
        self.assertTrue(HaBlindsController._coerce_bool(5, False))

    def test_truthy_strings(self) -> None:
        for value in ("1", "true", "True", "  TRUE  ", "yes", "on"):
            with self.subTest(value=value):
                self.assertTrue(HaBlindsController._coerce_bool(value, False))

    def test_falsy_strings(self) -> None:
        for value in ("0", "false", "False", "  FALSE  ", "no", "off"):
            with self.subTest(value=value):
                self.assertFalse(HaBlindsController._coerce_bool(value, True))

    def test_unrecognized_string_uses_fallback(self) -> None:
        self.assertTrue(HaBlindsController._coerce_bool("maybe", True))
        self.assertFalse(HaBlindsController._coerce_bool("maybe", False))

    def test_none_uses_fallback(self) -> None:
        self.assertTrue(HaBlindsController._coerce_bool(None, True))


if __name__ == "__main__":
    unittest.main()
