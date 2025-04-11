import os
import django
from django.contrib.auth.hashers import make_password
from django.db import transaction
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ca_crm.settings')  # change this
django.setup()

from employees.models import Role, Permission, RolePermission, CustomUser, EmployeeProfile, ReportingUser

def create_admin_user():
    with transaction.atomic():
        # Create Role
        role, _ = Role.objects.get_or_create(name="Admin", defaults={"description": "Admin role"})

        # Create Permission
        perm, _ = Permission.objects.get_or_create(name="admin", defaults={"description": "Admin permission"})

        # Map Role to Permission
        RolePermission.objects.get_or_create(role=role, permission=perm)

        # Create Admin User
        if not CustomUser.objects.filter(username="admin").exists():
            admin = CustomUser.objects.create(
                username="admin",
                email="admin@example.com",
                password=make_password("admin123"),
                first_name="Super",
                last_name="Admin",
                role=role,
                phone_number="9999999999",
                employee_code="EMP001",
                gender="Other",
                photo_url="",
                address="HQ",
                date_of_birth=date(1990, 1, 1),
                is_active=True,
            )

            EmployeeProfile.objects.create(user=admin, designation="Administrator")
            ReportingUser.objects.create(user=admin)

            print("✅ Admin user created.")
        else:
            print("ℹ️ Admin user already exists.")

if __name__ == "__main__":
    create_admin_user()
