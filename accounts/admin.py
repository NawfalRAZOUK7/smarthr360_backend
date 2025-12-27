from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import (
    LoginActivity,
    LoginAttempt,
    User,
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # adapt these fields to your existing config if you already customized it
    ordering = ("email",)
    list_display = (
        "email",
        "username",
        "first_name",
        "last_name",
        "role",
        "is_staff",
        "is_active",
        "is_email_verified",
        "email_verified_at",
    )
    list_filter = ("role", "is_active", "is_email_verified", "is_staff", "is_superuser")
    search_fields = ("email", "username", "first_name", "last_name")
    readonly_fields = ("email_verified_at",)

    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name")}),
        ("Role & permissions", {
            "fields": (
                "role",
                "is_active",
                "is_staff",
                "is_superuser",
                "is_email_verified",
                "email_verified_at",
                "groups",
                "user_permissions",
            )
        }),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "username",
                    "password1",
                    "password2",
                    "role",
                    "is_staff",
                    "is_superuser",
                    "is_active",
                ),
            },
        ),
    )

    filter_horizontal = ()

@admin.register(LoginActivity)
class LoginActivityAdmin(admin.ModelAdmin):
    list_display = ("user", "action", "success", "timestamp", "ip_address")
    list_filter = ("action", "success", "timestamp")
    search_fields = ("user__email", "ip_address", "user_agent")
    readonly_fields = (
        "user",
        "action",
        "success",
        "timestamp",
        "ip_address",
        "user_agent",
        "extra_data",
    )


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ("user", "failed_attempts", "is_locked", "locked_until")
    search_fields = ("user__email",)
    readonly_fields = ("failed_attempts", "last_failed_at", "is_locked", "locked_until")
