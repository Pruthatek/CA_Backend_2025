from django.db import models
from custom_auth.models import CustomUser
from clients.models import Customer


class Department(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
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
    name = models.CharField(max_length=255)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="work_categories")
    created_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, related_name="workcategories_created"
    )
    created_date = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, related_name="workcategories_updated"
    )
    updated_date = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.department.name})"


class WorkCategoryFilesRequired(models.Model):
    id = models.AutoField(primary_key=True)
    work_category = models.ForeignKey(WorkCategory, on_delete=models.CASCADE, related_name="files_required")
    file_name = models.CharField(max_length=255)
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
    created_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, related_name="workcategories_activitylist_created")
    created_date = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, related_name="workcategories_activitylist_updated")
    updated_date = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.activity_name} ({self.work_category.name})"


class WorkCategoryUploadDocumentRequired(models.Model):
    id = models.AutoField(primary_key=True)
    work_category = models.ForeignKey(WorkCategory, on_delete=models.CASCADE, related_name="upload_document")
    file_name = models.CharField(max_length=255)
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
    assignment_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="work_category_customer")
    work_category = models.ForeignKey(WorkCategory, on_delete=models.CASCADE, related_name="assignments")
    review_notes = models.CharField(max_length=400, blank=True, null=True)
    progress = models.CharField(max_length=100, choices=progress_choices, default="pending_from_client_side")
    allocated_hours = models.FloatField(blank=True, null=True)
    priority = models.IntegerField(default=1, choices=progress_choices)
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
    start_date = models.DateField(blank=True, null=True)
    completion_date = models.DateField(blank=True, null=True)
    updated_date = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.activity.activity_name} ({self.assignment.customer.name_of_business})"
    

class AssignedWorkOutputFiles(models.Model):
    id = models.AutoField(primary_key=True)
    assignment = models.ForeignKey(ClientWorkCategoryAssignment, on_delete=models.CASCADE, related_name="output_files")
    file_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=255, null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.file_name} ({self.assignment.customer.name_of_business})"