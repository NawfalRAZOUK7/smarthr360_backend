from django.db import migrations, models
import django.db.models.functions


def normalize_user_emails(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    users = list(User.objects.all().only("id", "email", "username"))
    normalized_map = {}
    duplicates = set()

    for user in users:
        if not user.email:
            continue
        normalized_email = user.email.strip().lower()
        if normalized_email in normalized_map and normalized_map[normalized_email] != user.id:
            duplicates.add(normalized_email)
        normalized_map[normalized_email] = user.id

    if duplicates:
        sample = ", ".join(sorted(duplicates)[:5])
        raise RuntimeError(
            "Case-insensitive duplicate emails found; resolve before migrating. "
            f"Examples: {sample}"
        )

    for user in users:
        if not user.email:
            continue
        normalized_email = user.email.strip().lower()
        updates = {}
        if user.email != normalized_email:
            updates["email"] = normalized_email
        if not user.username:
            updates["username"] = normalized_email
        if updates:
            User.objects.filter(pk=user.pk).update(**updates)


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0006_loginactivity"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="username",
            field=models.CharField(
                blank=True,
                help_text="Compatibility username; defaults to normalized email.",
                max_length=150,
                null=True,
                unique=True,
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="email_verified_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RunPython(normalize_user_emails, migrations.RunPython.noop),
        migrations.AddIndex(
            model_name="user",
            index=models.Index(fields=["role"], name="accounts_user_role_idx"),
        ),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.UniqueConstraint(
                django.db.models.functions.Lower("email"),
                name="accounts_user_email_ci_unique",
            ),
        ),
    ]
