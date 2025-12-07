from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient


class AuthSecurityTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    # --- JWT refresh / logout edge cases ---

    def test_refresh_with_invalid_token_is_rejected(self):
        resp = self.client.post(
            "/api/auth/refresh/",
            {"refresh": "bogus-token"},
            format="json",
        )
        self.assertIn(resp.status_code, (status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED))

    def test_refresh_without_token_is_rejected(self):
        resp = self.client.post(
            "/api/auth/refresh/",
            {},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    # --- Admin IP whitelist ---

    @override_settings(ADMIN_ENABLED=False)
    def test_admin_disabled_returns_403(self):
        resp = self.client.get("/admin/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    @override_settings(ADMIN_ENABLED=True, ADMIN_IP_WHITELIST=["1.2.3.4"])
    def test_admin_rejects_non_whitelisted_ip(self):
        resp = self.client.get("/admin/", REMOTE_ADDR="5.6.7.8")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    @override_settings(ADMIN_ENABLED=True, ADMIN_IP_WHITELIST=["1.2.3.4"])
    def test_admin_allows_whitelisted_ip(self):
        resp = self.client.get("/admin/", REMOTE_ADDR="1.2.3.4")
        self.assertIn(resp.status_code, (status.HTTP_200_OK, status.HTTP_302_FOUND))

    # --- CORS ---

    @override_settings(CORS_ALLOWED_ORIGINS=["http://allowed.test"])
    def test_cors_allows_configured_origin(self):
        resp = self.client.get("/api/auth/login/", HTTP_ORIGIN="http://allowed.test")
        self.assertEqual(resp.get("Access-Control-Allow-Origin"), "http://allowed.test")

    @override_settings(CORS_ALLOWED_ORIGINS=["http://allowed.test"])
    def test_cors_blocks_unlisted_origin(self):
        resp = self.client.get("/api/auth/login/", HTTP_ORIGIN="http://bad.test")
        self.assertIsNone(resp.get("Access-Control-Allow-Origin"))

    # --- SSL redirect ---

    @override_settings(SECURE_SSL_REDIRECT=True)
    def test_http_requests_redirect_to_https_when_ssl_redirect_on(self):
        resp = self.client.get("/api/auth/login/", follow=False)
        self.assertIn(resp.status_code, (status.HTTP_301_MOVED_PERMANENTLY, status.HTTP_302_FOUND))
        self.assertTrue(resp["Location"].startswith("https://"))
