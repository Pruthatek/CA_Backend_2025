from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist
from .models import Company, BankDetails
from workflow.views import ModifiedApiview
import posixpath
from django.core.files.storage import FileSystemStorage
import os
import uuid
import time
from django.conf import settings


def generate_short_unique_filename(extension):
    # Shortened UUID (6 characters) + Unix timestamp for uniqueness
    unique_id = uuid.uuid4().hex[:6]  # Get the first 6 characters of UUID
    timestamp = str(int(time.time()))  # Unix timestamp as a string
    return f"{unique_id}_{timestamp}{extension}"


# ============== COMPANY APIS ==============

class CompanyCreateAPI(ModifiedApiview):
    def post(self, request):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)

            # Handle both form-data and json requests
            
            data = request.data
            
            # Validate required fields
            required_fields = ['name', 'billing_address', 'pan_no']
            for field in required_fields:
                if field not in data or not data[field]:
                    return Response(
                        {'status': 'error', 'message': f'{field} is required'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Create company
            company = Company.objects.create(
                name=data['name'],
                billing_address=data['billing_address'],
                destination_address=data.get('destination_address'),
                pan_no=data['pan_no'],
                gst_no=data.get('gst_no'),
                state_code_gst=data.get('state_code_gst'),
                place_of_supply=data.get('place_of_supply'),
                mobile_no=data.get('mobile_no'),
                telephone_no=data.get('telephone_no'),
                email=data.get('email'),
                cin=data.get('cin'),
                terms_and_conditions=data.get('terms_and_conditions'),
            )
            
            # Handle logo if present
            logo_url = request.FILES.get('logo')
            if logo_url:
                extension = os.path.splitext(logo_url.name)[1]
                short_unique_filename = generate_short_unique_filename(extension)
                fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'logo_urls'))
                logo_path = fs.save(short_unique_filename, logo_url)
                logo_url = posixpath.join('media/logo_urls', logo_path)
            else:
                logo_url = None


            signature_url = request.FILES.get('signature')
            if signature_url:
                extension = os.path.splitext(signature_url.name)[1]
                short_unique_filename = generate_short_unique_filename(extension)
                fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'signature_urls'))
                signature_path = fs.save(short_unique_filename, signature_url)
                signature_url = posixpath.join('media/signature_urls', signature_path)
            else:
                signature_url = None

            qr_code_url = request.FILES.get('qr_code')
            if qr_code_url:
                extension = os.path.splitext(qr_code_url.name)[1]
                short_unique_filename = generate_short_unique_filename(extension)
                fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'qr_code_urls'))
                qr_code_path = fs.save(short_unique_filename, qr_code_url)
                qr_code_url = posixpath.join('media/qr_code_urls', qr_code_path)
            else:
                qr_code_url = None

            add_signature_to_invoice = data.get('add_signature_to_invoice', False)
            if isinstance(add_signature_to_invoice, str) and add_signature_to_invoice.lower() == 'true':
                company.add_signature_to_invoice = True

            company.add_signature_to_invoice = add_signature_to_invoice
            company.logo = logo_url
            company.signature = signature_url
            company.qr_code = qr_code_url
            company.save()



            return Response(
                {
                    'status': 'success',
                    'message': 'Company created successfully',
                    'company_id': company.id
                },
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class CompanyListAPI(ModifiedApiview):
    def get(self, request):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            companies = Company.objects.all()
            data = []
            for company in companies:
                data.append({
                    'id': company.id,
                    'name': company.name,
                    'billing_address': company.billing_address,
                    'pan_no': company.pan_no,
                    'logo_url': company.logo if company.logo else None,
                    'created_at': company.created_at,
                })
            return Response({'status': 'success', 'data': data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CompanyRetrieveAPI(ModifiedApiview):
    def get(self, request, pk):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            company = Company.objects.get(pk=pk)
            bank_details = company.bank_details.all()
            
            bank_details_data = []
            for bank in bank_details:
                bank_details_data.append({
                    'id': bank.id,
                    'bank_name': bank.bank_name,
                    'account_number': bank.account_number,
                })
            
            data = {
                'id': company.id,
                'name': company.name,
                'billing_address': company.billing_address,
                'destination_address': company.destination_address,
                'pan_no': company.pan_no,
                'gst_no': company.gst_no,
                'state_code_gst': company.state_code_gst,
                'place_of_supply': company.place_of_supply,
                'mobile_no': company.mobile_no,
                'telephone_no': company.telephone_no,
                'email': company.email,
                'cin': company.cin,
                'terms_and_conditions': company.terms_and_conditions,
                'logo_url': company.logo if company.logo else None,
                'signature_url': company.signature if company.signature else None,
                'qr_code_url': company.qr_code if company.qr_code else None,
                'add_signature_to_invoice': company.add_signature_to_invoice if company.add_signature_to_invoice else 'false',
                'bank_details': bank_details_data,
                'created_at': company.created_at,
                'updated_at': company.updated_at,
            }
            return Response({'status': 'success', 'data': data}, status=status.HTTP_200_OK)
        
        except ObjectDoesNotExist:
            return Response(
                {'status': 'error', 'message': 'Company not found'},
                status=status.HTTP_404_NOT_FOUND
            )

class CompanyUpdateAPI(ModifiedApiview):
    def put(self, request, pk):
        try:
            # Authentication check
            user = self.get_user_from_token(request)
            if not user:
                return Response(
                    {"status": "error", "message": "Authentication failed"}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )

            # Get company instance
            company = Company.objects.get(pk=pk)
            
            # Get data from request
            data = request.data
            
            # Validate required fields are present
            required_fields = ['name', 'billing_address', 'pan_no']
            for field in required_fields:
                if not data.get(field):
                    return Response(
                        {"status": "error", "message": f"{field} is required"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Update all fields directly
            company.name = data['name'].strip()
            company.billing_address = data['billing_address'].strip()
            company.destination_address = data['destination_address'].strip() if data.get('destination_address') else None
            company.pan_no = data['pan_no'].strip().upper()
            company.gst_no = data['gst_no'].strip().upper() if data.get('gst_no') else None
            company.state_code_gst = data['state_code_gst'].strip() if data.get('state_code_gst') else None
            company.place_of_supply = data['place_of_supply'].strip() if data.get('place_of_supply') else None
            company.mobile_no = data['mobile_no'].strip() if data.get('mobile_no') else None
            company.telephone_no = data['telephone_no'].strip() if data.get('telephone_no') else None
            company.email = data['email'].strip().lower() if data.get('email') else None
            company.cin = data['cin'].strip().upper() if data.get('cin') else None
            company.terms_and_conditions = data['terms_and_conditions'].strip() if data.get('terms_and_conditions') else None
            
            # Handle logo update if present
            logo_url = request.FILES.get('updated_logo', None)
            if logo_url:
                extension = os.path.splitext(logo_url.name)[1]
                short_unique_filename = generate_short_unique_filename(extension)
                fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'logo_urls'))
                logo_path = fs.save(short_unique_filename, logo_url)
                logo_url = posixpath.join('media/logo_urls', logo_path)
            else:
                logo_url = request.FILES.get('logo', None)
                if logo_url:
                    logo_url = company.logo
                else:
                    logo_url = None
                
            signature_url = request.FILES.get('updated_signature', None)
            if signature_url:
                extension = os.path.splitext(signature_url.name)[1]
                short_unique_filename = generate_short_unique_filename(extension)
                fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'signature_urls'))
                signature_path = fs.save(short_unique_filename, signature_url)
                signature_url = posixpath.join('media/signature_urls', signature_path)
            else:
                signature_url = request.FILES.get('signature', None)
                if signature_url:
                    signature_url = company.signature
                else:
                    signature_url = None
                
            qr_code_url = request.FILES.get('updated_qr_code', None)
            if qr_code_url:
                extension = os.path.splitext(qr_code_url.name)[1]
                short_unique_filename = generate_short_unique_filename(extension)
                fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'qr_code_urls'))
                qr_code_path = fs.save(short_unique_filename, qr_code_url)
                qr_code_url = posixpath.join('media/qr_code_urls', qr_code_path)
            else:
                qr_code_url = request.FILES.get('qr_code', None)
                if qr_code_url:
                    qr_code_url = company.qr_code
                else:
                    qr_code_url = None
                
            add_signature_to_invoice = data.get('add_signature_to_invoice', False)
            if isinstance(add_signature_to_invoice, str) and add_signature_to_invoice.lower() == 'true':
                company.add_signature_to_invoice = True
                
            company.add_signature_to_invoice = add_signature_to_invoice
            company.logo = logo_url
            company.signature = signature_url
            company.qr_code = qr_code_url
            company.save()
            
            # Prepare response data
            response_data = {
                "status": "success",
                "message": "Company updated successfully",
                "data": {
                    "id": company.id,
                    "name": company.name,
                    "billing_address": company.billing_address,
                    "pan_no": company.pan_no,
                    "updated_at": company.updated_at
                }
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except ObjectDoesNotExist:
            return Response(
                {"status": "error", "message": "Company not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        

class CompanyDeleteAPI(ModifiedApiview):
    def delete(self, request, pk):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)

            company = Company.objects.get(pk=pk)
            company.delete()
            return Response(
                {'status': 'success', 'message': 'Company deleted successfully'},
                status=status.HTTP_204_NO_CONTENT
            )
        except ObjectDoesNotExist:
            return Response(
                {'status': 'error', 'message': 'Company not found'},
                status=status.HTTP_404_NOT_FOUND
            )

# ============== BANK DETAILS APIS ==============

class BankDetailsCreateAPI(ModifiedApiview):
    def post(self, request, company_id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)

            company = Company.objects.get(pk=company_id)
            data = request.data
            
            # Validate required fields
            required_fields = ['bank_name', 'account_number', 'account_holder_name', 'ifsc_code']
            for field in required_fields:
                if field not in data or not data[field]:
                    return Response(
                        {'status': 'error', 'message': f'{field} is required'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Create bank detail
            bank_detail = BankDetails.objects.create(
                company=company,
                bank_name=data['bank_name'],
                account_number=data['account_number'],
                account_holder_name=data['account_holder_name'],
                ifsc_code=data['ifsc_code'],
                branch=data.get('branch')
            )
            
            return Response(
                {
                    'status': 'success',
                    'message': 'Bank details added successfully',
                    'bank_detail_id': bank_detail.id
                },
                status=status.HTTP_201_CREATED
            )
            
        except ObjectDoesNotExist:
            return Response(
                {'status': 'error', 'message': 'Company not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class BankDetailsListAPI(ModifiedApiview):
    def get(self, request, company_id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)

            company = Company.objects.get(pk=company_id)
            bank_details = company.bank_details.all()
            
            data = []
            for bank in bank_details:
                data.append({
                    'id': bank.id,
                    'bank_name': bank.bank_name,
                    'account_number': bank.account_number,
                    'account_holder_name': bank.account_holder_name,
                    'ifsc_code': bank.ifsc_code,
                    'branch': bank.branch,
                    'created_at': bank.created_at,
                })
            
            return Response({'status': 'success', 'data': data}, status=status.HTTP_200_OK)
        
        except ObjectDoesNotExist:
            return Response(
                {'status': 'error', 'message': 'Company not found'},
                status=status.HTTP_404_NOT_FOUND
            )

class BankDetailsRetrieveAPI(ModifiedApiview):
    def get(self, request, company_id, pk):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)

            bank_detail = BankDetails.objects.get(pk=pk, company_id=company_id)
            
            data = {
                'id': bank_detail.id,
                'bank_name': bank_detail.bank_name,
                'account_number': bank_detail.account_number,
                'account_holder_name': bank_detail.account_holder_name,
                'ifsc_code': bank_detail.ifsc_code,
                'branch': bank_detail.branch,
                'created_at': bank_detail.created_at,
                'updated_at': bank_detail.updated_at,
            }
            
            return Response({'status': 'success', 'data': data}, status=status.HTTP_200_OK)
        
        except ObjectDoesNotExist:
            return Response(
                {'status': 'error', 'message': 'Bank details not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class BankDetailsUpdateAPI(ModifiedApiview):
    def put(self, request, company_id, pk):
        try:
            # Authentication check
            user = self.get_user_from_token(request)
            if not user:
                return Response(
                    {"status": "error", "message": "Authentication failed"}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )

            # Get bank detail instance
            bank_detail = BankDetails.objects.get(pk=pk, company_id=company_id)
            data = request.data
            
            # Validate required fields
            required_fields = ['bank_name', 'account_number', 'account_holder_name', 'ifsc_code']
            for field in required_fields:
                if not data.get(field):
                    return Response(
                        {"status": "error", "message": f"{field} is required"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Update all fields directly
            bank_detail.bank_name = data['bank_name'].strip()
            bank_detail.account_number = data['account_number'].strip()
            bank_detail.account_holder_name = data['account_holder_name'].strip()
            bank_detail.ifsc_code = data['ifsc_code'].strip().upper()
            bank_detail.branch = data['branch'].strip() if data.get('branch') else None
            
            bank_detail.save()
            
            # Prepare response data
            response_data = {
                "status": "success",
                "message": "Bank details updated successfully",
                "data": {
                    "id": bank_detail.id,
                    "bank_name": bank_detail.bank_name,
                    "account_number": bank_detail.account_number,
                    "account_holder_name": bank_detail.account_holder_name,
                    "ifsc_code": bank_detail.ifsc_code,
                    "updated_at": bank_detail.updated_at
                }
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except ObjectDoesNotExist:
            return Response(
                {"status": "error", "message": "Bank details not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        

class BankDetailsDeleteAPI(ModifiedApiview):
    def delete(self, request, company_id, pk):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)

            bank_detail = BankDetails.objects.get(pk=pk, company_id=company_id)
            bank_detail.delete()
            return Response(
                {'status': 'success', 'message': 'Bank details deleted successfully'},
                status=status.HTTP_204_NO_CONTENT
            )
        except ObjectDoesNotExist:
            return Response(
                {'status': 'error', 'message': 'Bank details not found'},
                status=status.HTTP_404_NOT_FOUND
            )