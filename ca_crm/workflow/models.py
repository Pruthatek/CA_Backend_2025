from django.db import models
from custom_auth.models import CustomUser

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
    description = models.TextField(blank=True, null=True)
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
    id = models.IntegerField(primary_key=True)
    work_category = models.ForeignKey(WorkCategory, on_delete=models.CASCADE, related_name="files_required")
    file_name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
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
    id = models.IntegerField(primary_key=True)
    work_category = models.ForeignKey(WorkCategory, on_delete=models.CASCADE, related_name="activity_list")
    activity_name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, related_name="workcategories_activitylist_created")
    created_date = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, related_name="workcategories_activitylist_updated")
    updated_date = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.activity_name} ({self.work_category.name})"


class WorkCategoryUploadDocumetRequired(models.Model):
    id = models.IntegerField(primary_key=True)
    work_category = models.ForeignKey(WorkCategory, on_delete=models.CASCADE, related_name="upload_document")
    file_name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
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
    


                                      