"""Tests for app.services.storage_service – covers persistence and error-handling paths."""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.models import LeadRequest, LeadResponse, StoredLead
from app.services.storage_service import (
    DEFAULT_LEADS_FILE,
    _get_leads_file,
    _update_jsonl,
    load_leads,
    save_lead,
    update_lead_outcome,
)


def _make_stored_lead(**kwargs) -> StoredLead:
    defaults = {
        "name": "João",
        "city": "Fortaleza",
        "monthly_bill": 450.0,
        "property_type": "casa",
        "goal": "reduzir conta",
        "score": 7,
        "urgency": "alta",
        "recommendation": "Lead promissor",
        "timestamp": "2024-01-01T00:00:00Z",
    }
    defaults.update(kwargs)
    return StoredLead(**defaults)


class StorageServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.leads_file = os.path.join(self.temp_dir.name, "leads.jsonl")
        self.env_patcher = patch.dict(os.environ, {"LEADS_FILE": self.leads_file})
        self.env_patcher.start()

    def tearDown(self) -> None:
        self.env_patcher.stop()
        self.temp_dir.cleanup()

    # --- _get_leads_file ---

    def test_get_leads_file_uses_env_var_when_set(self) -> None:
        result = _get_leads_file()
        self.assertEqual(result, Path(self.leads_file).expanduser().resolve())

    def test_get_leads_file_returns_default_when_env_not_set(self) -> None:
        env = {k: v for k, v in os.environ.items() if k != "LEADS_FILE"}
        with patch.dict(os.environ, env, clear=True):
            result = _get_leads_file()
        self.assertEqual(result, DEFAULT_LEADS_FILE)

    # --- save_lead / load_leads happy path ---

    def test_save_then_load_returns_same_lead(self) -> None:
        record = _make_stored_lead()
        save_lead(record)
        leads = load_leads()
        self.assertEqual(len(leads), 1)
        self.assertEqual(leads[0].name, "João")
        self.assertEqual(leads[0].score, 7)

    def test_save_multiple_leads_appends_each(self) -> None:
        for i in range(3):
            save_lead(_make_stored_lead(name=f"Lead{i}", score=i + 5))
        leads = load_leads()
        self.assertEqual(len(leads), 3)
        names = {l.name for l in leads}
        self.assertEqual(names, {"Lead0", "Lead1", "Lead2"})

    def test_save_creates_parent_dirs_automatically(self) -> None:
        nested = os.path.join(self.temp_dir.name, "a", "b", "c", "leads.jsonl")
        with patch.dict(os.environ, {"LEADS_FILE": nested}):
            save_lead(_make_stored_lead())
        self.assertTrue(os.path.exists(nested))

    # --- load_leads edge cases ---

    def test_load_returns_empty_list_when_file_missing(self) -> None:
        leads = load_leads()
        self.assertEqual(leads, [])

    def test_load_skips_malformed_json_lines(self) -> None:
        with open(self.leads_file, "w", encoding="utf-8") as f:
            f.write(_make_stored_lead().model_dump_json() + "\n")
            f.write("this is not valid json\n")
            f.write(_make_stored_lead(name="Second").model_dump_json() + "\n")
        leads = load_leads()
        self.assertEqual(len(leads), 2)

    def test_load_skips_empty_and_whitespace_lines(self) -> None:
        with open(self.leads_file, "w", encoding="utf-8") as f:
            f.write(_make_stored_lead().model_dump_json() + "\n")
            f.write("\n")
            f.write("   \n")
        leads = load_leads()
        self.assertEqual(len(leads), 1)

    def test_load_returns_empty_list_on_read_error(self) -> None:
        # Create a directory at the file path so open() raises IsADirectoryError
        os.makedirs(self.leads_file, exist_ok=True)
        leads = load_leads()
        self.assertEqual(leads, [])

    # --- save_lead error handling ---

    def test_save_handles_write_error_silently(self) -> None:
        # Create a file at the would-be parent directory so mkdir fails
        blocking = os.path.join(self.temp_dir.name, "blocking")
        with open(blocking, "w") as f:
            f.write("file")
        bad_path = Path(blocking) / "subdir" / "leads.jsonl"
        with patch("app.services.storage_service._get_leads_file", return_value=bad_path):
            # Must not raise
            save_lead(_make_stored_lead())

    # --- stored data integrity ---

    def test_stored_json_contains_all_fields(self) -> None:
        record = _make_stored_lead(score=9, urgency="alta", recommendation="Rápido!")
        save_lead(record)
        with open(self.leads_file, encoding="utf-8") as f:
            data = json.loads(f.readline())
        self.assertEqual(data["score"], 9)
        self.assertEqual(data["urgency"], "alta")
        self.assertEqual(data["recommendation"], "Rápido!")
        self.assertIn("timestamp", data)

    def test_from_qualification_factory_produces_stored_lead(self) -> None:
        request = LeadRequest(
            name="Maria",
            city="Natal",
            monthly_bill=600.0,
            property_type="casa",
            goal="reduzir conta",
        )
        response = LeadResponse(score=8, urgency="alta", recommendation="Contato!")
        stored = StoredLead.from_qualification(request, response, ai_raw_score=7, rule_delta=1)
        self.assertEqual(stored.name, "Maria")
        self.assertEqual(stored.score, 8)
        self.assertEqual(stored.ai_raw_score, 7)
        self.assertEqual(stored.rule_delta, 1)
        self.assertTrue(stored.timestamp.endswith("Z"))


class UpdateLeadOutcomeTests(unittest.TestCase):
    """Tests for _update_jsonl and update_lead_outcome."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.leads_file = os.path.join(self.temp_dir.name, "leads.jsonl")
        self.env_patcher = patch.dict(os.environ, {"LEADS_FILE": self.leads_file})
        self.env_patcher.start()

    def tearDown(self) -> None:
        self.env_patcher.stop()
        self.temp_dir.cleanup()

    def _save_and_get_id(self, **kwargs) -> str:
        record = _make_stored_lead(**kwargs)
        save_lead(record)
        return record.id

    def test_update_jsonl_updates_outcome(self) -> None:
        lead_id = self._save_and_get_id()
        result = _update_jsonl(lead_id, "closed", None)
        self.assertIsNotNone(result)
        self.assertEqual(result.outcome, "closed")

    def test_update_jsonl_updates_outcome_notes(self) -> None:
        lead_id = self._save_and_get_id()
        result = _update_jsonl(lead_id, "ghosted", "não atendeu")
        self.assertEqual(result.outcome_notes, "não atendeu")

    def test_update_jsonl_returns_none_for_missing_id(self) -> None:
        result = _update_jsonl("nonexistent-id", "closed", None)
        self.assertIsNone(result)

    def test_update_jsonl_persists_change_to_file(self) -> None:
        lead_id = self._save_and_get_id()
        _update_jsonl(lead_id, "closed", None)
        reloaded = load_leads()
        self.assertEqual(reloaded[0].outcome, "closed")

    def test_update_lead_outcome_delegates_to_jsonl(self) -> None:
        lead_id = self._save_and_get_id()
        result = update_lead_outcome(lead_id, "scheduled_visit", "agendou visita")
        self.assertIsNotNone(result)
        self.assertEqual(result.outcome, "scheduled_visit")

    def test_update_lead_outcome_returns_none_for_missing_id(self) -> None:
        result = update_lead_outcome("bad-id", "closed", None)
        self.assertIsNone(result)


class OrgIdFilterTests(unittest.TestCase):
    """Tests for load_leads(org_id=...) filtering in the JSONL backend."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.leads_file = os.path.join(self.temp_dir.name, "leads.jsonl")
        self.env_patcher = patch.dict(os.environ, {"LEADS_FILE": self.leads_file})
        self.env_patcher.start()

    def tearDown(self) -> None:
        self.env_patcher.stop()
        self.temp_dir.cleanup()

    def test_load_without_org_id_returns_all_leads(self) -> None:
        save_lead(_make_stored_lead(name="Org1"))
        save_lead(_make_stored_lead(name="Org2"))
        leads = load_leads()
        self.assertEqual(len(leads), 2)

    def test_load_with_org_id_filters_by_org(self) -> None:
        from app.models import StoredLead as SL
        r1 = _make_stored_lead(name="Seller-A")
        r1_with_org = r1.model_copy(update={"org_id": "seller-a@solar.com"})
        r2 = _make_stored_lead(name="Seller-B")
        r2_with_org = r2.model_copy(update={"org_id": "seller-b@solar.com"})
        save_lead(r1_with_org)
        save_lead(r2_with_org)

        leads = load_leads(org_id="seller-a@solar.com")
        self.assertEqual(len(leads), 1)
        self.assertEqual(leads[0].name, "Seller-A")

    def test_load_with_nonexistent_org_id_returns_empty(self) -> None:
        save_lead(_make_stored_lead())
        leads = load_leads(org_id="nobody@example.com")
        self.assertEqual(leads, [])


if __name__ == "__main__":
    unittest.main()
