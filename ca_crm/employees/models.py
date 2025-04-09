from django.db import models
from custom_auth.models import CustomUser, EmployeeProfile
from datetime import datetime, timedelta
from clients.models import Customer
from workflow.models import ClientWorkCategoryAssignment, AssignedWorkActivity
# Create your models here.

class EmployeeAttendance(models.Model):
    STATUS_CHOICES = (
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('leave', 'Leave'),
    )
    employee = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="attendances"
    )
    date = models.DateField()
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    total_hrs = models.DurationField(null=True, blank=True) 
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='leave')
    remarks = models.TextField(null=True, blank=True)
    is_approved = models.BooleanField(default=False)

    class Meta:
        unique_together = ("employee", "date")
        ordering = ['-date']

    def __str__(self):
        return f"{self.employee.user.username} - {self.date}"

    def save(self, *args, **kwargs):
        """Calculate and store only hours and minutes in total_hrs."""
        if self.check_in and self.check_out:
            start = datetime.combine(self.date, self.check_in)
            end = datetime.combine(self.date, self.check_out)
            duration = end - start

            # Extract hours and minutes, ignoring seconds
            total_hours = duration.seconds // 3600
            total_minutes = (duration.seconds % 3600) // 60
            self.total_hrs = timedelta(hours=total_hours, minutes=total_minutes)

        super().save(*args, **kwargs)


class Holiday(models.Model):
    date = models.DateField(unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    is_optional = models.BooleanField(default=False)

    class Meta:
        ordering = ['date']

    def __str__(self):
        return f"{self.date} - {self.name}"


class TimeTracking(models.Model):
    TASK_TYPE_CHOICES = (
        ('billable', 'Billable'),
        ('non_billable', 'Non Billable')
    )
    employee = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="time_entries"
    )
    client = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, related_name="time_on_client")
    work = models.ForeignKey(ClientWorkCategoryAssignment, on_delete=models.SET_NULL, null=True, related_name="time_for_work")
    work_activity = models.ForeignKey(AssignedWorkActivity, on_delete=models.SET_NULL, null=True, related_name="time_for_activity")
    task_type = models.CharField(max_length=20, choices=TASK_TYPE_CHOICES, default="non_billable")
    date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    task_description = models.CharField(max_length=200, null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)

    class Meta:
        ordering = ['-date', 'start_time']

    def save(self, *args, **kwargs):
        # Optionally compute duration if start_time and end_time are provided
        if self.start_time and self.end_time:
            import datetime
            start = self.start_time
            end = self.end_time
            self.duration = end - start
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee.username} - {self.date} ({self.task_type})"
    

class LeaveType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    max_days = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class UserLeaveMapping(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    total_days = models.PositiveIntegerField(default=0)
    remaining_days = models.PositiveIntegerField(default=0)
    year = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'leave_type', 'year')


class LeaveApplication(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    
    employee = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='leave_applications')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE, related_name="applied_leave")
    start_date = models.DateField()
    end_date = models.DateField()
    days = models.PositiveIntegerField(default=1)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    approved_on = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee.username} - {self.leave_type.name} ({self.start_date} to {self.end_date})"
