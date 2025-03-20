from django.db import models
from custom_auth.models import CustomUser
from clients.models import Customer
from django.core.validators import MinValueValidator, MaxValueValidator


class Department(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    manager = models.ForeignKey(CustomUser, 
            on_delete=models.SET_NULL, null=True, related_name="departments_manager")
    created_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, related_name="departments_created"
    )
    created_date = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, related_name="departments_updated"
    )
    updated_date = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class WorkCategory(models.Model):
    FREQUENCY_CHOICES = [("daily", "Daily"), 
                         ("weekly", "Weekly"), 
                         ("monthly", "Monthly"), 
                         ("yearly", "Yearly"),
                         ("quarterly", "Quarterly"),
                         ("half_yearly", "Half Yearly"),
                         ("other", "Other")]
    name = models.CharField(max_length=255)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="work_categories")
    fees = models.FloatField(blank=True, null=True, default=0)
    created_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, related_name="workcategories_created"
    )
    created_date = models.DateTimeField(auto_now_add=True)
    frequency = models.CharField(max_length=100, choices=FREQUENCY_CHOICES, blank=True, null=True)
    start_dates = models.DateField(blank=True, null=True)
    updated_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, related_name="workcategories_updated"
    )
    updated_date = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.department.name})"


class WorkCategoryDate(models.Model):
    DATE_TYPE_CHOICES = [
        ('monthly', 'Monthly (e.g., 13th of every month)'),
        ('yearly', 'Yearly (e.g., 15th March)'),
    ]

    work_category = models.ForeignKey(
        'WorkCategory',
        on_delete=models.CASCADE,
        related_name='dates'
    )
    date_type = models.CharField(
        max_length=10,
        choices=DATE_TYPE_CHOICES,
        default='monthly'
    )
    # For monthly: day of the month (e.g., 15)
    day = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        help_text="Day of the month (1-31). Required for all types."
    )
    # For yearly: month (e.g., 3 for March)
    month = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text="Month (1-12). Required for 'yearly' type."
    )

    def __str__(self):
        if self.date_type == 'monthly':
            return f"Monthly: Day {self.day}"
        elif self.date_type == 'yearly':
            return f"Yearly: {self.day}/{self.month}"


class WorkCategoryFilesRequired(models.Model):
    id = models.AutoField(primary_key=True)
    work_category = models.ForeignKey(WorkCategory, on_delete=models.CASCADE, related_name="files_required")
    file_name = models.CharField(max_length=255)
    display_order = models.PositiveIntegerField(default=0, null=True, blank=True)
    created_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, related_name="workcategories_filesrequired_created"
    )
    created_date = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, related_name="workcategories_filesrequired_updated"
    )
    updated_date = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.file_name} ({self.work_category.name})"
    

class WorkCategoryActivityList(models.Model):
    id = models.AutoField(primary_key=True)
    work_category = models.ForeignKey(WorkCategory, on_delete=models.CASCADE, related_name="activity_list")
    activity_name = models.CharField(max_length=255)
    assigned_percentage = models.FloatField(blank=True, null=True)
    display_order = models.PositiveIntegerField(default=0, null=True, blank=True)
    created_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, related_name="workcategories_activitylist_created")
    created_date = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, related_name="workcategories_activitylist_updated")
    updated_date = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.activity_name} ({self.work_category.name})"


class WorkCategoryActivityStages(models.Model):
    id = models.AutoField(primary_key=True)
    work_category = models.ForeignKey(WorkCategory, on_delete=models.CASCADE, related_name="activity_stage")
    activity_stage = models.CharField(max_length=255)
    description = models.CharField(max_length=200, blank=True, null=True)
    display_order = models.PositiveIntegerField(default=0, null=True, blank=True)
    created_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, related_name="workcategories_activitystage_created")
    created_date = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, related_name="workcategories_activitystage_updated")
    updated_date = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.activity_stage} ({self.work_category.name})"


class WorkCategoryUploadDocumentRequired(models.Model):
    id = models.AutoField(primary_key=True)
    work_category = models.ForeignKey(WorkCategory, on_delete=models.CASCADE, related_name="upload_document")
    file_name = models.CharField(max_length=255)
    display_order = models.PositiveIntegerField(default=0, null=True, blank=True)
    created_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, related_name="workcategories_documentrequired_created"
    )
    created_date = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, related_name="workcategories_documentrequired_updated"
    )
    updated_date = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.file_name} ({self.work_category.name})"
    

class ClientWorkCategoryAssignment(models.Model):
    progress_choices = [("pending_from_client_side", "Pending from Client Side"),
                        ("details_received_but_work_not_started", "Details Received but Work Not Started"), 
                        ("work_in_progress", "Work in Progress"),
                        ("task_under_review", "Task Under Review"),
                        ("pending_sr_review", "Pending SR. Review"),
                        ("sr_review_completed", "SR. Review Completed"),
                        ("task_completed", "Task Completed"),
                        ("task_billed", "Task Billed"),
                        ("payment_pending", "Payment Pending"),
                        ("payment_received", "Payment Received"),
                        ("task_closed", "Task Closed")]
    priority_choices = [(1, "Low"), (2, "Medium"), (3, "High"), (4, "Urgent")]
    status_choices = [("wip_task", "WIP Task"), ("overdue", "Overdue"), ("closed", "Closed")]
    assignment_id = models.AutoField(primary_key=True)
    task_name = models.CharField(max_length=120, null=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="work_category_customer")
    work_category = models.ForeignKey(WorkCategory, on_delete=models.CASCADE, related_name="assignments")
    instructions = models.CharField(max_length=400, blank=True, null=True)
    review_notes = models.CharField(max_length=400, blank=True, null=True)
    progress = models.CharField(max_length=100, choices=progress_choices, default="pending_from_client_side")
    allocated_hours = models.FloatField(blank=True, null=True)
    priority = models.IntegerField(default=1, choices=priority_choices)
    start_date = models.DateField(blank=True, null=True)
    completion_date = models.DateField(blank=True, null=True)
    assigned_to = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name="work_category_assignments")
    assigned_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name="work_category_assignments_assigned")
    review_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name="work_category_reviewed")
    created_date = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name="work_category_assignments_created")
    updated_date = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name="work_category_assignments_updated")
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.customer.name_of_business} - {self.work_category.name}"
    

class AssignedWorkRequiredFiles(models.Model):
    id = models.AutoField(primary_key=True)
    assignment = models.ForeignKey(ClientWorkCategoryAssignment, on_delete=models.CASCADE, related_name="required_files")
    file_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=255, null=True, blank=True)
    display_order = models.PositiveIntegerField(default=0, null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.file_name} ({self.assignment.customer.name_of_business})"


class AssignedWorkActivity(models.Model):
    status_choices = [("pending", "Pending"), ("in_progress", "In Progress"), ("completed", "Completed")]
    id = models.AutoField(primary_key=True)
    assignment = models.ForeignKey(ClientWorkCategoryAssignment, on_delete=models.CASCADE, related_name="activities")
    activity = models.CharField(max_length=100, null=True, blank=True)
    assigned_percentage = models.FloatField(blank=True, null=True)
    status = models.CharField(max_length=100, choices=status_choices, default="pending")
    note = models.CharField(max_length=100, null=True, blank=True)
    display_order = models.PositiveIntegerField(default=0, null=True, blank=True)
    start_date = models.DateField(blank=True, null=True)
    completion_date = models.DateField(blank=True, null=True)
    updated_date = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.activity.activity_name} ({self.assignment.customer.name_of_business})"
    

class AssignedWorkActivityStages(models.Model):
    id = models.AutoField(primary_key=True)
    assignment = models.ForeignKey(ClientWorkCategoryAssignment, on_delete=models.CASCADE, related_name="activity_stages")
    activity_stage = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=100, null=True, blank=True)
    start_date = models.DateField(blank=True, null=True)
    display_order = models.PositiveIntegerField(default=0, null=True, blank=True)
    completion_date = models.DateField(blank=True, null=True)
    updated_date = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.stage} ({self.activity.activity})"


class AssignedWorkOutputFiles(models.Model):
    id = models.AutoField(primary_key=True)
    assignment = models.ForeignKey(ClientWorkCategoryAssignment, on_delete=models.CASCADE, related_name="output_files")
    file_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=255, null=True, blank=True)
    display_order = models.PositiveIntegerField(default=0, null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.file_name} ({self.assignment.customer.name_of_business})"