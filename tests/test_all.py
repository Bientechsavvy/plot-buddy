import os, re, sys, unittest
from datetime import date
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "api"))
import planner, guard  # noqa: E402


def plan(d, **kw):
    return planner.make_plan({"space": "bucket", **kw}, today=date.fromisoformat(d))


class PlannerTests(unittest.TestCase):
    def test_october_only_leafy_greens(self):
        self.assertEqual(plan("2026-10-09")["plant_now"], ["leafy_greens"])

    def test_november_dry_season_vegetables(self):
        self.assertIn("tomato", plan("2026-11-15")["plant_now"])

    def test_may_includes_okra(self):
        self.assertIn("okra", plan("2026-05-10")["plant_now"])

    def test_max_two_planting_tasks(self):
        self.assertLessEqual(len(plan("2026-05-10")["tasks"]), 2)

    def test_old_planting_may_be_ready(self):
        p = plan("2026-10-09", already_planted=[{"crop": "okra", "date": "2026-08-01"}])
        self.assertTrue(any("may be ready" in t["action"] for t in p["tasks"]))

    def test_young_planting_gets_check(self):
        p = plan("2026-10-09", already_planted=[{"crop": "okra", "date": "2026-10-01"}])
        self.assertTrue(any("day 8" in t["action"] for t in p["tasks"]))

    def test_bad_space_defaults_to_bucket(self):
        self.assertEqual(plan("2026-10-09", space="moon")["space"], "bucket")

    def test_bad_date_raises(self):
        with self.assertRaises(ValueError):
            plan("2026-10-09", already_planted=[{"crop": "okra", "date": "yesterday"}])

    def test_every_crop_has_sources_and_is_unverified(self):
        for c in planner.load_rules()["crops"]:
            self.assertFalse(c["verified"])
            for w in c["windows"]:
                self.assertTrue(w["source"].startswith("http"))

    def test_where_phrases_read_correctly(self):
        self.assertIn("in a bucket", plan("2026-10-10", space="bucket")["card_text"])
        self.assertIn("in a grow bag", plan("2026-10-10", space="bag")["card_text"])
        self.assertIn("on your balcony", plan("2026-10-10", space="balcony")["card_text"])
        self.assertNotIn("in your balcony", plan("2026-10-10", space="balcony")["card_text"])

    def test_low_confidence_note_only_when_shown(self):
        self.assertIn("low-confidence", plan("2026-10-10")["card_text"])        # greens are on the card
        self.assertNotIn("low-confidence", plan("2026-05-12", space="backyard")["card_text"])  # okra + tomato shown

    def test_sources_only_for_shown_crops(self):
        p = plan("2026-05-12", space="backyard")
        self.assertFalse(any("hedang" in s for s in p["sources"]))

    def test_card_has_no_money(self):
        self.assertFalse(guard.MONEY.search(plan("2026-10-09")["card_text"]))

    def test_ui_crop_ids_match_rules(self):
        with open(os.path.join(os.path.dirname(__file__), "..", "web", "index.html"), encoding="utf-8") as f:
            html = f.read()
        ui = set(re.findall(r'<option value="(\w+)">', html)) - set(planner.SPACES) - {"en", "pidgin"}
        self.assertEqual(ui, {c["id"] for c in planner.load_rules()["crops"]})


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.p = plan("2026-10-09")

    def test_accepts_faithful_text(self):
        self.assertTrue(guard.check("Put the phone down and go outside for about 20 minutes. "
                                    "Plant leafy greens in your bucket. Check back in 7 days.", self.p))

    def test_rejects_invented_number(self):
        self.assertFalse(guard.check("Plant 500 seeds today for 20 minutes. Check back in 7 days.", self.p))

    def test_rejects_money(self):
        self.assertFalse(guard.check("Seeds cost 20 naira. Check back in 7 days.", self.p))

    def test_rejects_other_crop(self):
        self.assertFalse(guard.check("Plant maize for 20 minutes. Check back in 7 days.", self.p))

    def test_rejects_empty_and_long(self):
        self.assertFalse(guard.check("", self.p))
        self.assertFalse(guard.check("a" * 1000, self.p))


if __name__ == "__main__":
    unittest.main()
