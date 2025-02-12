from django.db import models
from workflow.models import ClientWorkCategoryAssignment
from clients.models import Customer
from custom_auth.models import CustomUser


class CustomerDcs(models.Model):
    # Class Type Choices
    CLASS_TYPE_CHOICES = (
        ('class_type_1', 'Class type 1'),
        ('class_type_2', 'Class type 2'),
        ('class_type_3', 'Class type 3'),
    )

    # Position Choices
    POSITION_CHOICES = (
        ('individual', 'Individual'),
        ('director', 'Director'),
        ('partner', 'Partner'),
    )

    # Fields
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, related_name="dcs_customer")
    pan_no = models.CharField(max_length=10, unique=True, verbose_name="PAN No.")
    name = models.CharField(max_length=255, verbose_name="Name")
    related_company = models.CharField(max_length=255, verbose_name="Related Company")
    issue_date = models.DateField(verbose_name="Issue Date")
    valid_till_date = models.DateField(verbose_name="Valid Till Date")
    issuing_authority = models.CharField(max_length=255, blank=True, null=True, verbose_name="Issuing Authority")
    password = models.CharField(max_length=255, verbose_name="Password")
    position = models.CharField(max_length=20, choices=POSITION_CHOICES, verbose_name="Select Position")
    class_type = models.CharField(max_length=20, choices=CLASS_TYPE_CHOICES, verbose_name="Class Type")
    mobile_no = models.CharField(max_length=15, blank=True, null=True, verbose_name="Mobile No.")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    custodian_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Custodian Name")
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='dcs_created_customers')
    created_date = models.DateTimeField(auto_now_add=True, verbose_name="Created Date")
    updated_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='dcs_updated_customers')
    updated_date = models.DateTimeField(auto_now=True, verbose_name="Updated Date")

    def __str__(self):
        return f"{self.name} ({self.pan_no})"


