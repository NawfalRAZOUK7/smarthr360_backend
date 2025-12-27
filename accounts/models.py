import uuid
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager, Group
from django.db import models
from django.db.models.functions import Lower
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .grouping import BASE_ROLE_GROUPS, ROLE_TO_BASE_GROUP

def normalize_email_address(email):
    if not email:
        return email
    return email.strip().lower()


class UserManager(BaseUserManager):
    """
    Custom manager for User using email instead of username.
    """

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("L'utilisateur doit avoir une adresse email.")
        email = self.normalize_email(email)
        extra_fields.setdefault("username", email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    @classmethod
    def normalize_email(cls, email):
        return normalize_email_address(email)

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

    username = models.CharField(
        max_length=150,
        unique=True,
        blank=True,
        null=True,
        help_text="Compatibility username; defaults to normalized email.",
    )

    # ❗ MUST be unique because USERNAME_FIELD = "email"
    email = models.EmailField(unique=True)

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.EMPLOYEE,
    )

    # ⬇️ add these helper methods/properties

    ROLE_HIERARCHY: dict[str, int] = {
        "EMPLOYEE": 1,
        "MANAGER": 2,
        "HR": 3,
        "ADMIN": 4,
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
    REQUIRED_FIELDS: list[str] = []  # no username required

    objects = UserManager()

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower("email"),
                name="accounts_user_email_ci_unique",
            ),
        ]
        indexes = [
            models.Index(fields=["role"], name="accounts_user_role_idx"),
        ]

    def save(self, *args, **kwargs):
        if self.email:
            self.email = normalize_email_address(self.email)
        if self.email and not self.username:
            self.username = self.email
        if self.is_email_verified and not self.email_verified_at:
            self.email_verified_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.email} ({self.role})"

class PasswordResetToken(models.Model):
    """
    Simple password reset token model.

    - A random token linked to a user.
    - Expires after EXPIRATION_HOURS.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="password_reset_tokens",
    )
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    EXPIRATION_HOURS = 1

    def __str__(self):
        return f"Password reset token for {self.user.email} ({self.token})"

    @classmethod
    def create_for_user(cls, user):
        return cls.objects.create(
            user=user,
            token=uuid.uuid4().hex,
        )

    def _expiration_datetime(self):
        # Allow tests to inject a custom expires_at attribute without a schema change
        explicit = getattr(self, "expires_at", None)
        if explicit is not None:
            return explicit
        return self.created_at + timedelta(hours=self.EXPIRATION_HOURS)

    def mark_used(self):
        self.is_used = True
        self.save(update_fields=["is_used"])

    def is_expired(self):
        return self._expiration_datetime() < timezone.now()

class EmailVerificationToken(models.Model):
    """
    Token for verifying user email addresses.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="email_verification_tokens",
    )
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    EXPIRATION_HOURS = 24

    def __str__(self):
        return f"Email verification token for {self.user.email}"

    @classmethod
    def create_for_user(cls, user):
        return cls.objects.create(
            user=user,
            token=uuid.uuid4().hex,
        )

    def _expiration_datetime(self):
        explicit = getattr(self, "expires_at", None)
        if explicit is not None:
            return explicit
        return self.created_at + timedelta(hours=self.EXPIRATION_HOURS)

    def mark_used(self):
        self.is_used = True
        self.save(update_fields=["is_used"])

    def is_expired(self):
        return self._expiration_datetime() < timezone.now()

class LoginAttempt(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="login_attempt",
    )
    failed_attempts = models.PositiveIntegerField(default=0)
    last_failed_at = models.DateTimeField(null=True, blank=True)
    is_locked = models.BooleanField(default=False)
    locked_until = models.DateTimeField(null=True, blank=True)

    MAX_ATTEMPTS = 5               # after 5 failed logins → lock account
    LOCKOUT_MINUTES = 15           # locked for 15 minutes

    def mark_failed(self):
        from django.utils import timezone
        now = timezone.now()

        self.failed_attempts += 1
        self.last_failed_at = now

        if self.failed_attempts >= self.MAX_ATTEMPTS:
            self.is_locked = True
            self.locked_until = now + timedelta(minutes=self.LOCKOUT_MINUTES)

        self.save()

    def reset_attempts(self):
        self.failed_attempts = 0
        self.is_locked = False
        self.locked_until = None
        self.save()

    def check_lock_status(self):
        from django.utils import timezone

        if not self.is_locked:
            return False

        # if lock expired → unlock
        if self.locked_until and self.locked_until <= timezone.now():
            self.reset_attempts()
            return False

        return True

@receiver(post_save, sender=User)
def create_login_attempt(sender, instance, created, **kwargs):
    if created:
        LoginAttempt.objects.create(user=instance)


def _ensure_group(name: str) -> Group:
    group, _ = Group.objects.get_or_create(name=name)
    return group


def _sync_role_base_group(user: User) -> None:
    if not user.pk:
        return

    if user.role == User.Role.ADMIN:
        if BASE_ROLE_GROUPS:
            user.groups.remove(*Group.objects.filter(name__in=BASE_ROLE_GROUPS))
        return

    base_group_name = ROLE_TO_BASE_GROUP.get(user.role)
    if not base_group_name:
        return

    target_group = _ensure_group(base_group_name)
    user.groups.add(target_group)

    other_base_groups = BASE_ROLE_GROUPS - {base_group_name}
    if other_base_groups:
        user.groups.remove(*Group.objects.filter(name__in=other_base_groups))


@receiver(post_save, sender=User)
def sync_user_role_group(sender, instance, **kwargs):
    _sync_role_base_group(instance)

class LoginActivity(models.Model):
    class Action(models.TextChoices):
        LOGIN = "LOGIN", "Login"
        LOGOUT = "LOGOUT", "Logout"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="login_activities",
    )
    action = models.CharField(max_length=20, choices=Action.choices)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    success = models.BooleanField(default=True)
    extra_data = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.email} - {self.action} ({'success' if self.success else 'failed'})"
