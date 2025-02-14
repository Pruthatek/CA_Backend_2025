# api/views.py
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from .models import Customer
from custom_auth.models import CustomUser  # Update with your user model path
import pandas as pd
from django.db import transaction


logger = logging.getLogger(__name__)

# Helper function to get a customer object
def get_customer_object(pk):
    try:
        return Customer.objects.get(pk=pk, is_active=True)
    except Customer.DoesNotExist:
        logger.error(f"Customer with id {pk} not found or inactive")
        raise NotFound("Customer not found")


# Create Customer
class CustomerCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logger.info(f"Attempting to create new customer with data: {request.data}")
        
        try:
            # Extract data from request
            data = request.data
            required_fields = ["name_of_business", "customer_code", "file_no", "status", "business_pan_no", "mobile"]
            
            # Validate required fields
            for field in required_fields:
                if field not in data:
                    return Response(
                        {"error": f"Missing required field: {field}"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            
            if Customer.objects.filter(customer_code=data["customer_code"]).exists():
                return Response(
                    {"error": "Customer with this code already exists."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if data.get("status") not in ["proprietor", "firm", "private_limited", "public_limited", 
                                          "bank", "aop_or_boi", "huf", "ajp", "society",]:
                return Response({"error": "Invalid status."}, status=status.HTTP_400_BAD_REQUEST)

            if data.get("dcs") not in ["new_dcs", "received", "not_received", "na"]:
                return Response({"error": "Invalid DCS status."}, status=status.HTTP_400_BAD_REQUEST)
            
            if data.get("status") == "private_limited" and not data.get("cin_number"):
                return Response(
                    {"error": "CIN number is required for Private Limited status."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            # Create the customer
            customer = Customer.objects.create(
                name_of_business=data["name_of_business"],
                customer_code=data["customer_code"],
                file_no=data["file_no"],
                business_pan_no=data.get("business_pan_no"),
                status=data.get("status"),
                address=data.get("address"),
                road=data.get("road"),
                state=data.get("state"),
                city=data.get("city"),
                country=data.get("country"),
                pin=data.get("pin"),
                contact_number=data.get("contact_number"),
                email=data.get("email"),
                mobile=data.get("mobile"),
                additional_contact_number=data.get("additional_contact_number"),
                secondary_email_id=data.get("secondary_email_id"),
                gst_no=data.get("gst_no"),
                gst_state_code=data.get("gst_state_code"),
                cin_number=data.get("cin_number"),
                llipin_number=data.get("llipin_number"),
                din_number=data.get("din_number"),
                first_name=data.get("first_name"),
                last_name=data.get("last_name"),
                date_of_birth=data.get("date_of_birth"),
                pan_no=data.get("pan_no"),
                enable_account=data.get("enable_account", True),
                accountant_name=data.get("accountant_name"),
                accountant_phone=data.get("accountant_phone"),
                created_by=request.user,
            )
            
            logger.info(f"Customer created successfully: {customer.id}")
            return Response(
                {
                    "id": customer.id,
                    "name_of_business": customer.name_of_business,
                    "customer_code": customer.customer_code,
                },
                status=status.HTTP_201_CREATED,
            )
        
        except ValidationError as e:
            logger.error(f"Validation error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.error(f"Error creating customer: {str(e)}")
            return Response(
                {"error": "Failed to create customer"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# List Customers
class CustomerListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            customers = Customer.objects.filter(is_active=True).values(
                "id",
                "name_of_business",
                "customer_code",
                "status",
                "address",
                "city",
                "state",
                "country",
                "pin",
                "contact_number",
                "email",
                "mobile",
                "additional_contact_number",
                "secondary_email_id",
                "gst_no",
                "gst_state_code",
                "cin_number",
                "llipin_number",
                "din_number",
                "first_name",
                "last_name",
                "date_of_birth",
                "pan_no",
                "enable_account",
                "accountant_name",
                "accountant_phone"
            )
            logger.info("Successfully retrieved all active customers")
            return Response(list(customers))
        
        except Exception as e:
            logger.error(f"Error retrieving customers: {str(e)}")
            return Response(
                {"error": "Failed to retrieve customers"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# Retrieve Customer
class CustomerRetrieveAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            customer = get_customer_object(pk)
            customer_data = {
                "id": customer.id,
                "name_of_business": customer.name_of_business,
                "customer_code": customer.customer_code,
                "status": customer.status,
                "address": customer.address,
                "city": customer.city,
                "state": customer.state,
                "country": customer.country,
                "pin": customer.pin,
                "contact_number": customer.contact_number,
                "email": customer.email,
                "mobile": customer.mobile,
                "additional_contact_number": customer.additional_contact_number,
                "secondary_email_id": customer.secondary_email_id,
                "gst_no": customer.gst_no,
                "gst_state_code": customer.gst_state_code,
                "cin_number": customer.cin_number,
                "llipin_number": customer.llipin_number,
                "din_number": customer.din_number,
                "first_name": customer.first_name,
                "last_name": customer.last_name,
                "date_of_birth": customer.date_of_birth,
                "pan_no": customer.pan_no,
                "enable_account": customer.enable_account,
                "accountant_name": customer.accountant_name,
                "accountant_phone": customer.accountant_phone,
            }
            logger.info(f"Successfully retrieved customer with id {pk}")
            return Response(customer_data)
        
        except NotFound as e:
            raise
        except Exception as e:
            logger.error(f"Error retrieving customer: {str(e)}")
            return Response(
                {"error": "Failed to retrieve customer"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# Update Customer
class CustomerUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        logger.info(f"Attempting to update customer {pk} with data: {request.data}")
        
        try:
            customer = Customer.objects.get(id=pk)
            data = request.data

            # Validate customer code uniqueness if being changed
            if 'customer_code' in data and data['customer_code'] != customer.customer_code:
                if Customer.objects.filter(customer_code=data['customer_code']).exists():
                    return Response(
                        {"error": "Customer with this code already exists."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                customer.customer_code = data['customer_code']

            # Validate status
            if 'status' in data:
                if data['status'] not in ["proprietor", "firm", "private_limited", "public_limited", 
                                        "bank", "aop_or_boi", "huf", "ajp", "society"]:
                    return Response({"error": "Invalid status."}, status=status.HTTP_400_BAD_REQUEST)
                
                if data['status'] == "private_limited" and not data.get('cin_number') and not customer.cin_number:
                    return Response(
                        {"error": "CIN number is required for Private Limited status."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                customer.status = data['status']

            # Validate DCS status
            if 'dcs' in data:
                if data['dcs'] not in ["new_dcs", "received", "not_received", "na"]:
                    return Response({"error": "Invalid DCS status."}, status=status.HTTP_400_BAD_REQUEST)
                customer.dcs = data['dcs']

            # Update other fields
            customer.name_of_business = data.get('name_of_business', customer.name_of_business)
            customer.file_no = data.get('file_no', customer.file_no)
            customer.business_pan_no = data.get('business_pan_no', customer.business_pan_no)
            customer.address = data.get('address', customer.address)
            customer.road = data.get('road', customer.road)
            customer.state = data.get('state', customer.state)
            customer.city = data.get('city', customer.city)
            customer.country = data.get('country', customer.country)
            customer.pin = data.get('pin', customer.pin)
            customer.contact_number = data.get('contact_number', customer.contact_number)
            customer.email = data.get('email', customer.email)
            customer.mobile = data.get('mobile', customer.mobile)
            customer.additional_contact_number = data.get('additional_contact_number', customer.additional_contact_number)
            customer.secondary_email_id = data.get('secondary_email_id', customer.secondary_email_id)
            customer.gst_no = data.get('gst_no', customer.gst_no)
            customer.gst_state_code = data.get('gst_state_code', customer.gst_state_code)
            customer.cin_number = data.get('cin_number', customer.cin_number)
            customer.llipin_number = data.get('llipin_number', customer.llipin_number)
            customer.din_number = data.get('din_number', customer.din_number)
            customer.first_name = data.get('first_name', customer.first_name)
            customer.last_name = data.get('last_name', customer.last_name)
            customer.date_of_birth = data.get('date_of_birth', customer.date_of_birth)
            customer.pan_no = data.get('pan_no', customer.pan_no)
            customer.enable_account = data.get('enable_account', customer.enable_account)
            customer.accountant_name = data.get('accountant_name', customer.accountant_name)
            customer.accountant_phone = data.get('accountant_phone', customer.accountant_phone)

            customer.save()
            
            logger.info(f"Customer {pk} updated successfully")
            return Response(
                {
                    "id": customer.id,
                    "name_of_business": customer.name_of_business,
                    "customer_code": customer.customer_code,
                },
                status=status.HTTP_200_OK,
            )
            
        except Customer.DoesNotExist:
            logger.error(f"Customer {pk} not found")
            return Response(
                {"error": "Customer not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except ValidationError as e:
            logger.error(f"Validation error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error updating customer: {str(e)}")
            return Response(
                {"error": "Failed to update customer"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# Delete Customer (Soft Delete)
class CustomerDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        logger.info(f"Attempting soft delete of customer {pk}")
        
        try:
            customer = get_customer_object(pk)
            customer.is_active = False
            customer.save()
            
            logger.info(f"Customer {pk} soft deleted successfully")
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        except Exception as e:
            logger.error(f"Error deleting customer: {str(e)}")
            return Response(
                {"error": "Failed to delete customer"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        

class CustomerBulkCreateExcelAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logger.info("Attempting bulk create customers from Excel file")
        
        excel_file = request.FILES.get("file")
        if not excel_file:
            return Response({"error": "No file uploaded."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Read excel file into DataFrame
            df = pd.read_excel(excel_file)
        except Exception as e:
            logger.error(f"Error reading Excel file: {e}")
            return Response({"error": "Invalid Excel file."}, status=status.HTTP_400_BAD_REQUEST)

        required_fields = [
            "name_of_business", "customer_code", "file_no",
            "status", "business_pan_no", "mobile"
        ]
        for field in required_fields:
            if field not in df.columns or df[field].isnull().any():
                return Response(
                    {"error": f"Missing required field '{field}' in one or more rows."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        valid_statuses = [
            "proprietor", "firm", "private_limited", "public_limited",
            "bank", "aop_or_boi", "huf", "ajp", "society",
        ]
        if not df["status"].isin(valid_statuses).all():
            return Response(
                {"error": "One or more rows have an invalid status."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate DCS status if column exists
        if "dcs" in df.columns:
            if not df["dcs"].isin(["new_dcs", "received", "not_received", "na"]).all():
                return Response(
                    {"error": "One or more rows have an invalid DCS status."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # For rows with status 'private_limited', ensure 'cin_number' is provided.
        mask = df["status"] == "private_limited"
        if mask.any() and (("cin_number" not in df.columns) or df.loc[mask, "cin_number"].isnull().any()):
            return Response(
                {"error": "CIN number is required for all rows with Private Limited status."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check for duplicate customer_code in DB
        customer_codes = df["customer_code"].tolist()
        if Customer.objects.filter(customer_code__in=customer_codes).exists():
            return Response(
                {"error": "One or more customer codes already exist in the database."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        customers_to_create = []
        for row in df.to_dict(orient="records"):
            customers_to_create.append(
                Customer(
                    name_of_business=row.get("name_of_business"),
                    customer_code=row.get("customer_code"),
                    file_no=row.get("file_no"),
                    business_pan_no=row.get("business_pan_no"),
                    status=row.get("status"),
                    address=row.get("address"),
                    road=row.get("road"),
                    state=row.get("state"),
                    city=row.get("city"),
                    country=row.get("country"),
                    pin=row.get("pin"),
                    contact_number=row.get("contact_number"),
                    email=row.get("email"),
                    mobile=row.get("mobile"),
                    additional_contact_number=row.get("additional_contact_number"),
                    secondary_email_id=row.get("secondary_email_id"),
                    gst_no=row.get("gst_no"),
                    gst_state_code=row.get("gst_state_code"),
                    cin_number=row.get("cin_number"),
                    llipin_number=row.get("llipin_number"),
                    din_number=row.get("din_number"),
                    first_name=row.get("first_name"),
                    last_name=row.get("last_name"),
                    date_of_birth=row.get("date_of_birth"),
                    pan_no=row.get("pan_no"),
                    enable_account=row.get("enable_account", True),
                    accountant_name=row.get("accountant_name"),
                    accountant_phone=row.get("accountant_phone"),
                    created_by=request.user,
                )
            )

        try:
            with transaction.atomic():
                created_customers = Customer.objects.bulk_create(customers_to_create)
            logger.info(f"Bulk customer creation successful. Created {len(created_customers)} customers.")
            result = [
                {
                    "id": customer.id,
                    "name_of_business": customer.name_of_business,
                    "customer_code": customer.customer_code,
                }
                for customer in created_customers
            ]
            return Response(result, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error during bulk customer creation: {e}")
            return Response({"error": "Failed to create customers"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
