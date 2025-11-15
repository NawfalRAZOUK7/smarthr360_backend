from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """
    Custom manager for User using email instead of username.
    """

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("L'utilisateur doit avoir une adresse email.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        # Optionnel : rôle ADMIN par défaut pour superuser
        # (si tu veux un autre comportement, on changera)
        if "role" not in extra_fields:
            # we use self.model to access Role enum
            extra_fields["role"] = self.model.Role.ADMIN

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom User model for SmartHR360:
    - login by email
    - roles (EMPLOYEE, MANAGER, HR, ADMIN)
    """

    class Role(models.TextChoices):
        EMPLOYEE = "EMPLOYEE", "Employee"
        MANAGER = "MANAGER", "Manager"
        HR = "HR", "HR"
        ADMIN = "ADMIN", "Admin"

    # we remove username and use email instead
    # ❗ Remove username, use email instead
    username = None

    # ❗ MUST be unique because USERNAME_FIELD = "email"
    email = models.EmailField(unique=True)

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.EMPLOYEE,
    )

    # ⬇️ add these helper methods/properties

    ROLE_HIERARCHY = {
        Role.EMPLOYEE: 1,
        Role.MANAGER: 2,
        Role.HR: 3,
        Role.ADMIN: 4,
    }

    @property
    def role_rank(self) -> int:
        """
        Returns a numeric rank for comparison.
        Higher = more privileges.
        """
        return self.ROLE_HIERARCHY.get(self.role, 0)

    def has_role(self, *roles) -> bool:
        """
        Check if user has one of the given roles.
        Example: user.has_role(User.Role.HR, User.Role.ADMIN)
        """
        return self.role in roles

    def is_at_least(self, role: str) -> bool:
        """
        Check if user's rank >= given role rank.
        Example: user.is_at_least(User.Role.MANAGER)
        """
        required_rank = self.ROLE_HIERARCHY.get(role, 0)
        return self.role_rank >= required_rank

    # later we can add more fields (department, company, etc.)
    # department = models.CharField(max_length=100, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # no username required

    objects = UserManager()

    def __str__(self):
        return f"{self.email} ({self.role})"
