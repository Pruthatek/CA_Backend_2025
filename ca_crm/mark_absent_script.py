from datetime import date
from django.core.management.base import BaseCommand
from employees.models import EmployeeAttendance, EmployeeProfile, Holiday
from django.db import transaction

class Command(BaseCommand):
    help = "Marks employees as absent if they missed clock-in or clock-out"

    def handle(self, *args, **kwargs):
        today = date.today()

        # Skip if it's a weekend
        if today.weekday() in [5, 6]:  # 5=Saturday, 6=Sunday
            self.stdout.write("Skipping script for weekends.")
            return

        # Skip if it's a holiday
        if Holiday.objects.filter(date=today).exists():
            self.stdout.write("Skipping script for holiday.")
            return

        employees = EmployeeProfile.objects.all()

        with transaction.atomic():
            for employee in employees:
                attendance = EmployeeAttendance.objects.filter(employee=employee, date=today).first()

                if not attendance:
                    # No clock-in, mark absent
                    EmployeeAttendance.objects.create(
                        employee=employee,
                        date=today,
                        status="absent",
                        remarks="Did not check-in"
                    )
                elif attendance.check_in and not attendance.check_out:
                    # Forgot to clock out, mark absent
                    attendance.status = "absent"
                    attendance.remarks = "Did not check-out"
                    attendance.save()

        self.stdout.write("Attendance update complete.")
