from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


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

class Skill(models.Model):
    """
    Skill catalog (compétences de base).
    Defined by HR / Managers and reused in employee evaluations.
    """

    name = models.CharField(max_length=150)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_skills",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"

class EmployeeSkill(models.Model):
    """
    Employee evaluation on a given skill.
    """

    class Level(models.IntegerChoices):
        BEGINNER = 1, "Beginner"
        INTERMEDIATE = 2, "Intermediate"
        ADVANCED = 3, "Advanced"
        EXPERT = 4, "Expert"

    employee = models.ForeignKey(
        "hr.EmployeeProfile",
        on_delete=models.CASCADE,
        related_name="skills",
    )
    skill = models.ForeignKey(
        "hr.Skill",
        on_delete=models.CASCADE,
        related_name="employee_skills",
    )
    level = models.PositiveSmallIntegerField(choices=Level.choices)
    target_level = models.PositiveSmallIntegerField(
        choices=Level.choices,
        null=True,
        blank=True,
    )
    last_evaluated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="skill_evaluations",
    )
    last_evaluated_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("employee", "skill")
        ordering = ["employee", "skill"]

    def __str__(self):
        return f"{self.employee} - {self.skill} ({self.get_level_display()})"

class FutureCompetency(models.Model):
    """
    Future competency needs for departments / organization.
    Used for Module 3 'Prédire les compétences futures'.
    """

    TIMEFRAME_CHOICES = [
        ("SHORT", "0–12 months"),
        ("MEDIUM", "1–3 years"),
        ("LONG", "3+ years"),
    ]

    skill = models.ForeignKey(
        "hr.Skill",
        on_delete=models.CASCADE,
        related_name="future_competencies",
    )
    department = models.ForeignKey(
        "hr.Department",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="future_competencies",
    )
    timeframe = models.CharField(max_length=10, choices=TIMEFRAME_CHOICES)
    importance = models.PositiveSmallIntegerField(default=3)  # 1–5
    description = models.TextField(blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_future_competencies",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-importance", "skill__name"]

    def __str__(self):
        dept = self.department.name if self.department else "Global"
        return f"{self.skill.name} ({dept}, {self.timeframe})"
