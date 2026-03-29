"""Tests for app.services.rate_limit_service — focuses on the in-memory fallback path."""

import os
import unittest
from unittest.mock import patch

import app.services.rate_limit_service as rls


def _clear_mem_store() -> None:
    """Reset the module-level in-memory store between tests."""
    rls._mem_store.clear()


class CheckMemoryTests(unittest.TestCase):
    """Direct tests of _check_memory (no Redis / Firestore needed)."""

    def setUp(self) -> None:
        _clear_mem_store()

    def tearDown(self) -> None:
        _clear_mem_store()

    def test_first_request_is_allowed(self) -> None:
        self.assertTrue(rls._check_memory("client-1", limit=10))

    def test_requests_within_limit_are_allowed(self) -> None:
        for _ in range(5):
            result = rls._check_memory("client-2", limit=10)
            self.assertTrue(result)

    def test_request_exactly_at_limit_is_denied(self) -> None:
        for _ in range(5):
            rls._check_memory("client-3", limit=5)
        # 6th request should be denied
        self.assertFalse(rls._check_memory("client-3", limit=5))

    def test_different_keys_are_independent(self) -> None:
        for _ in range(5):
            rls._check_memory("key-a", limit=5)
        # key-a is at limit but key-b should still be allowed
        self.assertFalse(rls._check_memory("key-a", limit=5))
        self.assertTrue(rls._check_memory("key-b", limit=5))

    def test_expired_hits_are_pruned_and_allow_new_request(self) -> None:
        """Simulate old hits that fall outside the sliding window."""
        import time
        key = "expire-test"
        # Manually insert old timestamps well outside the 60s window
        rls._mem_store[key] = [time.monotonic() - 120] * 5  # 5 hits from 2 min ago
        # All old hits should be pruned; new request should be allowed (limit=5)
        self.assertTrue(rls._check_memory(key, limit=5, window_seconds=60))

    def test_unexpired_hits_block_new_request(self) -> None:
        import time
        key = "block-test"
        # 5 very recent hits
        rls._mem_store[key] = [time.monotonic() - 1] * 5
        self.assertFalse(rls._check_memory(key, limit=5, window_seconds=60))


class IsAllowedInMemoryTests(unittest.TestCase):
    """Test is_allowed() using the in-memory fallback (Redis + Firestore patched out)."""

    def setUp(self) -> None:
        _clear_mem_store()
        # Force in-memory path by returning None from Redis and no-Firestore DB
        self._redis_patcher = patch.object(rls, "_check_redis", return_value=None)
        self._db_patcher = patch("app.services.rate_limit_service._get_db", return_value=None)
        self._redis_patcher.start()
        self._db_patcher.start()

    def tearDown(self) -> None:
        self._redis_patcher.stop()
        self._db_patcher.stop()
        _clear_mem_store()

    def test_free_tier_allows_up_to_10_requests(self) -> None:
        for i in range(10):
            self.assertTrue(rls.is_allowed("free-user", tier="free"), f"Request {i+1} should be allowed")
        self.assertFalse(rls.is_allowed("free-user", tier="free"), "11th request should be denied")

    def test_demo_tier_allows_up_to_5_requests(self) -> None:
        for i in range(5):
            self.assertTrue(rls.is_allowed("demo-ip", tier="demo"), f"Request {i+1} should be allowed")
        self.assertFalse(rls.is_allowed("demo-ip", tier="demo"), "6th request should be denied")

    def test_pro_tier_allows_more_requests_than_free(self) -> None:
        # Just verify pro limit (100) > free limit (10)
        for _ in range(10):
            rls.is_allowed("pro-user", tier="pro")
        # After 10 requests, pro tier should still be allowed (limit is 100)
        self.assertTrue(rls.is_allowed("pro-user", tier="pro"))

    def test_unknown_tier_defaults_to_free_limit(self) -> None:
        for _ in range(10):
            rls.is_allowed("unknown-user", tier="nonexistent")
        # 11th request should be denied (defaulted to free=10)
        self.assertFalse(rls.is_allowed("unknown-user", tier="nonexistent"))

    def test_different_keys_tracked_separately(self) -> None:
        for _ in range(10):
            rls.is_allowed("user-a", tier="free")
        # user-a at limit, user-b should still be fine
        self.assertFalse(rls.is_allowed("user-a", tier="free"))
        self.assertTrue(rls.is_allowed("user-b", tier="free"))


class TierLimitsTests(unittest.TestCase):
    """Verify the TIER_LIMITS constants are correct."""

    def test_free_tier_limit_is_10(self) -> None:
        self.assertEqual(rls.TIER_LIMITS["free"], 10)

    def test_pro_tier_limit_is_100(self) -> None:
        self.assertEqual(rls.TIER_LIMITS["pro"], 100)

    def test_enterprise_tier_limit_is_1000(self) -> None:
        self.assertEqual(rls.TIER_LIMITS["enterprise"], 1000)

    def test_demo_tier_limit_is_5(self) -> None:
        self.assertEqual(rls.TIER_LIMITS["demo"], 5)


class RedisClientTests(unittest.TestCase):
    """Test _redis_client() early-return paths (no real Redis needed)."""

    def test_redis_client_returns_none_without_redis_url(self) -> None:
        env = {k: v for k, v in os.environ.items() if k != "REDIS_URL"}
        with patch.dict(os.environ, env, clear=True):
            result = rls._redis_client()
        self.assertIsNone(result)

    def test_check_redis_returns_none_when_no_redis_url(self) -> None:
        """When REDIS_URL is absent, _check_redis returns None (sentinel for fallthrough)."""
        env = {k: v for k, v in os.environ.items() if k != "REDIS_URL"}
        with patch.dict(os.environ, env, clear=True):
            result = rls._check_redis("key", limit=5)
        self.assertIsNone(result)


class RedisPathTests(unittest.TestCase):
    """Test that Redis path is used when _check_redis returns a boolean."""

    def setUp(self) -> None:
        _clear_mem_store()

    def tearDown(self) -> None:
        _clear_mem_store()

    def test_redis_allowed_result_bypasses_firestore(self) -> None:
        """When Redis returns True, Firestore/memory should not be consulted."""
        with patch.object(rls, "_check_redis", return_value=True) as mock_redis:
            with patch("app.services.rate_limit_service._check_firestore") as mock_fs:
                result = rls.is_allowed("user", tier="free")
        self.assertTrue(result)
        mock_fs.assert_not_called()

    def test_redis_denied_result_bypasses_firestore(self) -> None:
        """When Redis returns False, Firestore/memory should not be consulted."""
        with patch.object(rls, "_check_redis", return_value=False):
            with patch("app.services.rate_limit_service._check_firestore") as mock_fs:
                result = rls.is_allowed("user", tier="free")
        self.assertFalse(result)
        mock_fs.assert_not_called()

    def test_redis_none_falls_through_to_firestore(self) -> None:
        """When Redis returns None (sentinel), Firestore path should be used."""
        with patch.object(rls, "_check_redis", return_value=None):
            with patch("app.services.rate_limit_service._check_firestore", return_value=True) as mock_fs:
                result = rls.is_allowed("user", tier="free")
        self.assertTrue(result)
        mock_fs.assert_called_once()


if __name__ == "__main__":
    unittest.main()
