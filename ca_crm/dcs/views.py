from rest_framework.views import APIView 
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
import json
from .models import CustomerDcs
from workflow.views import ModifiedApiview
import pandas as pd

class CreateDSCView(ModifiedApiview):
    def post(self, request, *args, **kwargs):
        try:
            # Parse JSON data from the request body
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error":"You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            data = json.loads(request.body)

            # Validate required fields
            required_fields = ['customer_id', 'pan_no', 'name', 'related_company', 'issue_date', 'valid_till_date', 'password', 'position', 'class_type']
            for field in required_fields:
                if field not in data:
                    return Response({"error": f"{field} is required."}, status=status.HTTP_400_BAD_REQUEST)
            # customer_details = 
            # Get the user creating the entry
            created_by = user

            # Create the DSC entry
            customer = CustomerDcs(
                customer_id=data.get("customer_id"),
                pan_no=data['pan_no'],
                name=data['name'],
                related_company=data['related_company'],
                issue_date=data['issue_date'],
                valid_till_date=data['valid_till_date'],
                issuing_authority=data.get('issuing_authority'),
                password=data['password'],
                position=data['position'],
                class_type=data['class_type'],
                mobile_no=data.get('mobile_no'),
                email=data.get('email'),
                custodian_name=data.get('custodian_name'),
                created_by=created_by,
            )
            customer.save()

            return Response({"message": "DSC entry created successfully.", "id": customer.id}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        

class BulkCreateDSCView(ModifiedApiview):
    def post(self, request, *args, **kwargs):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error":"You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            if 'file' not in request.FILES:
                return Response({"error": "No file uploaded."}, status=status.HTTP_400_BAD_REQUEST)

            # Read the uploaded file
            file = request.FILES['file']
            if file.name.endswith('.xlsx'):
                df = pd.read_excel(file)
            elif file.name.endswith('.csv'):
                df = pd.read_csv(file)
            else:
                return Response({"error": "Unsupported file format. Please upload an Excel (.xlsx) or CSV (.csv) file."}, status=400)

            # Validate required columns
            required_columns = ['customer_id', 'pan_no', 'name', 'related_company', 'issue_date', 'valid_till_date', 'password', 'position', 'class_type']
            for column in required_columns:
                if column not in df.columns:
                    return Response({"error": f"{column} column is missing in the file."}, status=status.HTTP_400_BAD_REQUEST)

            # Get the user creating the entries
            created_by = user

            # Create DSC entries from the file
            created_ids = []
            for _, row in df.iterrows():
                customer = CustomerDcs(
                    customer_id = row['customer_id'],
                    pan_no=row['pan_no'],
                    name=row['name'],
                    related_company=row['related_company'],
                    issue_date=row['issue_date'],
                    valid_till_date=row['valid_till_date'],
                    issuing_authority=row.get('issuing_authority'),
                    password=row['password'],
                    position=row['position'],
                    class_type=row['class_type'],
                    mobile_no=row.get('mobile_no'),
                    email=row.get('email'),
                    custodian_name=row.get('custodian_name'),
                    created_by=created_by,
                )
                customer.save()
                created_ids.append(customer.id)

            return Response({"message": "Bulk DSC entries created successfully.", "created_ids": created_ids}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class UpdateDSCView(ModifiedApiview):
    def put(self, request, id):
        try:
            # Parse JSON data from the request body
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error":"You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            data = json.loads(request.body)
            

            
            # Fetch the DSC entry
            try:
                customer = CustomerDcs.objects.get(id=id)
            except CustomerDcs.DoesNotExist:
                return Response({"error": "DSC entry not found."}, status=status.HTTP_404_NOT_FOUND)
            
            # Update fields if provided
            update_fields = ['name', 'related_company', 'issue_date', 'valid_till_date', 'issuing_authority', 
                             'password', 'position', 'class_type', 'mobile_no', 'email', 'custodian_name']
            customer.name = data.get("name", customer.name)
            customer.related_company = data.get("related_company", customer.related_company)
            customer.issue_date = data.get("issue_date", customer.issue_date)
            customer.valid_till_date = data.get("valid_till_date", customer.valid_till_date)
            customer.issuing_authority = data.get("issuing_authority", customer.issuing_authority)
            customer.password = data.get("password", customer.password)
            customer.position = data.get("position", customer.position)
            customer.class_type = data.get("class_type", customer.class_type)
            customer.mobile_no = data.get("mobile_no", customer.mobile_no)
            customer.email = data.get("email", customer.email)
            customer.custodian_name = data.get("custodian_name", customer.custodian_name)
            
            # Update the 'updated_by' field

            customer.updated_by = user
            
            customer.save()
            
            return Response({"message": "DSC entry updated successfully."}, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class DeleteDSCView(ModifiedApiview):
    def delete(self, request,id):

        try:
            customer = CustomerDcs.objects.get(id=id)
            customer.delete()
            return Response({"message": "DSC entry deleted successfully."}, status=status.HTTP_200_OK)
        except CustomerDcs.DoesNotExist:
            return Response({"error": "DSC entry not found."}, status=status.HTTP_404_NOT_FOUND)        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class RetrieveDSCView(ModifiedApiview):
    def get(self, request, id):
        try:            
            customer = CustomerDcs.objects.get(id=id)
            customer_data = {
                'customer_id':customer.customer.id,
                'customer_name':customer.customer.name_of_business,
                "pan_no": customer.pan_no,
                "name": customer.name,
                "related_company": customer.related_company,
                "issue_date": customer.issue_date,
                "valid_till_date": customer.valid_till_date,
                "issuing_authority": customer.issuing_authority,
                "position": customer.position,
                "class_type": customer.class_type,
                "mobile_no": customer.mobile_no,
                "email": customer.email,
                "custodian_name": customer.custodian_name,
                "created_by": customer.created_by.id if customer.created_by else None,
                "created_date": customer.created_date,
                "updated_by": customer.updated_by.id if customer.updated_by else None,
                "updated_date": customer.updated_date
            }
            return Response(customer_data, status=status.HTTP_200_OK)
        except CustomerDcs.DoesNotExist:
            return Response({"error": "DSC entry not found."}, status=status.HTTP_404_NOT_FOUND)


class ListDSCView(ModifiedApiview):
    def get(self, request, *args, **kwargs):
        try:
            customers = CustomerDcs.objects.all()
            customer_list = [
                {
                    'customer_id':customer.customer.id,
                    'customer_name':customer.customer.name_of_business,
                    "pan_no": customer.pan_no,
                    "name": customer.name,
                    "related_company": customer.related_company,
                    "issue_date": customer.issue_date,
                    "valid_till_date": customer.valid_till_date,
                    "issuing_authority": customer.issuing_authority,
                    "mobile_no": customer.mobile_no,
                    "email": customer.email,
                    "custodian_name": customer.custodian_name,
                    "created_by": customer.created_by.id if customer.created_by else None,
                }
                for customer in customers
            ]
            return Response(customer_list, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
