from .base import *  # noqa: F403

# Production overrides
DEBUG = False
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='', cast=Csv())  # noqa: F405

# Hardened defaults (still environment-driven)
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)  # noqa: F405
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=True, cast=bool)  # noqa: F405
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=True, cast=bool)  # noqa: F405
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=3600, cast=int)  # noqa: F405
SECURE_HSTS_INCLUDE_SUBDOMAINS = config('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True, cast=bool)  # noqa: F405
SECURE_HSTS_PRELOAD = config('SECURE_HSTS_PRELOAD', default=False, cast=bool)  # noqa: F405
