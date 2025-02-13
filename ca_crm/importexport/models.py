from django.db import models
from clients.models import Customer
from custom_auth.models import CustomUser


class Location(models.Model):
    id = models.AutoField(primary_key=True)
    location = models.CharField(max_length=120, unique=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    photo = models.CharField(max_length=200, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    modified_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='location_modified')
    modified_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.location}"


class Inward(models.Model):
    # Choices for Inward Type
    INWARD_FOR_CHOICES = [
        ('partner','Partner'),
        ('other-users','Other Users'),
        ('team','Team')
    ]
    INWARD_TYPE_CHOICES = [
        ('returnable', 'Returnable'),
        ('non-returnable', 'Non-returnable'),
    ]

    # Choices for Reference To
    REFERENCE_TO_CHOICES = [
        ('task', 'Task'),
        ('regular', 'Regular'),
    ]
    id = models.AutoField(primary_key=True)
    company = models.CharField(max_length=100, verbose_name="Company")
    inward_for = models.CharField(max_length=100, 
                                  choices=INWARD_FOR_CHOICES, 
                                  verbose_name="Inward For")
    inward_type = models.CharField(
        max_length=50,
        choices=INWARD_TYPE_CHOICES,
        verbose_name="Inward Type"
    )
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE,
                                verbose_name="Customer",
                                related_name='inward_for_customer'
    )
    reference_to = models.CharField(
        max_length=50,
        choices=REFERENCE_TO_CHOICES,
        verbose_name="Reference To"
    )
    inward_title = models.CharField(max_length=120, verbose_name="Inward Title")
    description = models.TextField(verbose_name="Description / Remarks")
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, blank=True, null=True, 
                                 verbose_name="Location", related_name="inward_location")
    file = models.CharField(max_length=200, null=True, blank=True)
    through = models.CharField(max_length=255, verbose_name="Through")
    created_date = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='inward_created')
    modified_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='inward_modified')
    modified_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.inward_title

