from django.db import models

class Company(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    billing_address = models.CharField(max_length=300)
    destination_address = models.TextField(blank=True, null=True)
    pan_no = models.CharField(max_length=20)
    gst_no = models.CharField(max_length=50, blank=True, null=True)
    state_code_gst = models.CharField(max_length=10, blank=True, null=True)
    place_of_supply = models.CharField(max_length=100, blank=True, null=True)
    mobile_no = models.CharField(max_length=15, blank=True, null=True)
    telephone_no = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    cin = models.CharField(max_length=50, blank=True, null=True)
    terms_and_conditions = models.TextField(blank=True, null=True)
    logo = models.CharField(max_length=255, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class BankDetails(models.Model):
    id = models.AutoField(primary_key=True)
    company = models.ForeignKey(Company, related_name='bank_details', on_delete=models.CASCADE)
    bank_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=50)
    account_holder_name = models.CharField(max_length=255)
    ifsc_code = models.CharField(max_length=20)
    branch = models.CharField(max_length=100, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.bank_name} - {self.account_number}"