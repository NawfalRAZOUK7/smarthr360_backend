from .base import *  # noqa: F403

# Local overrides
DEBUG = True
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,testserver', cast=Csv())  # noqa: F405

# Keep console email backend by default locally
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')  # noqa: F405
