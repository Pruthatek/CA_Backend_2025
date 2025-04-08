from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.core.files.storage import FileSystemStorage
from decimal import Decimal
import os
from django.db import transaction
import posixpath
from .models import (Billing, 
                     BillItems, 
                     ExpenseItems, 
                     Customer, 
                     ClientWorkCategoryAssignment, 
                     Expense, 
                     CustomUser,
                     Receipt,
                     CreditNote,
                     CreditNoteItem,
                     DebitNote,
                     DebitNoteItem,
                     ReceiptInvoice)
from workflow.views import ModifiedApiview
from ca_crm.email_service import send_email
from django.db.models.functions import Coalesce
from django.db.models import Value


class BillingCreateView(ModifiedApiview):
    def post(self, request):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)

            # Extract data from the request
            bill_type = request.data.get('bill_type', 'adhoc')
            billing_company = request.data.get('billing_company')
            bank = request.data.get('bank')
            financial_year = request.data.get('financial_year')
            customer_id = request.data.get('customer')
            type_of_supply = request.data.get('type_of_supply', 'b2b')
            place_of_supply = request.data.get('place_of_supply')
            billing_description = request.data.get('billing_description')
            fees = request.data.get('fees')
            invoice_date = request.data.get('invoice_date')
            due_date = request.data.get('due_date')
            proforma_invoice = request.data.get('proforma_invoice', False)
            requested_by = request.data.get('requested_by')
            narration = request.data.get('narration')
            hrs_spent = request.data.get('hrs_spent')
            task = request.data.get('task')
            include_expense = request.data.get('include_expense', False)
            sub_total = request.data.get('sub_total')
            discount = request.data.get('discount')
            discount_amount = request.data.get('discount_amount')
            gst = request.data.get('gst')
            gst_amount = request.data.get('gst_amount')
            sgst = request.data.get('sgst',0)
            sgst_amount = request.data.get('sgst_amount',0)
            cgst = request.data.get('cgst',0)
            cgst_amount = request.data.get('cgst_amount',0)
            total = request.data.get('total')
            round_off = request.data.get('round_off')
            net_amount = request.data.get('net_amount')
            reverse_charges = request.data.get('reverse_charges', False)
            payment_status="unpaid"
            bill_items = request.data.get('bill_items', [])
            expense_items = request.data.get('expense_items', [])

            # Validate required fields
            if not all([billing_company, 
                        bank, 
                        financial_year, 
                        customer_id, 
                        billing_description, 
                        fees, 
                        invoice_date, requested_by, sub_total, total, net_amount]):
                return Response(
                    {"error": "Required fields are missing."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Fetch related objects
            customer = get_object_or_404(Customer, id=customer_id)

            # Create the Billing object
            with transaction.atomic():
                billing_obj = Billing.objects.create(
                    bill_type=bill_type,
                    billing_company=billing_company,
                    bank=bank,
                    financial_year=financial_year,
                    customer=customer,
                    type_of_supply=type_of_supply,
                    place_of_supply=place_of_supply,
                    billing_description=billing_description,
                    fees=fees,
                    invoice_date=invoice_date,
                    due_date=due_date,
                    proforma_invoice=proforma_invoice,
                    hrs_spent=hrs_spent,
                    task=task,
                    include_expense=include_expense,
                    requested_by=requested_by,
                    narration=narration,
                    sub_total=sub_total,
                    discount=discount,
                    discount_amount=discount_amount,
                    gst=gst,
                    gst_amount=gst_amount,
                    sgst=sgst,
                    sgst_amount=sgst_amount,
                    cgst=cgst,
                    cgst_amount=cgst_amount,
                    total=total,
                    round_off=round_off,
                    net_amount=net_amount,
                    paid_amount=0,
                    unpaid_amount=net_amount,
                    reverse_charges=reverse_charges,
                    payment_status=payment_status,
                    created_by=user,
                    updated_by=user
                )

                # Create BillItems for the billing
                work_category = None
                for item in bill_items:
                    if bill_type == 'structured':
                        work_category = get_object_or_404(ClientWorkCategoryAssignment, assignment_id=item.get("assignment_id"))
                
                    BillItems.objects.create(
                        bill=billing_obj,
                        task_name=item.get('task_name'),
                        work_category=work_category if bill_type == 'structured' else None,
                        hsn_code=item.get('hsn_code'),
                        amount=item.get('amount'),
                        narration=item.get('narration')
                    )

                # Create ExpenseItems for the billing
                if expense_items:
                    for expense in expense_items:
                        ExpenseItems.objects.create(
                            bill=billing_obj,
                            expense_description=expense.get('expense_description'),
                            expense_type=expense.get('expense_type'),
                            expense=get_object_or_404(Expense, id=expense.get('expense_id')) if expense.get('expense_id',None) else None,
                            hsn_code=expense.get('hsn_code'),
                            amount=expense.get('amount')
                        )
            return Response({"message":"bill_created_successfully", "bill_id":billing_obj.id}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

class BillingListView(ModifiedApiview):
    def get(self, request):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)

            bills = Billing.objects.all().values(
                'id', 'bill_type', 'billing_company', 'customer__name_of_business', 'invoice_date', "due_date", 'total', 'payment_status'
            )

            return Response(bills, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BillingRetrieveView(ModifiedApiview):
    def get(self, request, bill_id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)

            billing_obj = get_object_or_404(Billing, id=bill_id)
            bill_items = BillItems.objects.filter(bill=billing_obj).annotate(
                assignment_id=Coalesce("work_category__assignment_id", Value(None))
            ).values("id", "assignment_id", 'task_name', 'hsn_code', 'amount', "narration")

            expense_items = ExpenseItems.objects.filter(bill=billing_obj).annotate(
                expense__id=Coalesce("expense__id", Value(None))
            ).values("id", "expense__id", 'expense_description', 'expense_type', 'hsn_code', 'amount')
            billing_details = {
                "id": billing_obj.id,
                "bill_type": billing_obj.bill_type,
                "billing_company": billing_obj.billing_company,
                "bank": billing_obj.bank,
                "financial_year": billing_obj.financial_year,
                "customer": billing_obj.customer.name_of_business,
                "customer_id": billing_obj.customer.id,
                "type_of_supply": billing_obj.type_of_supply,
                "place_of_supply": billing_obj.place_of_supply,
                "billing_description": billing_obj.billing_description,
                "fees": billing_obj.fees,
                "invoice_date": billing_obj.invoice_date,
                "due_date": billing_obj.due_date,
                "proforma_invoice": billing_obj.proforma_invoice,
                "requested_by": billing_obj.requested_by,
                "narration": billing_obj.narration,
                "sub_total": billing_obj.sub_total,
                "hrs_spent": billing_obj.hrs_spent,
                "task": billing_obj.task,
                "include_expense": billing_obj.include_expense,
                "discount": billing_obj.discount,
                "discount_amount": billing_obj.discount_amount,
                "gst": billing_obj.gst,
                "gst_amount": billing_obj.gst_amount,
                "sgst": billing_obj.sgst,
                "sgst_amount": billing_obj.sgst_amount,
                "cgst": billing_obj.cgst,
                "cgst_amount": billing_obj.cgst_amount,
                "total": billing_obj.total,
                "round_off": billing_obj.round_off,
                "net_amount": billing_obj.net_amount,
                "reverse_charges": billing_obj.reverse_charges,
                "paid_amount": billing_obj.paid_amount,
                "unpaid_amount": billing_obj.unpaid_amount,
                "final_paid_amount": billing_obj.final_paid_amount,
                "payment_status": billing_obj.payment_status,
                "bill_items": list(bill_items),
                "expense_items": list(expense_items)
            }

            return Response(billing_details, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BillingUpdateView(ModifiedApiview):
    def put(self, request, bill_id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)

            # Fetch the existing billing object
            billing_obj = get_object_or_404(Billing, id=bill_id)

            # Extract data from the request
            bill_type = request.data.get('bill_type', billing_obj.bill_type)
            billing_company = request.data.get('billing_company', billing_obj.billing_company)
            bank = request.data.get('bank', billing_obj.bank)
            financial_year = request.data.get('financial_year', billing_obj.financial_year)
            customer_id = request.data.get('customer', billing_obj.customer.id)
            type_of_supply = request.data.get('type_of_supply', billing_obj.type_of_supply)
            place_of_supply = request.data.get('place_of_supply', billing_obj.place_of_supply)
            billing_description = request.data.get('billing_description', billing_obj.billing_description)
            fees = request.data.get('fees', billing_obj.fees)
            invoice_date = request.data.get('invoice_date', billing_obj.invoice_date)
            due_date = request.data.get('due_date', billing_obj.due_date)
            proforma_invoice = request.data.get('proforma_invoice', billing_obj.proforma_invoice)
            requested_by = request.data.get('requested_by', billing_obj.requested_by)
            narration = request.data.get('narration', billing_obj.narration)
            task = request.data.get('task', billing_obj.task)
            hrs_spent = request.data.get('hrs_spent', billing_obj.hrs_spent)
            include_expense = request.data.get('include_expense', billing_obj.include_expense)
            sub_total = request.data.get('sub_total', billing_obj.sub_total)
            discount = request.data.get('discount', billing_obj.discount)
            discount_amount = request.data.get('discount_amount', billing_obj.discount_amount)
            gst = request.data.get('gst', billing_obj.gst)
            gst_amount = request.data.get('gst_amount', billing_obj.gst_amount)
            sgst = request.data.get('sgst', billing_obj.sgst)
            sgst_amount = request.data.get('sgst_amount', billing_obj.sgst_amount)
            cgst = request.data.get('cgst', billing_obj.cgst)
            cgst_amount = request.data.get('cgst_amount', billing_obj.cgst_amount)
            total = request.data.get('total', billing_obj.total)
            round_off = request.data.get('round_off', billing_obj.round_off)
            net_amount = request.data.get('net_amount', billing_obj.net_amount)
            paid_amount = request.data.get('paid_amount', billing_obj.paid_amount)
            unpaid_amount = request.data.get('unpaid_amount', billing_obj.unpaid_amount)
            reverse_charges = request.data.get('reverse_charges', billing_obj.reverse_charges)
            bill_items = request.data.get('bill_items', [])
            expense_items = request.data.get('expense_items', [])

            # Fetch related objects
            customer = get_object_or_404(Customer, id=customer_id)
            
            with transaction.atomic():            
                # Update the Billing object
                billing_obj.bill_type = bill_type
                billing_obj.billing_company = billing_company
                billing_obj.bank = bank
                billing_obj.financial_year = financial_year
                billing_obj.customer = customer
                billing_obj.type_of_supply = type_of_supply
                billing_obj.place_of_supply = place_of_supply
                billing_obj.billing_description = billing_description
                billing_obj.fees = fees
                billing_obj.invoice_date = invoice_date
                billing_obj.proforma_invoice = proforma_invoice
                billing_obj.requested_by = requested_by
                billing_obj.narration = narration
                billing_obj.sub_total = sub_total
                billing_obj.hrs_spent = hrs_spent
                billing_obj.task = task
                billing_obj.include_expense = include_expense
                billing_obj.discount = discount
                billing_obj.discount_amount = discount_amount
                billing_obj.gst = gst
                billing_obj.gst_amount = gst_amount
                billing_obj.sgst = sgst
                billing_obj.sgst_amount = sgst_amount
                billing_obj.cgst = cgst
                billing_obj.cgst_amount = cgst_amount
                billing_obj.total = total
                billing_obj.round_off = round_off
                billing_obj.net_amount = net_amount
                billing_obj.paid_amount = paid_amount
                billing_obj.unpaid_amount = unpaid_amount
                billing_obj.reverse_charges = reverse_charges
                billing_obj.updated_by = user
                billing_obj.save()

            # Update or Create BillItems
                existing_bill_items = {item.id: item for item in billing_obj.bill_items.all()}
                work_category = None
                for item_data in bill_items:
                    item_id = item_data.get('id')
                    if item_id and item_id in existing_bill_items:
                        # Update existing BillItem
                        if bill_type == 'structured':
                            work_category = get_object_or_404(ClientWorkCategoryAssignment, assignment_id=item_data.get("assignment_id"))
                        
                        bill_item = existing_bill_items[item_id]
                        bill_item.task_name = item_data.get('task_name', bill_item.task_name)
                        bill_item.work_category = work_category if bill_type == 'structured' else None
                        bill_item.hsn_code = item_data.get('hsn_code', bill_item.hsn_code)
                        bill_item.amount = item_data.get('amount', bill_item.amount)
                        bill_item.save()
                    else:
                        # Create new BillItem
                        BillItems.objects.create(
                            bill=billing_obj,
                            task_name=item_data.get('task_name'),
                            work_category=work_category if bill_type == 'structured' else None,
                            hsn_code=item_data.get('hsn_code'),
                            amount=item_data.get('amount')
                        )

                # Delete BillItems not in the request
                requested_bill_item_ids = {item_data.get('id') for item_data in bill_items if item_data.get('id')}
                for item_id, item in existing_bill_items.items():
                    if item_id not in requested_bill_item_ids:
                        item.delete()

                # Update or Create ExpenseItems
                existing_expense_items = {item.id: item for item in billing_obj.expense_items.all()}
                for expense_data in expense_items:
                    expense_id = expense_data.get('id')
                    if expense_id and expense_id in existing_expense_items:
                        # Update existing ExpenseItem
                        expense_item = existing_expense_items[expense_id]
                        expense_item.expense_description = expense_data.get('expense_description', expense_item.expense_description)
                        expense_item.expense_type = expense_data.get('expense_type', expense_item.expense_type)
                        expense_item.expense = get_object_or_404(Expense, id=expense_data.get('expense_id')) if bill_type == 'structured' else None
                        expense_item.hsn_code = expense_data.get('hsn_code', expense_item.hsn_code)
                        expense_item.amount = expense_data.get('amount', expense_item.amount)
                        expense_item.save()
                    else:
                        # Create new ExpenseItem
                        ExpenseItems.objects.create(
                            bill=billing_obj,
                            expense_description=expense_data.get('expense_description'),
                            expense_type=expense_data.get('expense_type'),
                            expense=get_object_or_404(Expense, id=expense_data.get('work_category_id')) if expense_data.get('work_category_id', None) else None,
                            hsn_code=expense_data.get('hsn_code'),
                            amount=expense_data.get('amount')
                        )

                # Delete ExpenseItems not in the request
                requested_expense_item_ids = {expense_data.get('id') for expense_data in expense_items if expense_data.get('id')}
                for expense_id, expense_item in existing_expense_items.items():
                    if expense_id not in requested_expense_item_ids:
                        expense_item.delete()

            # Serialize the updated billing object
            return Response({"message":"Invoice Updated successfully"}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )                


class BillingDeleteView(ModifiedApiview):
    def delete(self, request, bill_id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)

            billing_obj = get_object_or_404(Billing, id=bill_id)
            billing_obj.is_active = False
            billing_obj.save()

            return Response({"message": "Billing deleted successfully"}, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class ReceiptCreateAPIView(ModifiedApiview):
    def post(self, request, *args, **kwargs):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            # Extract data from the request
            data = request.data
            client_id=data.get('client')
            client = get_object_or_404(Customer, id=client_id)

            # Create the Receipt record
            with transaction.atomic():
                receipt = Receipt(
                    company=data.get('company'),
                    deposit_to=data.get('deposit_to'),
                    payment_date=data.get('payment_date'),
                    receipt_no=data.get('receipt_no'),
                    client=client,
                    payment_amount=data.get('payment_amount'),
                    unsettled_amount=data.get('unsettled_amount', 0.00),
                    other_charges=data.get('other_charges', 0.00),
                    payment_type=data.get('payment_type'),
                    description=data.get('description'),
                    created_by=user,
                )
                receipt.save()

                # Create the ReceiptInvoice records and update Billing (Invoice) records
                for invoice_data in data.get('invoices', []):
                    invoice = get_object_or_404(Billing, id=invoice_data.get('invoice_id'))

                    # Calculate new paid and unpaid amounts for the invoice
                    new_paid_amount = Decimal(invoice.paid_amount) + Decimal(invoice_data.get('payment', 0.00))
                    new_unpaid_amount = Decimal(invoice.unpaid_amount) - Decimal(invoice_data.get('payment', 0.00))

                    # Ensure unpaid amount doesn't go negative
                    if new_unpaid_amount < 0:
                        new_unpaid_amount = 0

                    # Update the Billing (Invoice) record
                    invoice.paid_amount = new_paid_amount
                    invoice.unpaid_amount = new_unpaid_amount
                    invoice.save()

                    # Create the ReceiptInvoice record
                    receipt_invoice = ReceiptInvoice(
                        receipt=receipt,
                        invoice=invoice,
                        invoice_amount=invoice_data.get('invoice_amount'),
                        payment=invoice_data.get('payment'),
                        tds_deduction=invoice_data.get('tds_deduction', 0.00),
                        waived_off=invoice_data.get('waived_off', 0.00),
                    )
                    receipt_invoice.save()

            return Response({"message": "Receipt and invoices created successfully"}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )                


class ReceiptUpdateAPIView(ModifiedApiview):
    def put(self, request, id, *args, **kwargs):
        # Extract data from the request
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)

            data = request.data

            # Get the existing Receipt record
            receipt = get_object_or_404(Receipt, id=id)
            client = get_object_or_404(Customer, id=data.get('client'))

            # Update the Receipt record
            receipt.company = data.get('company', receipt.company)
            receipt.deposit_to = data.get('deposit_to', receipt.deposit_to)
            receipt.payment_date = data.get('payment_date', receipt.payment_date)
            receipt.client = client
            receipt.payment_amount = data.get('payment_amount', receipt.payment_amount)
            receipt.unsettled_amount = data.get('unsettled_amount', receipt.unsettled_amount)
            receipt.other_charges = data.get('other_charges', receipt.other_charges)
            receipt.payment_type = data.get('payment_type', receipt.payment_type)
            receipt.description = data.get('description', receipt.description)
            receipt.updated_by = user
            receipt.save()

            # Update or create the ReceiptInvoice records and update Billing (Invoice) records
            for invoice_data in data.get('invoices', []):
                invoice = get_object_or_404(Billing, id=invoice_data.get('invoice_id'))

                # Get the existing ReceiptInvoice record (if it exists)
                receipt_invoice, created = ReceiptInvoice.objects.get_or_create(
                    receipt=receipt,
                    invoice=invoice,
                    defaults={
                        'invoice_amount': invoice_data.get('invoice_amount'),
                        'payment': invoice_data.get('payment'),
                        'tds_deduction': invoice_data.get('tds_deduction', 0.00),
                        'waived_off': invoice_data.get('waived_off', 0.00),
                    }
                )

                # Calculate the difference in payment amount (if updating)
                if not created:
                    payment_difference = Decimal(invoice_data.get('payment', 0.00)) - Decimal(receipt_invoice.payment)
                else:
                    payment_difference = Decimal(invoice_data.get('payment', 0.00))

                # Update the Billing (Invoice) record
                invoice.paid_amount += Decimal(payment_difference)
                invoice.unpaid_amount -= Decimal(payment_difference)

                # Ensure unpaid amount doesn't go negative
                if invoice.unpaid_amount < 0:
                    invoice.unpaid_amount = 0

                invoice.save()

                # Update the ReceiptInvoice record
                if not created:
                    receipt_invoice.invoice_amount = invoice_data.get('invoice_amount', receipt_invoice.invoice_amount)
                    receipt_invoice.payment = invoice_data.get('payment', receipt_invoice.payment)
                    receipt_invoice.tds_deduction = invoice_data.get('tds_deduction', receipt_invoice.tds_deduction)
                    receipt_invoice.waived_off = invoice_data.get('waived_off', receipt_invoice.waived_off)
                    receipt_invoice.save()

            return Response({"message": "Receipt and invoices updated successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ReceiptListAPIView(ModifiedApiview):
    def get(self, request, *args, **kwargs):
        # Fetch all Receipt records
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)

            receipts = Receipt.objects.all()
            receipt_list = []

            for receipt in receipts:
                # Fetch associated ReceiptInvoice records
                receipt_invoices = ReceiptInvoice.objects.filter(receipt=receipt)
                invoice_list = []

                for invoice in receipt_invoices:
                    invoice_list.append({
                        "invoice_id": invoice.invoice.id,
                        "invoice_amount": invoice.invoice_amount,
                        "payment": invoice.payment,
                        "tds_deduction": invoice.tds_deduction,
                        "waived_off": invoice.waived_off,
                    })

                # Build the receipt data
                receipt_data = {
                    "id": receipt.id,
                    "company": receipt.company,
                    "deposit_to": receipt.deposit_to,
                    "payment_date": receipt.payment_date,
                    "receipt_no": receipt.receipt_no,
                    "client": receipt.client.name_of_business,
                    "client_id": receipt.client.id,
                    "payment_amount": receipt.payment_amount,
                    "unsettled_amount": receipt.unsettled_amount,
                    "other_charges": receipt.other_charges,
                    "payment_type": receipt.payment_type,
                    "description": receipt.description,
                    "is_active": receipt.is_active,
                    "created_by": receipt.created_by.id,
                    "created_date": receipt.created_date,
                    "updated_by": receipt.updated_by.id if receipt.updated_by else None,
                    "updated_date": receipt.updated_date,
                    "invoices": invoice_list,
                }
                receipt_list.append(receipt_data)

            return Response(receipt_list, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )     


class ReceiptRetrieveAPIView(ModifiedApiview):
    def get(self, request, id, *args, **kwargs):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)

            # Fetch the Receipt record
            receipt = get_object_or_404(Receipt, id=id)

            # Fetch associated ReceiptInvoice records
            receipt_invoices = ReceiptInvoice.objects.filter(receipt=receipt)
            invoice_list = []

            for invoice in receipt_invoices:
                invoice_list.append({
                    "invoice_id": invoice.invoice.id,
                    "invoice_amount": invoice.invoice_amount,
                    "payment": invoice.payment,
                    "tds_deduction": invoice.tds_deduction,
                    "waived_off": invoice.waived_off,
                })

            # Build the receipt data
            receipt_data = {
                "id": receipt.id,
                "company": receipt.company,
                "deposit_to": receipt.deposit_to,
                "payment_date": receipt.payment_date,
                "receipt_no": receipt.receipt_no,
                "client": receipt.client.name_of_business,
                "client_id": receipt.client.id,
                "payment_amount": receipt.payment_amount,
                "unsettled_amount": receipt.unsettled_amount,
                "other_charges": receipt.other_charges,
                "payment_type": receipt.payment_type,
                "description": receipt.description,
                "is_active": receipt.is_active,
                "created_by": receipt.created_by.id,
                "created_date": receipt.created_date,
                "updated_by": receipt.updated_by.id if receipt.updated_by else None,
                "updated_date": receipt.updated_date,
                "invoices": invoice_list,
            }

            return Response(receipt_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )     


class SendInvoiceAPIView(ModifiedApiview):
    def post(self, request):
        try:
            # Get user
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            attachments = request.FILES.get("invoice_pdf")
            if not attachments:
                Response({"message":"Error while fetching file"}, status=status.HTTP_400_BAD_REQUEST)
            extension = os.path.splitext(attachments.name)[1]
            if extension != "pdf":
                Response({"message":"Unsupported file format"}, status=status.HTTP_400_BAD_REQUEST)
            email_body = request.data.get("email_body")
            email_subject = request.data.get("email_subject")
            to_email = request.data.get("to_email")
            if isinstance(to_email, str):
                to_email = to_email.split(",")
            else:
                to_email = to_email
            print(to_email)
            email = send_email(subject=email_subject,
                               body=email_body,
                               to_emails=to_email,
                               attachment=attachments
                               )
            if email:
                return Response({"message":"Invoice Email sent successfully"}, status=status.HTTP_200_OK)
            else:
                return Response({"message":"Error while sending email"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"{e}"}, status=status.HTTP_400_BAD_REQUEST)


class ReceiptDeleteAPIView(ModifiedApiview):
    def delete(self, request, id, *args, **kwargs):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)

            # Fetch the Receipt record
            receipt = get_object_or_404(Receipt, id=id)

            # Fetch associated ReceiptInvoice records
            receipt_invoices = ReceiptInvoice.objects.filter(receipt=receipt)

            # Update the Billing (Invoice) records
            for receipt_invoice in receipt_invoices:
                invoice = receipt_invoice.invoice
                invoice.paid_amount -= receipt_invoice.payment
                invoice.unpaid_amount += receipt_invoice.payment

                # Ensure unpaid amount doesn't exceed the invoice amount
                if invoice.unpaid_amount > invoice.net_amount:
                    invoice.unpaid_amount = invoice.net_amount

                invoice.save()

            # Delete the ReceiptInvoice records
            receipt_invoices.delete()

            # Delete the Receipt record
            receipt.delete()

            return Response({"message": "Receipt and associated invoices deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )     


class CreditNoteCreateView(ModifiedApiview):
    def post(self, request):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)

            # Extract data from the request
            billing_company = request.data.get('billing_company')
            customer_id = request.data.get('customer')
            reason = request.data.get('reason', None)
            type_of_supply = request.data.get('type_of_supply')
            place_of_supply = request.data.get('place_of_supply')
            credit_note_date = request.data.get('credit_note_date')
            bill_no_to_be_adjusted = request.data.get('bill_no_to_be_adjusted')
            gst = request.data.get('gst', 18.00)
            total = request.data.get('total')
            credit_note_amount = request.data.get('credit_note_amount')
            items = request.data.get('items', [])

            # Validate required fields
            if not all([billing_company, customer_id, type_of_supply, place_of_supply, credit_note_date, bill_no_to_be_adjusted, total, credit_note_amount]):
                return Response(
                    {"error": "Required fields are missing."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if type_of_supply not in ["b2b", "sezwp", "sezwop", "expwop", "dexp", "b2c"]:
                return Response({"message": "pleases select proper type of supply"}, status=status.HTTP_400_BAD_REQUEST)
            
            if reason not in ["sales_return", "post_sales_discount", "deficiency_in_service", "correction_in_invoice", 
                              "change_in_pos", "finalization_of_provisional_assessment", "others"]:
                return Response({"message": "pleases select proper reason"}, status=status.HTTP_400_BAD_REQUEST)

            # Fetch related objects
            customer = get_object_or_404(Customer, id=customer_id)

            # Create the CreditNote object
            with transaction.atomic():
                credit_note = CreditNote.objects.create(
                    billing_company=billing_company,
                    customer=customer,
                    reason=reason,
                    type_of_supply=type_of_supply,
                    place_of_supply=place_of_supply,
                    credit_note_date=credit_note_date,
                    bill_no_to_be_adjusted=bill_no_to_be_adjusted,
                    gst=gst,
                    total=total,
                    credit_note_amount=credit_note_amount,
                    created_by=user,
                    updated_by=user
                )

                # Create CreditNoteItems for the credit note
                for item in items:
                    CreditNoteItem.objects.create(
                        credit_note=credit_note,
                        item_name=item.get('item_name'),
                        hsn_no=item.get('hsn_no', None),
                        unit_price=item.get('unit_price')
                    )

            return Response(
                {"message": "Credit note created successfully", "credit_note_id": credit_note.id},
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

class CreditNoteUpdateView(ModifiedApiview):
    def put(self, request, id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            # Fetch the existing CreditNote object
            credit_note = get_object_or_404(CreditNote, id=id)


            # Extract data from the request
            billing_company = request.data.get('billing_company', credit_note.billing_company)
            customer_id = request.data.get('customer', credit_note.customer.id)
            reason = request.data.get('reason', credit_note.reason)
            type_of_supply = request.data.get('type_of_supply', credit_note.type_of_supply)
            place_of_supply = request.data.get('place_of_supply', credit_note.place_of_supply)
            credit_note_date = request.data.get('credit_note_date', credit_note.credit_note_date)
            bill_no_to_be_adjusted = request.data.get('bill_no_to_be_adjusted', credit_note.bill_no_to_be_adjusted)
            gst = request.data.get('gst', credit_note.gst)
            total = request.data.get('total', credit_note.total)
            credit_note_amount = request.data.get('credit_note_amount', credit_note.credit_note_amount)
            items = request.data.get('items', [])

            if type_of_supply not in ["b2b", "sezwp", "sezwop", "expwop", "dexp", "b2c"]:
                return Response({"message": "pleases select proper type of supply"}, status=status.HTTP_400_BAD_REQUEST)
            
            if reason not in ["sales_return", "post_sales_discount", "deficiency_in_service", "correction_in_invoice", 
                              "change_in_pos", "finalization_of_provisional_assessment", "others"]:
                return Response({"message": "pleases select proper reason"}, status=status.HTTP_400_BAD_REQUEST)
            # Fetch related objects
            customer = get_object_or_404(Customer, id=customer_id)

            # Update the CreditNote object
            with transaction.atomic():
                credit_note.billing_company = billing_company
                credit_note.customer = customer
                credit_note.reason = reason
                credit_note.type_of_supply = type_of_supply
                credit_note.place_of_supply = place_of_supply
                credit_note.credit_note_date = credit_note_date
                credit_note.bill_no_to_be_adjusted = bill_no_to_be_adjusted
                credit_note.gst = gst
                credit_note.total = total
                credit_note.credit_note_amount = credit_note_amount
                credit_note.updated_by = user
                credit_note.save()

                # Delete existing CreditNoteItems
                credit_note.items.all().delete()

                # Create new CreditNoteItems for the credit note
                for item in items:
                    CreditNoteItem.objects.create(
                        credit_note=credit_note,
                        item_name=item.get('item_name'),
                        hsn_no=item.get('hsn_no', None),
                        unit_price=item.get('unit_price')
                    )

            return Response(
                {"message": "Credit note updated successfully", "credit_note_id": credit_note.id},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CreditNoteListView(ModifiedApiview):
    def get(self, request):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)

            # Fetch all CreditNote records
            credit_notes = CreditNote.objects.all()
            credit_note_list = []

            for credit_note in credit_notes:
                # Fetch associated CreditNoteItem records
                items = credit_note.items.all()
                item_list = []

                for item in items:
                    item_list.append({
                        "item_name": item.item_name,
                        "hsn_no": item.hsn_no,
                        "unit_price": item.unit_price
                    })

                # Build the credit note data
                credit_note_data = {
                    "id": credit_note.id,
                    "billing_company": credit_note.billing_company,
                    "customer": credit_note.customer.id,
                    "reason": credit_note.reason,
                    "type_of_supply": credit_note.type_of_supply,
                    "place_of_supply": credit_note.place_of_supply,
                    "credit_note_date": credit_note.credit_note_date,
                    "bill_no_to_be_adjusted": credit_note.bill_no_to_be_adjusted,
                    "gst": credit_note.gst,
                    "total": credit_note.total,
                    "credit_note_amount": credit_note.credit_note_amount,
                    "created_at": credit_note.created_date,
                    "updated_at": credit_note.updated_date,
                    "items": item_list
                }
                credit_note_list.append(credit_note_data)

            return Response(credit_note_list, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CreditNoteRetrieveView(ModifiedApiview):
    def get(self, request, id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)

            # Fetch the CreditNote record
            credit_note = get_object_or_404(CreditNote, id=id)

            # Fetch associated CreditNoteItem records
            items = credit_note.items.all()
            item_list = []

            for item in items:
                item_list.append({
                    "item_name": item.item_name,
                    "hsn_no": item.hsn_no,
                    "unit_price": item.unit_price
                })

            # Build the credit note data
            credit_note_data = {
                "id": credit_note.id,
                "billing_company": credit_note.billing_company,
                "customer": credit_note.customer.id,
                "reason": credit_note.reason,
                "type_of_supply": credit_note.type_of_supply,
                "place_of_supply": credit_note.place_of_supply,
                "credit_note_date": credit_note.credit_note_date,
                "bill_no_to_be_adjusted": credit_note.bill_no_to_be_adjusted,
                "gst": credit_note.gst,
                "total": credit_note.total,
                "credit_note_amount": credit_note.credit_note_amount,
                "created_at": credit_note.created_date,
                "updated_at": credit_note.updated_date,
                "items": item_list
            }

            return Response(credit_note_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CreditNoteDeleteView(ModifiedApiview):
    def delete(self, request, id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)

            # Fetch the CreditNote record
            credit_note = get_object_or_404(CreditNote, id=id)

            # Delete the CreditNote and its associated items
            with transaction.atomic():
                credit_note.items.all().delete()  # Delete associated items
                credit_note.delete()  # Delete the credit note

            return Response(
                {"message": "Credit note deleted successfully"},
                status=status.HTTP_204_NO_CONTENT
            )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DebitNoteCreateView(ModifiedApiview):
    def post(self, request):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)


            # Extract data from the request
            billing_company = request.data.get('billing_company')
            customer_id = request.data.get('customer')
            reason = request.data.get('reason', None)
            type_of_supply = request.data.get('type_of_supply')
            place_of_supply = request.data.get('place_of_supply')
            debit_note_date = request.data.get('debit_note_date')
            bill_no_to_be_adjusted = request.data.get('bill_no_to_be_adjusted')
            gst = request.data.get('gst', 18.00)
            total = request.data.get('total')
            debit_note_amount = request.data.get('debit_note_amount')
            items = request.data.get('items', [])

            # Validate required fields
            if not all([billing_company, customer_id, type_of_supply, place_of_supply, debit_note_date, bill_no_to_be_adjusted, total, debit_note_amount]):
                return Response(
                    {"error": "Required fields are missing."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Fetch related objects
            if type_of_supply not in ["b2b", "sezwp", "sezwop", "expwop", "dexp", "b2c"]:
                return Response({"message": "pleases select proper type of supply"}, status=status.HTTP_400_BAD_REQUEST)
            
            if reason not in ["sales_return", "post_sales_discount", "deficiency_in_service", "correction_in_invoice", 
                              "change_in_pos", "finalization_of_provisional_assessment", "others"]:
                return Response({"message": "pleases select proper reason"}, status=status.HTTP_400_BAD_REQUEST)

            customer = get_object_or_404(Customer, id=customer_id)

            # Create the DebitNote object
            with transaction.atomic():
                debit_note = DebitNote.objects.create(
                    billing_company=billing_company,
                    customer=customer,
                    reason=reason,
                    type_of_supply=type_of_supply,
                    place_of_supply=place_of_supply,
                    debit_note_date=debit_note_date,
                    bill_no_to_be_adjusted=bill_no_to_be_adjusted,
                    gst=gst,
                    total=total,
                    debit_note_amount=debit_note_amount,
                    created_by=user,
                    updated_by=user
                )

                # Create DebitNoteItems for the debit note
                for item in items:
                    DebitNoteItem.objects.create(
                        debit_note=debit_note,
                        item_name=item.get('item_name'),
                        hsn_no=item.get('hsn_no', None),
                        unit_price=item.get('unit_price')
                    )

            return Response(
                {"message": "Debit note created successfully", "debit_note_id": debit_note.id},
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

class DebitNoteUpdateView(ModifiedApiview):
    def put(self, request, id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)



            # Fetch the existing DebitNote object
            debit_note = get_object_or_404(DebitNote, id=id)

            # Extract data from the request
            billing_company = request.data.get('billing_company', debit_note.billing_company)
            customer_id = request.data.get('customer', debit_note.customer.id)
            reason = request.data.get('reason', debit_note.reason)
            type_of_supply = request.data.get('type_of_supply', debit_note.type_of_supply)
            place_of_supply = request.data.get('place_of_supply', debit_note.place_of_supply)
            debit_note_date = request.data.get('debit_note_date', debit_note.debit_note_date)
            bill_no_to_be_adjusted = request.data.get('bill_no_to_be_adjusted', debit_note.bill_no_to_be_adjusted)
            gst = request.data.get('gst', debit_note.gst)
            total = request.data.get('total', debit_note.total)
            debit_note_amount = request.data.get('debit_note_amount', debit_note.debit_note_amount)
            items = request.data.get('items', [])

            if type_of_supply not in ["b2b", "sezwp", "sezwop", "expwop", "dexp", "b2c"]:
                return Response({"message": "pleases select proper type of supply"}, status=status.HTTP_400_BAD_REQUEST)
            
            if reason not in ["sales_return", "post_sales_discount", "deficiency_in_service", "correction_in_invoice", 
                              "change_in_pos", "finalization_of_provisional_assessment", "others"]:
                return Response({"message": "pleases select proper reason"}, status=status.HTTP_400_BAD_REQUEST)
            
            # Fetch related objects
            customer = get_object_or_404(Customer, id=customer_id)

            # Update the DebitNote object
            with transaction.atomic():
                debit_note.billing_company = billing_company
                debit_note.customer = customer
                debit_note.reason = reason
                debit_note.type_of_supply = type_of_supply
                debit_note.place_of_supply = place_of_supply
                debit_note.debit_note_date = debit_note_date
                debit_note.bill_no_to_be_adjusted = bill_no_to_be_adjusted
                debit_note.gst = gst
                debit_note.total = total
                debit_note.debit_note_amount = debit_note_amount
                debit_note.updated_by = user
                debit_note.save()

                # Delete existing DebitNoteItems
                debit_note.items.all().delete()

                # Create new DebitNoteItems for the debit note
                for item in items:
                    DebitNoteItem.objects.create(
                        debit_note=debit_note,
                        item_name=item.get('item_name'),
                        hsn_no=item.get('hsn_no', None),
                        unit_price=item.get('unit_price')
                    )

            return Response(
                {"message": "Debit note updated successfully", "debit_note_id": debit_note.id},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DebitNoteListView(ModifiedApiview):
    def get(self, request):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)

            # Fetch all DebitNote records
            debit_notes = DebitNote.objects.all()
            debit_note_list = []

            for debit_note in debit_notes:
                # Fetch associated DebitNoteItem records
                items = debit_note.items.all()
                item_list = []

                for item in items:
                    item_list.append({
                        "item_name": item.item_name,
                        "hsn_no": item.hsn_no,
                        "unit_price": item.unit_price
                    })

                # Build the debit note data
                debit_note_data = {
                    "id": debit_note.id,
                    "billing_company": debit_note.billing_company,
                    "customer": debit_note.customer.id,
                    "reason": debit_note.reason,
                    "type_of_supply": debit_note.type_of_supply,
                    "place_of_supply": debit_note.place_of_supply,
                    "debit_note_date": debit_note.debit_note_date,
                    "bill_no_to_be_adjusted": debit_note.bill_no_to_be_adjusted,
                    "gst": debit_note.gst,
                    "total": debit_note.total,
                    "debit_note_amount": debit_note.debit_note_amount,
                    "created_at": debit_note.created_date,
                    "updated_at": debit_note.updated_date,
                    "items": item_list
                }
                debit_note_list.append(debit_note_data)

            return Response(debit_note_list, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DebitNoteRetrieveView(ModifiedApiview):
    def get(self, request, id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)

            # Fetch the DebitNote record
            debit_note = get_object_or_404(DebitNote, id=id)

            # Fetch associated DebitNoteItem records
            items = debit_note.items.all()
            item_list = []

            for item in items:
                item_list.append({
                    "item_name": item.item_name,
                    "hsn_no": item.hsn_no,
                    "unit_price": item.unit_price
                })

            # Build the debit note data
            debit_note_data = {
                "id": debit_note.id,
                "billing_company": debit_note.billing_company,
                "customer": debit_note.customer.id,
                "reason": debit_note.reason,
                "type_of_supply": debit_note.type_of_supply,
                "place_of_supply": debit_note.place_of_supply,
                "debit_note_date": debit_note.debit_note_date,
                "bill_no_to_be_adjusted": debit_note.bill_no_to_be_adjusted,
                "gst": debit_note.gst,
                "total": debit_note.total,
                "debit_note_amount": debit_note.debit_note_amount,
                "created_at": debit_note.created_date,
                "updated_at": debit_note.updated_date,
                "items": item_list
            }

            return Response(debit_note_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DebitNoteDeleteView(ModifiedApiview):
    def delete(self, request, id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)

            # Fetch the DebitNote record
            debit_note = get_object_or_404(DebitNote, id=id)

            # Delete the DebitNote and its associated items
            with transaction.atomic():
                debit_note.items.all().delete()  # Delete associated items
                debit_note.delete()  # Delete the debit note

            return Response(
                {"message": "Debit note deleted successfully"},
                status=status.HTTP_204_NO_CONTENT
            )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )