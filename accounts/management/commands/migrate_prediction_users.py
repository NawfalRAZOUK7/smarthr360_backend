"""
Migrate users from prediction_skills auth tables into accounts.User.

Default behavior is a dry-run. Use --apply to write changes.
"""

from __future__ import annotations

import re
from datetime import datetime

import dj_database_url
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import connections, transaction
from django.db.utils import OperationalError
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from accounts.models import normalize_email_address

SOURCE_ALIAS = "prediction_source"
HR_GROUPS = {"DRH", "RESPONSABLE_RH", "HR", "HR_ADMIN"}
MANAGER_GROUPS = {"MANAGER", "MANAGER_ADMIN"}


def _to_aware(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return timezone.make_aware(value) if timezone.is_naive(value) else value
    if isinstance(value, str):
        parsed = parse_datetime(value)
        if parsed is None:
            return None
        return timezone.make_aware(parsed) if timezone.is_naive(parsed) else parsed
    return None


def _safe_email_local(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9._+-]+", "-", value.strip().lower())
    cleaned = cleaned.strip("-._")
    cleaned = re.sub(r"[-.]{2,}", "-", cleaned)
    return cleaned or "user"


def _build_placeholder_email(username: str | None, source_id: int, domain: str) -> str:
    base = username or f"user{source_id}"
    local = _safe_email_local(base)[:64]
    return f"{local}@{domain}"


def _ensure_unique_username(base: str, used: set[str], max_length: int = 150) -> str:
    base_clean = base.strip()[:max_length] or "user"
    candidate = base_clean
    counter = 1
    while candidate.lower() in used:
        suffix = f"-{counter}"
        allowed = max_length - len(suffix)
        candidate = f"{base_clean[:allowed]}{suffix}"
        counter += 1
    used.add(candidate.lower())
    return candidate


def _prefer_candidate(current: dict, candidate: dict) -> bool:
    if candidate["is_active"] != current["is_active"]:
        return bool(candidate["is_active"])
    candidate_last = _to_aware(candidate["last_login"])
    current_last = _to_aware(current["last_login"])
    if candidate_last and current_last and candidate_last != current_last:
        return candidate_last > current_last
    if candidate_last and not current_last:
        return True
    if not candidate_last and current_last:
        return False
    candidate_joined = _to_aware(candidate["date_joined"])
    current_joined = _to_aware(current["date_joined"])
    if candidate_joined and current_joined and candidate_joined != current_joined:
        return candidate_joined > current_joined
    if candidate_joined and not current_joined:
        return True
    if not candidate_joined and current_joined:
        return False
    return candidate["source_id"] > current["source_id"]


class Command(BaseCommand):
    help = "Migrate users from prediction_skills auth_user/auth_group tables."

    def add_arguments(self, parser):
        parser.add_argument(
            "--source-url",
            required=True,
            help="Database URL for prediction_skills (ex: postgres:// or sqlite:///).",
        )
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Apply changes (default: dry-run).",
        )
        parser.add_argument(
            "--update-existing",
            action="store_true",
            help="Update existing users matched by email (or username with --match-username).",
        )
        parser.add_argument(
            "--match-username",
            action="store_true",
            help="Allow matching by username when email match is not found.",
        )
        parser.add_argument(
            "--mark-verified",
            action="store_true",
            help="Mark imported users as email-verified when an email is present.",
        )
        parser.add_argument(
            "--default-email-domain",
            default="placeholder.local",
            help="Domain used when source email is missing.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Limit the number of users processed (after de-duplication).",
        )

    def handle(self, *args, **options):
        source_url = options["source_url"]
        apply_changes = options["apply"]
        update_existing = options["update_existing"]
        match_username = options["match_username"]
        mark_verified = options["mark_verified"]
        default_domain = options["default_email_domain"]
        limit = options["limit"]

        self._register_source_db(source_url)

        source_users = self._fetch_source_users()
        if not source_users:
            self.stdout.write(self.style.WARNING("No users found in source database."))
            return

        selected_users, duplicate_emails, placeholder_count = self._dedupe_and_prepare(
            source_users,
            default_domain=default_domain,
        )

        if limit:
            selected_users = selected_users[:limit]

        User = get_user_model()
        existing_emails = {
            normalize_email_address(email)
            for email in User.objects.values_list("email", flat=True)
            if email
        }
        existing_usernames = {
            username.lower()
            for username in User.objects.values_list("username", flat=True)
            if username
        }

        stats = {
            "source_total": len(source_users),
            "after_dedupe": len(selected_users),
            "created": 0,
            "updated": 0,
            "skipped_existing": 0,
            "duplicates": len(duplicate_emails),
            "placeholder_emails": placeholder_count,
        }

        def process_user(source, *, apply_changes: bool):
            role = self._map_role(User, source["is_superuser"], source["groups"])
            email = source["email"]

            existing_user = User.objects.filter(email__iexact=email).first()
            if not existing_user and match_username and source["username"]:
                existing_user = User.objects.filter(username__iexact=source["username"]).first()

            verified_at = None
            is_verified = False
            if mark_verified and email:
                is_verified = True
                verified_at = (
                    _to_aware(source["last_login"])
                    or _to_aware(source["date_joined"])
                    or timezone.now()
                )

            if existing_user:
                if not update_existing:
                    stats["skipped_existing"] += 1
                    return

                if apply_changes:
                    existing_user.first_name = source["first_name"]
                    existing_user.last_name = source["last_name"]
                    existing_user.is_active = source["is_active"]
                    existing_user.is_staff = bool(source["is_staff"] or source["is_superuser"])
                    existing_user.is_superuser = source["is_superuser"]
                    existing_user.role = role
                    existing_user.last_login = _to_aware(source["last_login"])
                    existing_user.date_joined = _to_aware(source["date_joined"]) or existing_user.date_joined
                    existing_user.password = source["password"]
                    if is_verified:
                        existing_user.is_email_verified = True
                        if verified_at:
                            existing_user.email_verified_at = verified_at
                    existing_user.save()
                stats["updated"] += 1
                return

            if normalize_email_address(email) in existing_emails:
                stats["skipped_existing"] += 1
                return

            username_base = source["username"] or email
            username = _ensure_unique_username(username_base, existing_usernames)
            user = User(
                email=email,
                username=username,
                first_name=source["first_name"],
                last_name=source["last_name"],
                is_active=source["is_active"],
                is_staff=bool(source["is_staff"] or source["is_superuser"]),
                is_superuser=source["is_superuser"],
                role=role,
                last_login=_to_aware(source["last_login"]),
                date_joined=_to_aware(source["date_joined"]) or timezone.now(),
                is_email_verified=is_verified,
                email_verified_at=verified_at,
            )
            user.password = source["password"]
            if apply_changes:
                user.save()
            stats["created"] += 1
            existing_emails.add(normalize_email_address(email))

        if apply_changes:
            with transaction.atomic():
                for source in selected_users:
                    process_user(source, apply_changes=True)
        else:
            for source in selected_users:
                process_user(source, apply_changes=False)

        self._print_summary(stats, duplicate_emails, dry_run=not apply_changes)

    def _register_source_db(self, source_url: str) -> None:
        try:
            db_config = dj_database_url.parse(source_url)
        except Exception as exc:
            raise CommandError(f"Invalid --source-url: {exc}") from exc

        if not db_config:
            raise CommandError("Unable to parse --source-url.")

        settings.DATABASES[SOURCE_ALIAS] = db_config
        connections.databases = settings.DATABASES

        try:
            connections[SOURCE_ALIAS].ensure_connection()
        except OperationalError as exc:
            raise CommandError(f"Failed to connect to source database: {exc}") from exc

    def _fetch_source_users(self) -> list[dict]:
        query = """
            SELECT
                u.id,
                u.username,
                u.email,
                u.first_name,
                u.last_name,
                u.is_active,
                u.is_staff,
                u.is_superuser,
                u.last_login,
                u.date_joined,
                u.password,
                g.name
            FROM auth_user u
            LEFT JOIN auth_user_groups ug ON u.id = ug.user_id
            LEFT JOIN auth_group g ON ug.group_id = g.id
            ORDER BY u.id
        """

        users = {}
        with connections[SOURCE_ALIAS].cursor() as cursor:
            cursor.execute(query)
            for row in cursor.fetchall():
                (
                    source_id,
                    username,
                    email,
                    first_name,
                    last_name,
                    is_active,
                    is_staff,
                    is_superuser,
                    last_login,
                    date_joined,
                    password,
                    group_name,
                ) = row

                record = users.setdefault(
                    source_id,
                    {
                        "source_id": source_id,
                        "username": username or "",
                        "email": email or "",
                        "first_name": first_name or "",
                        "last_name": last_name or "",
                        "is_active": bool(is_active),
                        "is_staff": bool(is_staff),
                        "is_superuser": bool(is_superuser),
                        "last_login": last_login,
                        "date_joined": date_joined,
                        "password": password,
                        "groups": set(),
                    },
                )
                if group_name:
                    record["groups"].add(str(group_name))

        result = list(users.values())
        result.sort(key=lambda item: item["source_id"])
        return result

    def _dedupe_and_prepare(self, users: list[dict], default_domain: str):
        selected = {}
        duplicates = {}
        placeholder_count = 0

        for user in users:
            email = normalize_email_address(user["email"])
            if not email:
                email = _build_placeholder_email(user["username"], user["source_id"], default_domain)
                placeholder_count += 1
            user["email"] = email
            email_key = email.lower()

            if email_key in selected:
                # Resolve duplicate emails deterministically.
                if _prefer_candidate(selected[email_key], user):
                    duplicates.setdefault(email_key, []).append(selected[email_key]["source_id"])
                    selected[email_key] = user
                else:
                    duplicates.setdefault(email_key, []).append(user["source_id"])
                continue

            selected[email_key] = user

        return list(selected.values()), duplicates, placeholder_count

    def _map_role(self, user_model, is_superuser: bool, groups: set[str]) -> str:
        if is_superuser:
            return user_model.Role.ADMIN
        normalized = {group.strip().upper() for group in groups if group}
        if normalized & HR_GROUPS:
            return user_model.Role.HR
        if normalized & MANAGER_GROUPS:
            return user_model.Role.MANAGER
        return user_model.Role.EMPLOYEE

    def _print_summary(self, stats: dict, duplicates: dict, *, dry_run: bool) -> None:
        mode = "DRY-RUN" if dry_run else "APPLIED"
        self.stdout.write(self.style.MIGRATE_HEADING(f"Migration summary ({mode})"))
        self.stdout.write(f"- Source users: {stats['source_total']}")
        self.stdout.write(f"- After de-duplication: {stats['after_dedupe']}")
        self.stdout.write(f"- Created: {stats['created']}")
        self.stdout.write(f"- Updated: {stats['updated']}")
        self.stdout.write(f"- Skipped (existing): {stats['skipped_existing']}")
        self.stdout.write(f"- Duplicate emails: {stats['duplicates']}")
        self.stdout.write(f"- Placeholder emails: {stats['placeholder_emails']}")

        if duplicates:
            sample_keys = list(duplicates.keys())[:5]
            self.stdout.write("Duplicate email samples:")
            for key in sample_keys:
                ids = ", ".join(str(item) for item in duplicates[key][:5])
                self.stdout.write(f"  - {key}: {ids}")
