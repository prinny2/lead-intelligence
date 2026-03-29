import unittest
from unittest.mock import MagicMock, patch

from app.auth import (
    ClientInfo,
    _verify_firebase_token,
    get_api_key_for_firebase_token,
    link_google_account,
)


def _make_doc(data: dict):
    """Create a mock Firestore document snapshot."""
    doc = MagicMock()
    doc.to_dict.return_value = data
    doc.reference = MagicMock()
    return doc


class TestVerifyFirebaseToken(unittest.TestCase):
    """Tests for _verify_firebase_token with google_uid fallback."""

    @patch("app.auth._get_firestore")
    @patch("firebase_admin.auth", create=True)
    @patch("firebase_admin._apps", {"[DEFAULT]": True})
    def test_returns_client_info_for_email_match(self, mock_fb_auth, mock_fs):
        mock_fb_auth.verify_id_token.return_value = {
            "uid": "u1", "email": "a@b.com", "name": "Ana",
        }
        doc = _make_doc({"status": "active", "tier": "pro", "api_key": "ls_key123456789"})
        db = MagicMock()
        db.collection.return_value.where.return_value.limit.return_value.get.return_value = [doc]
        mock_fs.return_value = db

        result = _verify_firebase_token("tok")
        self.assertIsNotNone(result)
        self.assertEqual(result.email, "a@b.com")
        self.assertEqual(result.tier, "pro")
        self.assertTrue(result.api_key_prefix.endswith("..."))

    @patch("app.auth._get_firestore")
    @patch("firebase_admin.auth", create=True)
    @patch("firebase_admin._apps", {"[DEFAULT]": True})
    def test_falls_back_to_google_uid_when_email_not_found(self, mock_fb_auth, mock_fs):
        mock_fb_auth.verify_id_token.return_value = {
            "uid": "u1", "email": "a@b.com", "name": "Ana",
        }
        doc_uid = _make_doc({"status": "active", "tier": "starter", "api_key": "ls_uid_key12345"})
        db = MagicMock()

        email_q = MagicMock()
        email_q.where.return_value.limit.return_value.get.return_value = []
        uid_q = MagicMock()
        uid_q.where.return_value.limit.return_value.get.return_value = [doc_uid]

        def where_side_effect(field, op, value):
            if field == "email":
                return email_q.where.return_value
            return uid_q.where.return_value

        db.collection.return_value.where.side_effect = where_side_effect
        mock_fs.return_value = db

        result = _verify_firebase_token("tok")
        self.assertIsNotNone(result)
        self.assertEqual(result.tier, "starter")

    @patch("app.auth._get_firestore")
    @patch("firebase_admin.auth", create=True)
    @patch("firebase_admin._apps", {"[DEFAULT]": True})
    def test_returns_free_tier_when_no_firestore(self, mock_fb_auth, mock_fs):
        mock_fb_auth.verify_id_token.return_value = {
            "uid": "u1", "email": "a@b.com", "name": "Ana",
        }
        mock_fs.return_value = None

        result = _verify_firebase_token("tok")
        self.assertIsNotNone(result)
        self.assertEqual(result.tier, "free")
        self.assertEqual(result.api_key_prefix, "firebase")

    @patch("firebase_admin._apps", {})
    def test_returns_none_when_no_firebase_apps(self):
        result = _verify_firebase_token("tok")
        self.assertIsNone(result)

    @patch("firebase_admin.auth", create=True)
    @patch("firebase_admin._apps", {"[DEFAULT]": True})
    def test_returns_none_on_invalid_token(self, mock_fb_auth):
        mock_fb_auth.verify_id_token.side_effect = Exception("bad token")
        result = _verify_firebase_token("bad")
        self.assertIsNone(result)


class TestLinkGoogleAccount(unittest.TestCase):
    """Tests for link_google_account()."""

    @patch("firebase_admin._apps", {})
    def test_returns_false_when_no_firebase_apps(self):
        result = link_google_account("tok", "key123")
        self.assertFalse(result)

    @patch("app.auth._get_firestore")
    @patch("firebase_admin.auth", create=True)
    @patch("firebase_admin._apps", {"[DEFAULT]": True})
    def test_returns_false_when_no_firestore(self, mock_fb_auth, mock_fs):
        mock_fb_auth.verify_id_token.return_value = {"uid": "u1"}
        mock_fs.return_value = None
        result = link_google_account("tok", "key123")
        self.assertFalse(result)

    @patch("app.auth._get_firestore")
    @patch("firebase_admin.auth", create=True)
    @patch("firebase_admin._apps", {"[DEFAULT]": True})
    def test_returns_false_when_no_matching_doc(self, mock_fb_auth, mock_fs):
        mock_fb_auth.verify_id_token.return_value = {"uid": "u1"}
        db = MagicMock()
        db.collection.return_value.where.return_value.limit.return_value.get.return_value = []
        mock_fs.return_value = db
        result = link_google_account("tok", "key123")
        self.assertFalse(result)

    @patch("app.auth._get_firestore")
    @patch("firebase_admin.auth", create=True)
    @patch("firebase_admin._apps", {"[DEFAULT]": True})
    def test_updates_google_uid_on_success(self, mock_fb_auth, mock_fs):
        mock_fb_auth.verify_id_token.return_value = {"uid": "u1"}
        doc = _make_doc({"api_key": "key123"})
        db = MagicMock()
        db.collection.return_value.where.return_value.limit.return_value.get.return_value = [doc]
        mock_fs.return_value = db

        result = link_google_account("tok", "key123")
        self.assertTrue(result)
        doc.reference.update.assert_called_once_with({"google_uid": "u1"})

    @patch("firebase_admin.auth", create=True)
    @patch("firebase_admin._apps", {"[DEFAULT]": True})
    def test_returns_false_on_exception(self, mock_fb_auth):
        mock_fb_auth.verify_id_token.side_effect = Exception("bad token")
        result = link_google_account("bad", "key123")
        self.assertFalse(result)


class TestGetApiKeyForFirebaseToken(unittest.TestCase):
    """Tests for get_api_key_for_firebase_token()."""

    @patch("firebase_admin._apps", {})
    def test_returns_none_when_no_firebase_apps(self):
        result = get_api_key_for_firebase_token("tok")
        self.assertIsNone(result)

    @patch("app.auth._get_firestore")
    @patch("firebase_admin.auth", create=True)
    @patch("firebase_admin._apps", {"[DEFAULT]": True})
    def test_returns_none_when_no_firestore(self, mock_fb_auth, mock_fs):
        mock_fb_auth.verify_id_token.return_value = {"uid": "u1", "email": "a@b.com"}
        mock_fs.return_value = None
        result = get_api_key_for_firebase_token("tok")
        self.assertIsNone(result)

    @patch("app.auth._get_firestore")
    @patch("firebase_admin.auth", create=True)
    @patch("firebase_admin._apps", {"[DEFAULT]": True})
    def test_returns_key_by_email(self, mock_fb_auth, mock_fs):
        mock_fb_auth.verify_id_token.return_value = {"uid": "u1", "email": "a@b.com"}
        doc = _make_doc({"api_key": "ls_test_key_123", "status": "active"})
        db = MagicMock()
        db.collection.return_value.where.return_value.where.return_value.limit.return_value.get.return_value = [doc]
        mock_fs.return_value = db

        result = get_api_key_for_firebase_token("tok")
        self.assertEqual(result, "ls_test_key_123")

    @patch("app.auth._get_firestore")
    @patch("firebase_admin.auth", create=True)
    @patch("firebase_admin._apps", {"[DEFAULT]": True})
    def test_falls_back_to_google_uid(self, mock_fb_auth, mock_fs):
        mock_fb_auth.verify_id_token.return_value = {"uid": "u1", "email": "a@b.com"}

        doc = _make_doc({"api_key": "ls_uid_key_456", "status": "active"})
        db = MagicMock()
        call_count = [0]

        def get_side_effect():
            call_count[0] += 1
            if call_count[0] == 1:
                return []  # email lookup
            return [doc]  # uid lookup

        db.collection.return_value.where.return_value.where.return_value.limit.return_value.get.side_effect = get_side_effect
        mock_fs.return_value = db

        result = get_api_key_for_firebase_token("tok")
        self.assertEqual(result, "ls_uid_key_456")

    @patch("app.auth._get_firestore")
    @patch("firebase_admin.auth", create=True)
    @patch("firebase_admin._apps", {"[DEFAULT]": True})
    def test_returns_none_when_no_match(self, mock_fb_auth, mock_fs):
        mock_fb_auth.verify_id_token.return_value = {"uid": "u1", "email": "a@b.com"}
        db = MagicMock()
        db.collection.return_value.where.return_value.where.return_value.limit.return_value.get.return_value = []
        mock_fs.return_value = db

        result = get_api_key_for_firebase_token("tok")
        self.assertIsNone(result)

    @patch("firebase_admin.auth", create=True)
    @patch("firebase_admin._apps", {"[DEFAULT]": True})
    def test_returns_none_on_exception(self, mock_fb_auth):
        mock_fb_auth.verify_id_token.side_effect = Exception("invalid token")
        result = get_api_key_for_firebase_token("tok")
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
