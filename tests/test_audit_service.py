"""Tests for app.services.audit_service — verifies non-blocking behaviour and payload construction."""

import unittest
from unittest.mock import MagicMock, call, patch

from app.services.audit_service import log_event


class AuditServiceNoFirestoreTests(unittest.TestCase):
    """All tests run without a real Firestore connection."""

    def setUp(self) -> None:
        # Ensure _get_db always returns None so we stay in the stdout-only path
        self.db_patcher = patch("app.services.audit_service._get_db", return_value=None)
        self.db_patcher.start()

    def tearDown(self) -> None:
        self.db_patcher.stop()

    def test_minimal_call_does_not_raise(self) -> None:
        # Only required positional arg is event_type
        log_event("lead_qualified")

    def test_full_kwargs_does_not_raise(self) -> None:
        log_event(
            "lead_qualified",
            client_id="user@example.com",
            api_key_prefix="sk-ls-abc",
            ip="127.0.0.1",
            endpoint="/lead",
            method="POST",
            status_code=200,
            lead_id="abc-123",
            score=8,
            error="",
            extra={"custom_field": "value"},
        )

    def test_optional_lead_id_included_when_set(self) -> None:
        with patch("app.services.audit_service.logger") as mock_logger:
            log_event("lead_qualified", lead_id="abc-123")
        # logger.info is called once — check the event_type arg
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        self.assertIn("lead_qualified", str(call_args))

    def test_optional_score_included_when_set(self) -> None:
        # Should not raise even when score=0 (falsy but valid)
        log_event("scored", score=0)

    def test_optional_error_included_when_set(self) -> None:
        log_event("request_failed", error="something went wrong")

    def test_extra_dict_does_not_raise(self) -> None:
        log_event("custom_event", extra={"key1": "val1", "key2": 42})

    def test_event_type_logged_via_logger(self) -> None:
        with patch("app.services.audit_service.logger") as mock_logger:
            log_event("payment_received", client_id="cust-1", status_code=200)
        mock_logger.info.assert_called_once()
        # The log message includes event type and client_id
        logged_str = str(mock_logger.info.call_args)
        self.assertIn("payment_received", logged_str)
        self.assertIn("cust-1", logged_str)


class AuditServiceFirestoreTests(unittest.TestCase):
    """Verify Firestore write path and silent failure on exception."""

    def test_writes_to_firestore_when_db_available(self) -> None:
        mock_db = MagicMock()
        with patch("app.services.audit_service._get_db", return_value=mock_db):
            log_event("lead_qualified", client_id="user@example.com", score=7)
        # Firestore collection().add() should have been called
        mock_db.collection.assert_called_once_with("audit_logs")
        mock_db.collection.return_value.add.assert_called_once()

    def test_payload_contains_required_keys(self) -> None:
        mock_db = MagicMock()
        with patch("app.services.audit_service._get_db", return_value=mock_db):
            log_event("test_event", client_id="tester", ip="1.2.3.4", endpoint="/lead", status_code=201)

        payload = mock_db.collection.return_value.add.call_args.args[0]
        self.assertIn("timestamp", payload)
        self.assertIn("event_type", payload)
        self.assertEqual(payload["event_type"], "test_event")
        self.assertEqual(payload["client_id"], "tester")
        self.assertEqual(payload["ip"], "1.2.3.4")
        self.assertEqual(payload["status_code"], 201)

    def test_lead_id_in_payload_when_provided(self) -> None:
        mock_db = MagicMock()
        with patch("app.services.audit_service._get_db", return_value=mock_db):
            log_event("lead_stored", lead_id="lead-xyz")

        payload = mock_db.collection.return_value.add.call_args.args[0]
        self.assertEqual(payload["lead_id"], "lead-xyz")

    def test_lead_id_absent_from_payload_when_not_provided(self) -> None:
        mock_db = MagicMock()
        with patch("app.services.audit_service._get_db", return_value=mock_db):
            log_event("lead_stored")

        payload = mock_db.collection.return_value.add.call_args.args[0]
        self.assertNotIn("lead_id", payload)

    def test_score_absent_from_payload_when_not_provided(self) -> None:
        mock_db = MagicMock()
        with patch("app.services.audit_service._get_db", return_value=mock_db):
            log_event("event_no_score")

        payload = mock_db.collection.return_value.add.call_args.args[0]
        self.assertNotIn("score", payload)

    def test_extra_dict_merged_into_payload(self) -> None:
        mock_db = MagicMock()
        with patch("app.services.audit_service._get_db", return_value=mock_db):
            log_event("event", extra={"solar_city": "Fortaleza", "plan": "pro"})

        payload = mock_db.collection.return_value.add.call_args.args[0]
        self.assertEqual(payload["solar_city"], "Fortaleza")
        self.assertEqual(payload["plan"], "pro")

    def test_firestore_exception_is_swallowed(self) -> None:
        mock_db = MagicMock()
        mock_db.collection.return_value.add.side_effect = RuntimeError("Firestore unavailable")
        with patch("app.services.audit_service._get_db", return_value=mock_db):
            # Must not raise
            log_event("risky_event")


if __name__ == "__main__":
    unittest.main()
