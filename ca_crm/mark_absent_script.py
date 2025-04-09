import os
import django
from datetime import date
from django.db import transaction

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ca_crm.settings')  # change this
django.setup()

from employees.models import EmployeeAttendance, EmployeeProfile, Holiday, CustomUser

def mark_absent():
    today = date.today()

    if today.weekday() in [5, 6]:
        print("Skipping script for weekends.")
        return

    if Holiday.objects.filter(date=today).exists():
        print("Skipping script for holiday.")
        return

    employees = CustomUser.objects.all()

    with transaction.atomic():
        for employee in employees:
            attendance = EmployeeAttendance.objects.filter(employee=employee, date=today).first()

            if not attendance:
                EmployeeAttendance.objects.create(
                    employee=employee,
                    date=today,
                    status="absent",
                    remarks="Did not check-in"
                )
            elif attendance.check_in and not attendance.check_out:
                attendance.status = "absent"
                attendance.remarks = "Did not check-out"
                attendance.save()

    print("Attendance update complete.")

if __name__ == "__main__":
    mark_absent()
