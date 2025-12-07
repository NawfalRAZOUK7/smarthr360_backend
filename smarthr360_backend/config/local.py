from .base import *  # noqa: F403

# Local overrides
DEBUG = True
_local_hosts = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,testserver', cast=Csv())  # noqa: F405
ALLOWED_HOSTS = list(_local_hosts)
if 'testserver' not in ALLOWED_HOSTS:
	ALLOWED_HOSTS.append('testserver')

# Keep console email backend by default locally
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')  # noqa: F405
