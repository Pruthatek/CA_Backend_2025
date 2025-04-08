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
    due_date = models.DateField(verbose_name="Due Date", blank=True, null=True)
    proforma_invoice = models.BooleanField(default=False, verbose_name="Proforma Invoice")
    requested_by = models.CharField(max_length=255, verbose_name="Requested By")
    hrs_spent = models.FloatField(default=0.00, null=True, blank=True)
    task = models.CharField(max_length=125, blank=True, null=True)
    narration = models.CharField(max_length=255, blank=True, null=True, verbose_name="Narration")
    sub_total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Sub Total")
    discount = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Discount")
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Discount Amount")
    gst = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="GST(18%)")
    include_expense = models.BooleanField(default=False)
    gst_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="GST amount")
    sgst = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="SGST(9%)", default=0.0)
    sgst_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="SGST amount", default=0.0)
    cgst = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="CGST(9%)", default=0.0)
    cgst_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="CGST_amount", default=0.0)
    total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total")
    round_off = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Round Off")
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Net Amount")
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Paid Amount", default=0)
    unpaid_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Unpaid Amount")
    final_paid_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Paid Amount", default=0)
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
    hsn_code = models.CharField(max_length=255, verbose_name="hsn_code", null=True)
    narration = models.CharField(max_length=255, verbose_name="narration", null=True, blank=True)
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
    


class CreditNote(models.Model):
    TYPE_OF_SUPPLY = [ ("b2b","B2B"), ("sezwp","SEZWP"), 
                      ("sezwop","SEZWOP"), ("expwop","EXPWOP"), 
                      ("dexp","DEXP"), ("b2c","B2C")]

    REASONS_LIST = [ 
                    ("sales_return","Sales Return"), 
                    ("post_sales_discount","Post sales Discount"), 
                    ("deficiency_in_service","Deficiency In Service"), 
                    ("correction_in_invoice","Correction in invoice"), 
                    ("change_in_pos","Change in POS"), 
                    ("finalization_of_provisional_assessment","Finalization of provisional Assessment"), 
                    ("others","Others")]        
    # Main fields
    billing_company = models.CharField(max_length=255, verbose_name="Billing Company")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='customer_credit')
    reason = models.CharField(max_length=255, choices=REASONS_LIST, default='others')
    type_of_supply = models.CharField(max_length=100, choices=TYPE_OF_SUPPLY, verbose_name="Type Of Supply")
    place_of_supply = models.CharField(max_length=100, verbose_name="Place Of Supply")
    credit_note_date = models.DateField(verbose_name="Credit Note Date")
    bill_no_to_be_adjusted = models.CharField(max_length=100, verbose_name="Bill No. to be Adjusted")
    gst = models.DecimalField(
        max_digits=5, decimal_places=2, default=18.00, verbose_name="GST (%)")
    total = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name="Total")
    credit_note_amount = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name="Credit Note Amount")
    
    # Timestamps
    created_date = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="credit_note_created_by")
    updated_date = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="credit_note_updated_by")

    def __str__(self):
        return f"Credit Note - {self.bill_no_to_be_adjusted}"


class CreditNoteItem(models.Model):
    # ForeignKey to CreditNote
    credit_note = models.ForeignKey(
        CreditNote, on_delete=models.CASCADE, related_name="items",
        verbose_name="Credit Note"
    )
    item_name = models.CharField(max_length=255, verbose_name="Item Name")
    hsn_no = models.CharField(max_length=255, blank=True, null=True)
    unit_price = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name="Unit Price")

    def __str__(self):
        return f"{self.item_name} - {self.hsn_no}"


class DebitNote(models.Model):
    # Main fields
    TYPE_OF_SUPPLY = [ ("b2b","B2B"), ("sezwp","SEZWP"), 
                      ("sezwop","SEZWOP"), ("expwop","EXPWOP"), 
                      ("dexp","DEXP"), ("b2c","B2C")]

    REASONS_LIST = [ 
                    ("sales_return","Sales Return"), 
                    ("post_sales_discount","Post sales Discount"), 
                    ("deficiency_in_service","Deficiency In Service"), 
                    ("correction_in_invoice","Correction in invoice"), 
                    ("change_in_pos","Change in POS"), 
                    ("finalization_of_provisional_assessment","Finalization of provisional Assessment"), 
                    ("others","Others")]
    
    billing_company = models.CharField(max_length=255, verbose_name="Billing Company")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='customer_debit')
    reason = models.CharField(max_length=255, choices=REASONS_LIST, verbose_name="Reason", null=True, blank=True)
    type_of_supply = models.CharField(max_length=100, choices=TYPE_OF_SUPPLY, verbose_name="Type Of Supply")
    place_of_supply = models.CharField(max_length=100, verbose_name="Place Of Supply")
    debit_note_date = models.DateField(verbose_name="Debit Note Date")
    bill_no_to_be_adjusted = models.CharField(max_length=100, verbose_name="Bill No. to be Adjusted")
    gst = models.DecimalField(
        max_digits=5, decimal_places=2, default=18.00, verbose_name="GST (%)")
    total = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name="Total")
    debit_note_amount = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name="Debit Note Amount")

    # Timestamps
    created_date = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="debit_note_created_by")
    updated_date = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="debit_note_updated_by")

    def __str__(self):
        return f"Debit Note - {self.bill_no_to_be_adjusted}"


class DebitNoteItem(models.Model):
    # ForeignKey to DebitNote
    debit_note = models.ForeignKey(
        DebitNote, on_delete=models.CASCADE, related_name="items",
        verbose_name="Debit Note"
    )

    # Item details
    item_name = models.CharField(max_length=255, verbose_name="Item Name")
    hsn_no = models.CharField(max_length=255, blank=True, null=True, verbose_name="HSN No.")
    unit_price = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name="Unit Price")

    def __str__(self):
        return f"{self.item_name} - {self.hsn_no}"