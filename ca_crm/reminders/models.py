from django.db import models
from billing.models import Billing
from clients.models import Customer
from custom_auth.models import CustomUser


class Reminders(models.Model):
    id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="customer_reminder")
    billing = models.ForeignKey(Billing, on_delete=models.SET_NULL, null=True, blank=True, related_name="billing_reminder")
    type_of_reminder = models.CharField(max_length=100, blank=True, null=True)
    reminder_title = models.CharField(max_length=200, null=True, blank=True)
    content = models.TextField(null=True, blank=True)
    reminder_date = models.DateField(null=True, blank=True)
    to_email = models.CharField(max_length=200, null=True, blank=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="reminder_created_by")
    created_date = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name="reminder_updated_by")
    updated_date = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.customer} - {self.reminder_title}"

    


