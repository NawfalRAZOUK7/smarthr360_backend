from django.contrib.auth.models import AbstractUser
from django.db import models

# TODO (Step 1): Define custom User model:
# - email as USERNAME_FIELD
# - role field with choices (EMPLOYEE, MANAGER, HR, ADMIN)
class User(AbstractUser):
    # We'll implement fields in Step 1
    pass

