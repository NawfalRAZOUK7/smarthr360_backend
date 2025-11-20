from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError


class Department(models.Model):
    """
    Basic department / team inside SmartHR360.
    Example: 'IT', 'HR', 'Finance', 'Marketing'...
    """
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.code} - {self.name}"


class EmployeeProfile(models.Model):
    """
    HR information for a user.
    One-to-one with accounts.User (AUTH_USER_MODEL).
    """
    class EmploymentType(models.TextChoices):
        FULL_TIME = "FULL_TIME", "Full time"
        PART_TIME = "PART_TIME", "Part time"
        INTERN = "INTERN", "Intern"
        CONTRACTOR = "CONTRACTOR", "Contractor"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="employee_profile",
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employees",
    )

    manager = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="team_members",
    )

    job_title = models.CharField(max_length=150, blank=True)
    employment_type = models.CharField(
        max_length=20,
        choices=EmploymentType.choices,
        default=EmploymentType.FULL_TIME,
    )
    hire_date = models.DateField(null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=30, blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.job_title or 'Employee'}"

    def clean(self):
        super().clean()

        # cannot be own manager
        if self.manager_id and self.manager_id == self.id:
            raise ValidationError("An employee cannot be their own manager.")

        # manager must have MANAGER / HR / ADMIN role
        if self.manager and self.manager.user.role not in [
            self.manager.user.Role.MANAGER,
            self.manager.user.Role.HR,
            self.manager.user.Role.ADMIN,
        ]:
            raise ValidationError("Selected manager must have Manager, HR, or Admin role.")

