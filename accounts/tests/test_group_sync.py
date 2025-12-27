from django.contrib.auth.models import Group
from django.test import TestCase

from accounts.models import User


class GroupSyncTests(TestCase):
    def test_role_assigns_base_group(self):
        user = User.objects.create_user(
            email="hr_group@example.com",
            username="hr_group",
            password="HrPass123!",
            role=User.Role.HR,
        )

        self.assertTrue(user.groups.filter(name="HR").exists())

    def test_role_change_updates_base_group_without_removing_admin_groups(self):
        user = User.objects.create_user(
            email="manager_group@example.com",
            username="manager_group",
            password="ManagerPass123!",
            role=User.Role.HR,
        )
        hr_admin, _ = Group.objects.get_or_create(name="HR_ADMIN")
        user.groups.add(hr_admin)

        user.role = User.Role.MANAGER
        user.save()

        self.assertTrue(user.groups.filter(name="MANAGER").exists())
        self.assertFalse(user.groups.filter(name="HR").exists())
        self.assertTrue(user.groups.filter(name="HR_ADMIN").exists())

    def test_admin_removes_base_groups(self):
        user = User.objects.create_user(
            email="admin_group@example.com",
            username="admin_group",
            password="AdminPass123!",
            role=User.Role.MANAGER,
        )
        self.assertTrue(user.groups.filter(name="MANAGER").exists())

        user.role = User.Role.ADMIN
        user.save()

        self.assertFalse(user.groups.filter(name__in=["HR", "MANAGER", "EMPLOYEE"]).exists())
