from django.db import models
from workflow.models import ClientWorkCategoryAssignment
from clients.models import Customer
from custom_auth.models import CustomUser


# Create your models here.
class Expense(models.Model):
    id = models.AutoField(primary_key=True)
    work = models.ForeignKey(ClientWorkCategoryAssignment, on_delete=models.CASCADE, related_name="task_expense")
    expense_name = models.CharField(max_length=100, null=True, blank=True)
    expense_amount = models.FloatField(blank=True, null=True, default=0)
    expense_date = models.DateTimeField(auto_now=True)
    file = models.CharField(max_length=255, null=True, blank=True, default=0)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='expense_created')
    created_date = models.DateTimeField(auto_now_add=True, verbose_name="Created Date")    
    updated_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='expense_updated')
    updated_date = models.DateTimeField(auto_now=True, verbose_name="Updated Date")

    def __str__(self):
        return f"{self.expense_name}"
    
    

