from django.db import models
from clients.models import Customer
from custom_auth.models import CustomUser
from workflow.models import ClientWorkCategoryAssignment

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
    task = models.ForeignKey(
        ClientWorkCategoryAssignment,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='inward_for_task'
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


class Outward(models.Model):
    # Choices for Outward Reference
    OUTWARD_REFERENCE_CHOICES = [
        ('non-inward-entry', 'Non-Inward Entry'),
        ('inward-entry', 'Inward Entry'),
    ]
    OUTWARD_THROUGH_CHOICES = [
        ('by_courier', 'By Courier'),
        ('hand_over_to_client', 'Hand over to client in-person'),
        ('sent_via_office_boy', 'Sent Via Office Boy'),
    ]

    # Customer field (Foreign Key)
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        verbose_name="Customer",
        related_name='outward_customer'
    )
    outward_reference = models.CharField(
        max_length=50,
        choices=OUTWARD_REFERENCE_CHOICES,
        verbose_name="Outward Reference"
    )
    inward = models.ForeignKey(
        Inward,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Inward Entry",
        related_name='outward_inward'
    )
    company = models.CharField(max_length=100, verbose_name="Company")
    outward_title = models.CharField(max_length=120, verbose_name="Outward Title")
    about_outward = models.TextField(verbose_name="About Outward")
    outward_through = models.CharField(max_length=100, choices=OUTWARD_THROUGH_CHOICES, verbose_name="Outward Through")
    # in case of courier
    avb_no = models.CharField(max_length=100, blank=True, null=True)
    courier_name = models.CharField(max_length=100, blank=True, null=True)
    # in other two cases
    name_of_person = models.CharField(max_length=100, blank=True, null=True)
    
    outward_date = models.DateField(verbose_name="Outward Date")
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='outward_created',
        verbose_name="Created By"
    )
    created_date = models.DateTimeField(auto_now_add=True, verbose_name="Created Date")
    modified_by = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='outward_modified',
        verbose_name="Modified By"
    )
    modified_date = models.DateTimeField(auto_now=True, verbose_name="Modified Date")

    def __str__(self):
        return self.outward_title
