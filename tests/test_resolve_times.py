import importlib.util
import unittest
from pathlib import Path

helper = Path(__file__).resolve().parents[1] / "skills/apple-calendar-followup/scripts/resolve_times.py"
spec = importlib.util.spec_from_file_location("followup_times", helper)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class TimeTests(unittest.TestCase):
    def test_parse_offset_rejects_invalid_and_unicode_digits(self):
        for value in ("", "+24:00", "+00:60", "+０１:００"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    module.parse_offset(value)

    def test_parse_offset_accepts_largest_valid_offset(self):
        self.assertEqual(str(module.parse_offset("+23:59")), "23:59:00")

    def test_shanghai_midnight_is_previous_utc_day(self):
        value = module.resolve("2026-10-20", "Asia/Shanghai", "2026-10-20T09:30")
        self.assertEqual(value["first_read_utc"], "2026-10-19T16:00:00+00:00")
        self.assertEqual(value["retry_utc"], "2026-10-20T01:30:00+00:00")

    def test_paris_offset_changes_between_midnight_and_retry(self):
        value = module.resolve("2026-10-25", "Europe/Paris", "2026-10-25T09:30")
        self.assertEqual(value["first_read_at"], "2026-10-25T00:00:00+02:00")
        self.assertEqual(value["retry_at"], "2026-10-25T09:30:00+01:00")

    def test_ambiguous_retry_needs_explicit_offset(self):
        with self.assertRaisesRegex(ValueError, "Ambiguous"):
            module.resolve("2026-10-25", "Europe/Paris", "2026-10-25T02:30")
        early = module.resolve("2026-10-25", "Europe/Paris", "2026-10-25T02:30+02:00")
        late = module.resolve("2026-10-25", "Europe/Paris", "2026-10-25T02:30+01:00")
        self.assertEqual(early["retry_utc"], "2026-10-25T00:30:00+00:00")
        self.assertEqual(late["retry_utc"], "2026-10-25T01:30:00+00:00")

    def test_nonexistent_retry_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Nonexistent"):
            module.resolve("2026-03-29", "Europe/Paris", "2026-03-29T02:30")

    def test_wrong_named_zone_offset_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "offset does not match"):
            module.resolve("2026-10-20", "Asia/Shanghai", "2026-10-20T09:30+02:00")

    def test_fallback_not_after_first_is_rejected(self):
        for retry in ("2026-10-19T23:30", "2026-10-20T00:00"):
            with self.subTest(retry=retry), self.assertRaisesRegex(ValueError, "later than"):
                module.resolve("2026-10-20", "Europe/Paris", retry)

    def test_nonexistent_midnight_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Nonexistent"):
            module.resolve("2011-12-30", "Pacific/Apia", "2011-12-31T09:30")

    def test_time_zone_and_date_are_explicit(self):
        with self.assertRaisesRegex(ValueError, "abbreviation"):
            module.resolve("2026-10-20", "CST", "2026-10-20T09:30")
        with self.assertRaisesRegex(ValueError, "YYYY-MM-DD"):
            module.resolve("20261020", "Europe/Paris", "2026-10-20T09:30")


if __name__ == "__main__":
    unittest.main()
