from django.db import models
from clients.models import Customer
from custom_auth.models import CustomUser
from workflow.models import ClientWorkCategoryAssignment
from expense.models import Expense


class Billing(models.Model):
    TYPE_OF_SUPPLY = [ ("b2b","B2B"), ("sezwp","SEZWP"), 
                      ("sezwop","SEZWOP"), ("expwop","EXPWOP"), 
                      ("dexp","DEXP"), ("b2c","B2C")]
    BILL_TYPES = [("adhoc", "AD-HOC"), ("structured", "Structured")]
    STATUS_TYPES = [("unpaid","Unpaid"),
                    ("partially-paid","Partially-paid"),
                    ("paid","Paid"),
                    ]


    bill_type = models.CharField(max_length=20, choices=BILL_TYPES, default="adhoc")
    billing_company = models.CharField(max_length=255, verbose_name="Billing Company")
    bank = models.CharField(max_length=255, verbose_name="Bank")
    financial_year = models.CharField(max_length=10, verbose_name="Financial Year")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="customer_bill")
    type_of_supply = models.CharField(max_length=10, choices=TYPE_OF_SUPPLY, verbose_name="Type Of Supply", default="b2b")
    place_of_supply = models.CharField(max_length=100, verbose_name="Place Of Supply", null=True, blank=True)
    billing_description = models.TextField(verbose_name="Billing Description")
    fees = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Fees")
    invoice_date = models.DateField(verbose_name="Invoice Date")
    proforma_invoice = models.BooleanField(default=False, verbose_name="Proforma Invoice")
    requested_by = models.CharField(max_length=255, verbose_name="Requested By")
    narration = models.TextField(verbose_name="Narration")
    sub_total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Sub Total")
    discount = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Discount")
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Discount Amount")
    gst = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="GST(18%)")
    gst_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="GST amount")
    total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total")
    round_off = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Round Off")
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Net Amount")
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Paid Amount", default=0)
    unpaid_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Unpaid Amount")
    payment_status = models.CharField(max_length=50, choices=STATUS_TYPES,  default="unpaid")
    reverse_charges = models.BooleanField(default=False, verbose_name="Reverse Charges")
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, related_name="bill_created"
    )
    created_date = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, related_name="bill_updated"
    )
    updated_date = models.DateTimeField(auto_now=True)



    def __str__(self):
        return f"{self.billing_company} - {self.customer} - {self.invoice_date}"

    class Meta:
        verbose_name = "Billing"
        verbose_name_plural = "Billings"


class BillItems(models.Model):
    id = models.AutoField(primary_key=True)
    bill = models.ForeignKey(Billing, on_delete=models.CASCADE, related_name='bill_items')
    task_name = models.CharField(max_length=255, verbose_name="task_name", null=True)
    work_category = models.ForeignKey(ClientWorkCategoryAssignment, on_delete=models.SET_NULL, null=True, blank=True, related_name="bill_task")
    hsn_code = models.CharField(max_length=255, verbose_name="task_name", null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Item Amount")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.task_name}"



class ExpenseItems(models.Model):
    id = models.AutoField(primary_key=True)
    bill = models.ForeignKey(Billing, on_delete=models.CASCADE, related_name='expense_items')
    expense_description = models.CharField(max_length=255, verbose_name="expense_description", null=True)
    expense_type = models.CharField(max_length=255, verbose_name="expense_type", null=True)
    expense = models.ForeignKey(Expense, on_delete=models.SET_NULL, null=True, blank=True, related_name="expense_item")
    hsn_code = models.CharField(max_length=255, verbose_name="hsn_code", null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Expense Amount")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.id}"


class Receipt(models.Model):
    company = models.CharField(max_length=255)
    deposit_to = models.CharField(max_length=255)
    payment_date = models.DateField()
    receipt_no = models.CharField(max_length=100, unique=True)
    client = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='customer_receipt')
    payment_amount = models.DecimalField(max_digits=12, decimal_places=2)
    unsettled_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    other_charges = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    payment_type = models.CharField(max_length=100)
    description = models.TextField()
    
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='receipts_created')
    created_date = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='receipts_updated')
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Receipt {self.receipt_no} - {self.client}" 


class ReceiptInvoice(models.Model):
    receipt = models.ForeignKey(Receipt, on_delete=models.CASCADE, related_name='receipt_invoice')
    invoice = models.ForeignKey(Billing, on_delete=models.CASCADE, related_name='bill_details')
    invoice_amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment = models.DecimalField(max_digits=12, decimal_places=2)
    tds_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    waived_off = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    def __str__(self):
        return f"Invoice {self.invoice} - Receipt {self.receipt.receipt_no}"
    

