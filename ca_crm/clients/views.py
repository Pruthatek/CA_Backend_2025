# api/views.py
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from .models import Customer
from custom_auth.models import CustomUser  # Update with your user model path

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