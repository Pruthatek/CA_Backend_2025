from rest_framework.permissions import IsAdminUser, AllowAny, IsAuthenticated
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from .models import (Customer, 
                     CustomerContacts, 
                     CustomerGroups, 
                     CustomerBranch, 
                     CustomerBranchMapping, 
                     CustomerGroupMapping,
                     Inquiry
                     )
from custom_auth.models import CustomUser  # Update with your user model path
import pandas as pd
from django.db import transaction
from workflow.views import ModifiedApiview 

logger = logging.getLogger(__name__)

# Helper function to get a customer object
def get_customer_object(pk):
    try:
        return Customer.objects.get(pk=pk, is_active=True)
    except Customer.DoesNotExist:
        logger.error(f"Customer with id {pk} not found or inactive")
        raise NotFound("Customer not found")


# Create Customer
class CustomerCreateAPIView(ModifiedApiview):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = self.get_user_from_token(request)
        if not user:
            return Response(
                {"error": "Invalid user or You are not authorized to perform this action."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        # logger.info(f"Attempting to create new customer with data: {request.data}")
        
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
                                          "bank", "aop_or_boi", "huf", "ajp", "society", "individual"]:
                return Response({"error": "Invalid status."}, status=status.HTTP_400_BAD_REQUEST)

            if data.get("dsc") not in ["new_dsc", "received", "not_received", "na"]:
                return Response({"error": "Invalid DSC status."}, status=status.HTTP_400_BAD_REQUEST)
            
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
                destination_address=data.get("destination_address", None),
                cin_number=data.get("cin_number"),
                llipin_number=data.get("llipin_number"),
                din_number=data.get("din_number"),
                date_of_birth=data.get("date_of_birth"),
                dsc=data.get("dsc", None),
                pan_no=data.get("pan_no"),
                enable_account=data.get("enable_account", True),
                accountant_name=data.get("accountant_name"),
                accountant_phone=data.get("accountant_phone"),
                created_by=request.user,
            )
            contacts = data.get("contacts", [])
            for contact in contacts:
                CustomerContacts.objects.create(
                    customer=customer,
                    first_name=contact.get("first_name"),
                    last_name=contact.get("last_name"),
                    email=contact.get("email", None),
                    phone=contact.get("phone", None),
                    designation=contact.get("designation"),
                    created_by=request.user,
                )
            
            # Save customer group mapping
            group_id = data.get("customer_group", None)
            if group_id:
                group = CustomerGroups.objects.filter(id=group_id, is_active=True).first()
                if group:
                    CustomerGroupMapping.objects.create(
                        customer=customer,
                        group=group,
                        created_by=request.user,
                    )
                else:
                    return Response({"error": "Invalid customer group."}, status=status.HTTP_400_BAD_REQUEST)
            
            # Save customer branch mapping
            branch_id = data.get("customer_branch", None)
            if branch_id:
                branch = CustomerBranch.objects.filter(id=branch_id, is_active=True).first()
                if branch:
                    CustomerBranchMapping.objects.create(
                        customer=customer,
                        branch=branch,
                        created_by=request.user,
                    )
                else:
                    return Response({"error": "Invalid customer branch."}, status=status.HTTP_400_BAD_REQUEST)
            
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
class CustomerListAPIView(ModifiedApiview):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response(
                    {"error": "Invalid user or You are not authorized to perform this action."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
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
                "date_of_birth",
                "pan_no",
                "enable_account",
                "accountant_name",
                "accountant_phone",
                "dsc",
                "file_no",
                "created_date"

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
class CustomerRetrieveAPIView(ModifiedApiview):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response(
                    {"error": "Invalid user or You are not authorized to perform this action."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            customer = get_customer_object(pk)
            customer_data = {
                "id": customer.id,
                "name_of_business": customer.name_of_business,
                "customer_code": customer.customer_code,
                "status": customer.status,
                "business_pan_no": customer.business_pan_no,
                "file_no": customer.file_no,
                "address": customer.address,
                "road": customer.road,
                "city": customer.city,
                "state": customer.state,
                "country": customer.country,
                "pin": customer.pin,
                "contact_number": customer.contact_number,
                "email": customer.email,
                "mobile": customer.mobile,
                "additional_contact_number": customer.additional_contact_number,
                "secondary_email_id": customer.secondary_email_id,
                "destination_address": customer.destination_address,
                "dsc": customer.dsc,
                "gst_no": customer.gst_no,
                "gst_state_code": customer.gst_state_code,
                "cin_number": customer.cin_number,
                "llipin_number": customer.llipin_number,
                "din_number": customer.din_number,
                "date_of_birth": customer.date_of_birth,
                "pan_no": customer.pan_no,
                "enable_account": customer.enable_account,
                "accountant_name": customer.accountant_name,
                "accountant_phone": customer.accountant_phone,
                "contacts": list(customer.customer_contact.values("first_name", "last_name", "email", "phone", "designation", "id")),
                "customer_group": customer.customer_group_mapping.first().group.name if customer.customer_group_mapping.exists() else None,
                "customer_branch": customer.customer_branch_mapping.first().branch.name if customer.customer_branch_mapping.exists() else None,
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
class CustomerUpdateAPIView(ModifiedApiview):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        logger.info(f"Attempting to update customer {pk} with data: {request.data}")
        
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response(
                    {"error": "Invalid user or You are not authorized to perform this action."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
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
                                        "bank", "aop_or_boi", "huf", "ajp", "society", "individual"]:
                    return Response({"error": "Invalid status."}, status=status.HTTP_400_BAD_REQUEST)
                
                if data['status'] == "private_limited" and not data.get('cin_number') and not customer.cin_number:
                    return Response(
                        {"error": "CIN number is required for Private Limited status."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                customer.status = data['status']

            # Validate DSC status
            if 'dsc' in data:
                if data['dsc'] not in ["new_dsc", "received", "not_received", "na"]:
                    return Response({"error": "Invalid DSC status."}, status=status.HTTP_400_BAD_REQUEST)
                customer.dsc = data['dsc']

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
            customer.destination_address = data.get("destination_address", customer.destination_address)
            customer.cin_number = data.get('cin_number', customer.cin_number)
            customer.llipin_number = data.get('llipin_number', customer.llipin_number)
            customer.din_number = data.get('din_number', customer.din_number)
            customer.dsc = data.get('dsc', customer.dsc)
            customer.date_of_birth = data.get('date_of_birth', customer.date_of_birth)
            customer.pan_no = data.get('pan_no', customer.pan_no)
            customer.enable_account = data.get('enable_account', customer.enable_account)
            customer.accountant_name = data.get('accountant_name', customer.accountant_name)
            customer.accountant_phone = data.get('accountant_phone', customer.accountant_phone)

            customer.save()

            new_contacts = data.get("new_contacts", [])
            if new_contacts:
                for contact in new_contacts:
                    CustomerContacts.objects.create(
                        customer=customer,
                        first_name=contact.get("first_name"),
                        last_name=contact.get("last_name"),
                        email=contact.get("email", None),
                        phone=contact.get("phone", None),
                        designation=contact.get("designation"),
                        created_by=request.user,
                    )
    
            updated_contacts = data.get("updated_contacts", [])
            if updated_contacts:
                for contact in updated_contacts:
                    CustomerContacts.objects.filter(id=contact.get("id")).update(
                        customer=customer,
                        first_name=contact.get("first_name"),
                        last_name=contact.get("last_name"),
                        email=contact.get("email", None),
                        phone=contact.get("phone", None),
                        designation=contact.get("designation"),
                        updated_by=request.user,
                    )
            deleted_contacts = data.get("deleted_contacts", [])
            if deleted_contacts:
                for contact_id in deleted_contacts:
                    CustomerContacts.objects.filter(id=contact_id).delete()

            # Save customer group mapping
            group_id = data.get("customer_group", None)
            if group_id:
                group = CustomerGroups.objects.filter(id=group_id, is_active=True).first()
                previous_group = customer.customer_group_mapping.first().group if customer.customer_group_mapping.exists() else None
                if previous_group:
                    customer.customer_group_mapping.first().delete()
                if group:
                    CustomerGroupMapping.objects.create(
                        customer=customer,
                        group=group,
                        created_by=request.user,
                    )
                else:
                    return Response({"error": "Invalid customer group."}, status=status.HTTP_400_BAD_REQUEST)
            
            # Save customer branch mapping
            branch_id = data.get("customer_branch", None)
            if branch_id:
                branch = CustomerBranch.objects.filter(id=branch_id, is_active=True).first()
                if branch:
                    CustomerBranchMapping.objects.create(
                        customer=customer,
                        branch=branch,
                        created_by=request.user,
                    )
                else:
                    return Response({"error": "Invalid customer branch."}, status=status.HTTP_400_BAD_REQUEST)
    
            
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
class CustomerDeleteAPIView(ModifiedApiview):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        logger.info(f"Attempting soft delete of customer {pk}")
        
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response(
                    {"error": "Invalid user or You are not authorized to perform this action."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
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
        

class CustomerBulkCreateExcelAPIView(ModifiedApiview):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = self.get_user_from_token(request)
        if not user:
            return Response(
                {"error": "Invalid user or You are not authorized to perform this action."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
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

        # Validate DSC status if column exists
        if "dsc" in df.columns:
            if not df["dsc"].isin(["new_dsc", "received", "not_received", "na"]).all():
                return Response(
                    {"error": "One or more rows have an invalid DSC status."},
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

# CustomerBranch Views

class CustomerBranchCreateView(ModifiedApiview):
    def post(self, request):
        user = self.get_user_from_token(request)
        if not user:
            return Response(
                {"error": "Invalid user or You are not authorized to perform this action."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        data = request.data
        branch = CustomerBranch.objects.create(
            name=data.get('name'),
            created_by=user,
            updated_by=user,
            is_active=True
        )
        return Response({'id': branch.id, 'name': branch.name}, status=status.HTTP_201_CREATED)


class CustomerBranchListView(ModifiedApiview):
    def get(self, request):
        user = self.get_user_from_token(request)
        if not user:
            return Response(
                {"error": "Invalid user or You are not authorized to perform this action."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        branches = CustomerBranch.objects.filter(is_active=True)
        branches_data = [{'id': branch.id, 'name': branch.name} for branch in branches]
        return Response(branches_data, status=status.HTTP_200_OK)


class CustomerBranchDetailView(ModifiedApiview):
    def get(self, request, branch_id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response(
                    {"error": "Invalid user or You are not authorized to perform this action."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            branch = CustomerBranch.objects.get(id=branch_id, is_active=True)
            branch_data = {'id': branch.id, 'name': branch.name}
            return Response(branch_data, status=status.HTTP_200_OK)
        except CustomerBranch.DoesNotExist:
            return Response({'error': 'Branch not found'}, status=status.HTTP_404_NOT_FOUND)


class CustomerBranchUpdateView(ModifiedApiview):
    def put(self, request, branch_id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response(
                    {"error": "Invalid user or You are not authorized to perform this action."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            branch = CustomerBranch.objects.get(id=branch_id)
            data = request.data
            branch.name = data.get('name', branch.name)
            branch.updated_by_id = user
            branch.save()
            return Response({'id': branch.id, 'name': branch.name}, status=status.HTTP_200_OK)
        except CustomerBranch.DoesNotExist:
            return Response({'error': 'Branch not found'}, status=status.HTTP_404_NOT_FOUND)


class CustomerBranchDeleteView(ModifiedApiview):
    def delete(self, request, branch_id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response(
                    {"error": "Invalid user or You are not authorized to perform this action."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            branch = CustomerBranch.objects.get(id=branch_id)
            branch.is_active = False
            branch.save()
            return Response({'message': 'Branch deactivated successfully'}, status=status.HTTP_200_OK)
        except CustomerBranch.DoesNotExist:
            return Response({'error': 'Branch not found'}, status=status.HTTP_404_NOT_FOUND)


# CustomerGroups Views

class CustomerGroupCreateView(ModifiedApiview):
    def post(self, request):
        user = self.get_user_from_token(request)
        if not user:
            return Response(
                {"error": "Invalid user or You are not authorized to perform this action."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        data = request.data
        group = CustomerGroups.objects.create(
            name=data.get('name'),
            created_by=user,
            updated_by=user,
            is_active=True
        )
        return Response({'id': group.id, 'name': group.name}, status=status.HTTP_201_CREATED)


class CustomerGroupListView(ModifiedApiview):
    def get(self, request):
        user = self.get_user_from_token(request)
        if not user:
            return Response(
                {"error": "Invalid user or You are not authorized to perform this action."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        groups = CustomerGroups.objects.filter(is_active=True)
        groups_data = [{'id': group.id, 'name': group.name} for group in groups]
        return Response(groups_data, status=status.HTTP_200_OK)


class CustomerGroupDetailView(ModifiedApiview):
    def get(self, request, group_id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response(
                    {"error": "Invalid user or You are not authorized to perform this action."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            group = CustomerGroups.objects.get(id=group_id, is_active=True)
            group_data = {'id': group.id, 'name': group.name}
            return Response(group_data, status=status.HTTP_200_OK)
        except CustomerGroups.DoesNotExist:
            return Response({'error': 'Group not found'}, status=status.HTTP_404_NOT_FOUND)


class CustomerGroupUpdateView(ModifiedApiview):
    def put(self, request, group_id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response(
                    {"error": "Invalid user or You are not authorized to perform this action."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            group = CustomerGroups.objects.get(id=group_id)
            data = request.data
            group.name = data.get('name', group.name)
            group.updated_by_id = user
            group.save()
            return Response({'id': group.id, 'name': group.name}, status=status.HTTP_200_OK)
        except CustomerGroups.DoesNotExist:
            return Response({'error': 'Group not found'}, status=status.HTTP_404_NOT_FOUND)


class CustomerGroupDeleteView(ModifiedApiview):
    def delete(self, request, group_id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response(
                    {"error": "Invalid user or You are not authorized to perform this action."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            group = CustomerGroups.objects.get(id=group_id)
            group.is_active = False
            group.save()
            return Response({'message': 'Group deactivated successfully'}, status=status.HTTP_200_OK)
        except CustomerGroups.DoesNotExist:
            return Response({'error': 'Group not found'}, status=status.HTTP_404_NOT_FOUND)
        

class InquiryCreateView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        data = request.data
        required_fields = ["full_name", "mobile_no", "email_id", "selected_services"]
        
        for field in required_fields:
            if field not in data:
                return Response({"error": f"Missing required field: {field}"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Convert list to comma-separated string before saving
        selected_services_str = ",".join(list(data.get("selected_services", [])))

        inquiry = Inquiry.objects.create(
            full_name=data["full_name"],
            mobile_no=data["mobile_no"],
            email_id=data["email_id"],
            address=data.get("address", ""),
            remark=data.get("remark", ""),
            selected_services=selected_services_str,
            other_services=data.get("other_services", ""),
            reference_full_name=data.get("reference_full_name", None),
            reference_mobile_no=data.get("reference_mobile_no", None),
            reference_email_id=data.get("reference_email_id", None),
            call_full_name=data.get("call_full_name", None),
            call_mobile_no=data.get("call_mobile_no", None),
            call_relation=data.get("call_relation", None),
            otp_full_name=data.get("otp_full_name", None),
            otp_mobile_no=data.get("otp_mobile_no", None),
            otp_relation=data.get("otp_relation", None),
        )
        
        return Response({"message": "Inquiry submitted successfully!", "inquiry_id": inquiry.id}, status=status.HTTP_201_CREATED)


class InquiryListView(APIView):
    def get(self, request):
        try:
            # Extract and validate pagination parameters
            page = request.GET.get("page", "1")
            per_page = request.GET.get("per_page", "10")

            if not page.isdigit() or not per_page.isdigit():
                return Response({"error": "Page and per_page must be valid integers"}, status=status.HTTP_400_BAD_REQUEST)

            page = int(page)
            per_page = int(per_page)

            if page < 1 or per_page < 1:
                return Response({"error": "Page and per_page must be greater than 0"}, status=status.HTTP_400_BAD_REQUEST)

            start_index = (page - 1) * per_page

            # Fetch only required fields with limit & offset for efficiency
            inquiries = list(
                Inquiry.objects.filter()
                .order_by("-created_at")
                .values("id", "full_name", "mobile_no", "email_id", "selected_services", "created_at", "address", "other_services", "remark", "reference_full_name")
                [start_index : start_index + per_page]
            )

            for inquiry in inquiries:
                inquiry["selected_services"] = inquiry["selected_services"].split(",") if inquiry["selected_services"] else []
                inquiry["other_services"] = inquiry["other_services"].split(",") if inquiry["other_services"] else []

            # Check if there is a next page
            has_next = Inquiry.objects.filter().order_by("-created_at")[start_index + per_page : start_index + per_page + 1].exists()

            # If no inquiries found
            if not inquiries:
                return Response({"message": "No inquiries found", "current_page": page, "per_page": per_page, "has_next": False, "data": []}, status=status.HTTP_200_OK)

            return Response({
                "current_page": page,
                "per_page": per_page,
                "has_next": has_next,
                "data": inquiries
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": f"Something went wrong: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InquiryRetrieveView(APIView):
    def get(self, request, id):
        try:
            inquiry = Inquiry.objects.get(id=id)
            return Response({
                "full_name": inquiry.full_name,
                "mobile_no": inquiry.mobile_no,
                "email_id": inquiry.email_id,
                "address": inquiry.address,
                "remark": inquiry.remark,
                "selected_services": inquiry.get_services_list(),  # Convert back to list
                "other_services": inquiry.other_services,
                "reference_full_name": inquiry.reference_full_name,
                "reference_mobile_no": inquiry.reference_mobile_no,
                "reference_email_id": inquiry.reference_email_id,
                "call_full_name": inquiry.call_full_name,
                "call_mobile_no": inquiry.call_mobile_no,
                "call_relation": inquiry.call_relation,
                "otp_full_name": inquiry.otp_full_name,
                "otp_mobile_no": inquiry.otp_mobile_no,
                "otp_relation": inquiry.otp_relation,
                "created_at": inquiry.created_at,
            }, status=status.HTTP_200_OK)
        except Inquiry.DoesNotExist:
            return Response({"error": "Inquiry not found"}, status=status.HTTP_404_NOT_FOUND)


class InquiryDeleteView(APIView):
    def delete(self, request, id):
        try:
            inquiry = Inquiry.objects.get(id=id)
            inquiry.delete()
            return Response({"message": "Inquiry deleted successfully"}, status=status.HTTP_200_OK)
        except Inquiry.DoesNotExist:
            return Response({"error": "Inquiry not found"}, status=status.HTTP_404_NOT_FOUND)
