from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import CustomUser, Permission, Role, RolePermission, EmployeeProfile, ReportingUser, FamilyMemberDetails
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAdminUser,AllowAny, IsAuthenticated
import posixpath
from django.core.files.storage import FileSystemStorage
import traceback
from django.conf import settings
import pandas as pd
from datetime import datetime, date
import os
import uuid
import time


def generate_short_unique_filename(extension):
    # Shortened UUID (6 characters) + Unix timestamp for uniqueness
    unique_id = uuid.uuid4().hex[:6]  # Get the first 6 characters of UUID
    timestamp = str(int(time.time()))  # Unix timestamp as a string
    return f"{unique_id}_{timestamp}{extension}"


class CreateEmployeeView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        try:
            # Handle photo upload
            photo_url = request.FILES.get("photo_url")
            if photo_url:
                extension = os.path.splitext(photo_url.name)[1]
                short_unique_filename = generate_short_unique_filename(extension)
                fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'photo_urls'))
                logo_path = fs.save(short_unique_filename, photo_url)
                logo_url = posixpath.join('media/photo_urls', logo_path)
            else:
                logo_url = ""

            # Create the user
            user = CustomUser.objects.create(
                username=data['username'],
                email=data['email'],
                password=make_password(data['password']),
                first_name=data.get('first_name', ''),
                last_name=data.get('last_name', ''),
                gender=data.get('gender', ''),
                phone_number=data.get('phone_number', ''),
                employee_code=data.get('employee_code', ''),
                address=data.get('address', ''),
                photo_url=logo_url,
                role=Role.objects.get(name=data.get('role', 'employee')),  # Assuming 'employee' is a valid role
            )

            # Create EmployeeProfile entry
            EmployeeProfile.objects.create(
                user=user,
                date_of_joining=data.get('date_of_joining'),
                date_of_leaving=data.get('date_of_leaving', None),
                referred_by=data.get('referred_by', ''),
                designation=data.get('designation', ''),
                is_active=data.get('is_active', True),
                login_enabled=data.get('login_enabled', True),
            )

            # Create ReportingUser entry
            if data.get('reporting_to', None) and data.get('working_under', None):
                # Check if referenced user exists
                try:
                    
                    reporting_to_user = CustomUser.objects.get(id=data['reporting_to'])
                    working_under_user = CustomUser.objects.get(id=data['working_under'])
                    ReportingUser.objects.create(
                        user=user,
                        reporting_to=reporting_to_user,
                        working_under=working_under_user,
                        is_active=True,
                    )
                except CustomUser.DoesNotExist:
                    return Response(
                        {'error': 'Reporting to or working under user not found'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # Create ReportingUser entry

            family_data = data.get('family_details', [])
            if family_data:
                for member in family_data:
                    FamilyMemberDetails.objects.create(
                        user=user,
                        name=member.get('name'),
                        relationship=member.get('relation'),
                        contact_no=member.get('contact_number'),
                        email=member.get('email'),
                        is_active=True,
                    )

            # Generate JWT tokens
            return Response(
                {
                    'user_id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'message': 'Employee created successfully',
                },
                status=status.HTTP_201_CREATED,
            )

        except CustomUser.DoesNotExist as e:
            return Response(
                {'error': f"Referenced user not found: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class EmployeeListView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        # Fetch Employee data with related user and reporting details
        employees = EmployeeProfile.objects.select_related('user').filter(is_active=True, user__is_active=True)
        reporting_data = ReportingUser.objects.select_related('user', 'reporting_to', 'working_under').filter(is_active=True, user__is_active=True)
        family_members = FamilyMemberDetails.objects.select_related('user').filter(is_active=True, user__is_active=True)
        # Convert QuerySets to lists of dictionaries
        employee_data = [
            {
                "employee_id":emp.user.id,
                "employee_name": emp.user.username,
                "designation": emp.designation,
                "email": emp.user.email,
                "phone": emp.user.phone_number,
            }
            for emp in employees
        ]

        reporting_dict = {
            rep.user.id: {
                "reporting_to": rep.reporting_to.username if rep.reporting_to else None,
                "working_under": rep.working_under.username if rep.working_under else None,
            }
            for rep in reporting_data
        }

        family_dict = {
            member.user.id: {
                "id"
                "name": member.name,
                "relation": member.relationship,
                "contact_number": member.contact_no,
                "email": member.email,
            }
            for member in family_members
        }

        # Convert to DataFrame for fast processing
        df_employees = pd.DataFrame(employee_data)
        df_reporting = pd.DataFrame.from_dict(reporting_dict, orient="index").reset_index().rename(columns={"index": "user_id"})
        df_family = pd.DataFrame.from_dict(family_dict, orient="index").reset_index().rename(columns={"index": "user_id"})

        # Merge DataFrames
        df_merged = pd.merge(df_employees, df_reporting, how="left", left_on="employee_name", right_on="user_id")
        df_merged = pd.merge(df_merged, df_family, how="left", left_on="employee_id", right_on="user_id")
        df_merged.drop(columns=["user_id"], inplace=True)

        # Replace NaN values with None
        df_merged.fillna("", inplace=True)

        # Convert to list of dicts for JSON response
        response_data = df_merged.to_dict(orient="records")

        return Response({"employees": response_data}, status=status.HTTP_200_OK)


class RetrieveEmployeeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        try:
            user = CustomUser.objects.get(id=user_id)
            employee_profile = EmployeeProfile.objects.get(user=user)
            
            # Try fetching the ReportingUser, but handle if it doesn't exist
            try:
                reporting_user = ReportingUser.objects.get(user=user)
                reporting_data = {
                    "reporting_to": reporting_user.reporting_to.id if reporting_user.reporting_to else None,
                    "working_under": reporting_user.working_under.id if reporting_user.working_under else None,
                    "is_active": reporting_user.is_active,
                } if reporting_user.reporting_to else None
            except ReportingUser.DoesNotExist:
                reporting_data = None

            try:
                family_members = FamilyMemberDetails.objects.filter(user=user, is_active=True)
                family_data = [
                    {
                        "name": member.name,
                        "relation": member.relationship,
                        "contact_number": member.contact_no,
                        "email": member.email,
                    }
                    for member in family_members
                ]
            except FamilyMemberDetails.DoesNotExist:
                family_data = []

            data = {
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "phone_number": user.phone_number,
                    "address": user.address,
                },
                "employee_profile": {
                    "date_of_joining": employee_profile.date_of_joining,
                    "date_of_leaving": employee_profile.date_of_leaving,
                    "referred_by": employee_profile.referred_by,
                    "designation": employee_profile.designation,
                    "is_active": employee_profile.is_active,
                    "login_enabled": employee_profile.login_enabled,
                },
                "family_details": family_data
            }

            if reporting_data:
                data["reporting_user"] = reporting_data

            return Response(data, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        except EmployeeProfile.DoesNotExist:
            return Response({"error": "Employee profile not found"}, status=status.HTTP_404_NOT_FOUND)


class UpdateEmployeeView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, user_id):
        data = request.data
        try:
            user = CustomUser.objects.get(id=user_id)
            employee_profile = EmployeeProfile.objects.get(user=user)
            try:
                reporting_user = ReportingUser.objects.get(user=user)
            except ReportingUser.DoesNotExist:
                reporting_user = None
            # Update user fields
            user.first_name = data.get('first_name', user.first_name)
            user.last_name = data.get('last_name', user.last_name)
            user.phone_number = data.get('phone_number', user.phone_number)
            user.address = data.get('address', user.address)
            user.save()

            # Update employee profile
            employee_profile.date_of_joining = data.get('date_of_joining', employee_profile.date_of_joining)
            employee_profile.date_of_leaving = data.get('date_of_leaving', employee_profile.date_of_leaving)
            employee_profile.referred_by = data.get('referred_by', employee_profile.referred_by)
            employee_profile.designation = data.get('designation', employee_profile.designation)
            employee_profile.is_active = data.get('is_active', employee_profile.is_active)
            employee_profile.login_enabled = data.get('login_enabled', employee_profile.login_enabled)
            employee_profile.save()

            # Update reporting user only if mappings change
            if reporting_user:
                if 'reporting_to' in data:
                    new_reporting_to = CustomUser.objects.get(id=data['reporting_to']) if data['reporting_to'] else None
                    if reporting_user.reporting_to != new_reporting_to:
                        reporting_user.reporting_to = new_reporting_to

                if 'working_under' in data:
                    new_working_under = CustomUser.objects.get(id=data['working_under']) if data['working_under'] else None
                    if reporting_user.working_under != new_working_under:
                        reporting_user.working_under = new_working_under
                reporting_user.is_active = data.get('is_active', reporting_user.is_active)
                reporting_user.save()

            # Update family members
            if 'family_members' in data:
                family_members_data = data['family_members']
                existing_family_members = FamilyMemberDetails.objects.filter(user=user)

                # Create a set of existing family member IDs
                existing_family_member_ids = set(existing_family_members.values_list('id', flat=True))

                # Iterate through the provided family members data
                for member_data in family_members_data:
                    member_id = member_data.get('id')
                    if member_id:
                        # Update existing family member
                        family_member = existing_family_members.get(id=member_id)
                        family_member.name = member_data.get('name', family_member.name)
                        family_member.relationship = member_data.get('relationship', family_member.relationship)
                        family_member.contact_no = member_data.get('contact_no', family_member.contact_no)
                        family_member.email = member_data.get('email', family_member.email)
                        family_member.is_active = member_data.get('is_active', family_member.is_active)
                        family_member.save()

                        # Remove the ID from the set of existing IDs
                        existing_family_member_ids.discard(member_id)
                    else:
                        # Create a new family member
                        FamilyMemberDetails.objects.create(
                            user=user,
                            name=member_data.get('name'),
                            relationship=member_data.get('relationship'),
                            contact_no=member_data.get('contact_no'),
                            email=member_data.get('email'),
                            is_active=member_data.get('is_active', True)
                        )

                # Delete family members that were not included in the request
                if existing_family_member_ids:
                    FamilyMemberDetails.objects.filter(id__in=existing_family_member_ids).delete()

            return Response({"message": "User updated successfully"}, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        except EmployeeProfile.DoesNotExist:
            return Response({"error": "Employee profile not found"}, status=status.HTTP_404_NOT_FOUND)
        except ReportingUser.DoesNotExist:
            return Response({"error": "Reporting user not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        data = request.data
        try:
            user = CustomUser.objects.get(email=data['email'])
            
            # Check password
            if not check_password(data['password'], user.password):
                return Response(
                    {'error': 'Invalid credentials'},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            
            if not user.is_active:
                return Response(
                    {'error': 'User account is inactive'},
                    status=status.HTTP_403_FORBIDDEN,
                )

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            user_details = {
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role.name,
            }
            return Response(
                {
                    'user_details': user_details,
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                },
                status=status.HTTP_200_OK,
            )
        except CustomUser.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND,
            )


class CheckPermissionView(APIView):
    def get(self, request):
        try:
            user_id = request.query_params.get('user_id')
            permission_name = request.query_params.get('permission_name')

            # Validate inputs
            if not user_id or not permission_name:
                return Response({'error': 'user_id and permission_name are required'}, status=status.HTTP_400_BAD_REQUEST)

            # Fetch user
            user = CustomUser.objects.get(id=user_id, is_active=True)
            role = user.role

            if not role:
                return Response({'error': f'{user.username} does not have a role assigned'}, status=status.HTTP_404_NOT_FOUND)

            # Check if the role has the permission
            has_permission = RolePermission.objects.filter(
                role=role,
                permission__name=permission_name,
                is_active=True
            ).exists()

            if has_permission:
                return Response({'message': f'User {user.username} has permission: {permission_name}'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': f'User {user.username} does not have permission: {permission_name}'}, status=status.HTTP_403_FORBIDDEN)

        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found or inactive'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AssignRoleView(APIView):
    def post(self, request):
        try:
            user_id = request.data.get('user_id')
            role_id = request.data.get('role_id')

            # Validate inputs
            if not user_id or not role_id:
                return Response({'error': 'user_id and role_id are required'}, status=status.HTTP_400_BAD_REQUEST)

            # Fetch user and role
            user = CustomUser.objects.get(id=user_id, is_active=True)
            role = Role.objects.get(id=role_id, is_active=True)

            # Assign role
            user.role = role
            user.save()

            return Response({'message': f'Role {role.name} assigned to {user.username}'}, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found or inactive'}, status=status.HTTP_404_NOT_FOUND)
        except Role.DoesNotExist:
            return Response({'error': 'Role not found or inactive'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RoleCreateAPIView(APIView):
    def post(self, request):
        """Create a new role"""
        name = request.data.get("name")
        description = request.data.get("description")

        if not name:
            return Response({"error": "Name is required"}, status=status.HTTP_400_BAD_REQUEST)

        role = Role.objects.create(name=name, description=description)
        return Response(
            {
                "id": role.id,
                "name": role.name,
                "description": role.description,
                "is_active": role.is_active,
                "created_on": role.created_on,
                "updated_on": role.updated_on,
            },
            status=status.HTTP_201_CREATED,
        )


class RoleListAPIView(APIView):
    def get(self, request):
        """Retrieve all active roles"""
        roles = Role.objects.filter(is_active=True).values(
            "id", "name", "description", "is_active", "created_on", "updated_on"
        )
        return Response(list(roles), status=status.HTTP_200_OK)


class RoleUpdateAPIView(APIView):
    def put(self, request, role_id):
        """Update an existing role"""
        try:
            role = Role.objects.get(id=role_id)
            role.name = request.data.get("name", role.name)
            role.description = request.data.get("description", role.description)
            role.save()

            return Response(
                {
                    "id": role.id,
                    "name": role.name,
                    "description": role.description,
                    "is_active": role.is_active,
                    "created_on": role.created_on,
                    "updated_on": role.updated_on,
                },
                status=status.HTTP_200_OK,
            )
        except Role.DoesNotExist:
            return Response({"error": "Role not found"}, status=status.HTTP_404_NOT_FOUND)


class RoleDeleteAPIView(APIView):
    def delete(self, request, role_id):
        """Soft delete a role"""
        try:
            role = Role.objects.get(id=role_id)
            role.is_active = False
            role.save()
            return Response({"message": "Role deleted successfully"}, status=status.HTTP_200_OK)
        except Role.DoesNotExist:
            return Response({"error": "Role not found"}, status=status.HTTP_404_NOT_FOUND)


class PermissionCreateAPIView(APIView):
    def post(self, request):
        """Create a new permission"""
        name = request.data.get("name")
        description = request.data.get("description")

        if not name:
            return Response({"error": "Name is required"}, status=status.HTTP_400_BAD_REQUEST)

        permission = Permission.objects.create(name=name, description=description)
        return Response(
            {
                "id": permission.id,
                "name": permission.name,
                "description": permission.description,
                "is_active": permission.is_active,
                "created_on": permission.created_on,
                "updated_on": permission.updated_on,
            },
            status=status.HTTP_201_CREATED,
        )


class PermissionListAPIView(APIView):
    def get(self, request):
        """Retrieve all active permissions"""
        permissions = Permission.objects.filter(is_active=True).values(
            "id", "name", "description", "is_active", "created_on", "updated_on"
        )
        return Response(list(permissions), status=status.HTTP_200_OK)


class PermissionUpdateAPIView(APIView):
    def put(self, request, permission_id):
        """Update an existing permission"""
        try:
            permission = Permission.objects.get(id=permission_id)
            permission.name = request.data.get("name", permission.name)
            permission.description = request.data.get("description", permission.description)
            permission.save()

            return Response(
                {
                    "id": permission.id,
                    "name": permission.name,
                    "description": permission.description,
                    "is_active": permission.is_active,
                    "created_on": permission.created_on,
                    "updated_on": permission.updated_on,
                },
                status=status.HTTP_200_OK,
            )
        except Permission.DoesNotExist:
            return Response({"error": "Permission not found"}, status=status.HTTP_404_NOT_FOUND)


class PermissionDeleteAPIView(APIView):
    def delete(self, request, permission_id):
        """Soft delete a permission"""
        try:
            permission = Permission.objects.get(id=permission_id)
            permission.is_active = False
            permission.save()
            return Response({"message": "Permission deleted successfully"}, status=status.HTTP_200_OK)
        except Permission.DoesNotExist:
            return Response({"error": "Permission not found"}, status=status.HTTP_404_NOT_FOUND)


class RolePermissionAddAPIView(APIView):
    def post(self, request):
        """Add permissions to a role"""
        role_id = request.data.get("role_id")
        permission_ids = request.data.get("permission_ids", [])  # List of permission IDs

        if not role_id or not permission_ids:
            return Response({"error": "role_id and permission_ids are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            role = Role.objects.get(id=role_id)
            for permission_id in permission_ids:
                permission = Permission.objects.get(id=permission_id)
                RolePermission.objects.get_or_create(role=role, permission=permission)

            return Response({"message": "Permissions added to role successfully"}, status=status.HTTP_200_OK)

        except Role.DoesNotExist:
            return Response({"error": "Role not found"}, status=status.HTTP_404_NOT_FOUND)
        except Permission.DoesNotExist:
            return Response({"error": "One or more permissions not found"}, status=status.HTTP_404_NOT_FOUND)


class RolePermissionListAPIView(APIView):
    def get(self, request, role_id):
        """List all permissions for a specific role"""
        try:
            role = Role.objects.get(id=role_id)
            permissions = role.permissions.filter(is_active=True).values(
                "id", "permission__name", "permission__description", "is_active", "created_on", "updated_on"
            )
            permissions_df = pd.DataFrame.from_records(list(permissions))
            permissions_df.rename(columns={
                "permission__name": "name",
                "permission__description": "description"
            }, inplace=True)

            return Response({"role": role.name, "permissions": permissions_df.to_dict("records")}, status=status.HTTP_200_OK)

        except Role.DoesNotExist:
            return Response({"error": "Role not found"}, status=status.HTTP_404_NOT_FOUND)


class RolePermissionRemoveAPIView(APIView):
    def post(self, request):
        """Remove permissions from a role"""
        role_id = request.data.get("role_id")
        permission_ids = request.data.get("permission_ids", [])  # List of permission IDs

        if not role_id or not permission_ids:
            return Response({"error": "role_id and permission_ids are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            role = Role.objects.get(id=role_id)
            for permission_id in permission_ids:
                permission = Permission.objects.get(id=permission_id)
                RolePermission.objects.filter(role=role, permission=permission).delete()

            return Response({"message": "Permissions removed from role successfully"}, status=status.HTTP_200_OK)

        except Role.DoesNotExist:
            return Response({"error": "Role not found"}, status=status.HTTP_404_NOT_FOUND)
        except Permission.DoesNotExist:
            return Response({"error": "One or more permissions not found"}, status=status.HTTP_404_NOT_FOUND)


class BulkCreateEmployeeView(APIView):
    def post(self, request):
        try:
            excel_file = request.FILES.get("file")
            if not excel_file:
                return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)
            
            # Read the Excel file
            df = pd.read_excel(excel_file)
            
            created_users = []
            errors = []
            
            for _, row in df.iterrows():
                try:
                    # Handle photo upload if provided
                    photo_url = row.get("photo_url", "")
                    logo_url = ""
                    if photo_url:
                        extension = os.path.splitext(photo_url)[1]
                        short_unique_filename = generate_short_unique_filename(extension)
                        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'photo_urls'))
                        logo_path = fs.save(short_unique_filename, photo_url)
                        logo_url = os.path.join('media/photo_urls', logo_path)
                    
                    # Create user
                    user = CustomUser.objects.create(
                        username=row["username"],
                        email=row["email"],
                        password=make_password(row["password"]),
                        first_name=row.get("first_name", ""),
                        last_name=row.get("last_name", ""),
                        gender=row.get("gender", ""),
                        phone_number=row.get("phone_number", ""),
                        employee_code=row.get("employee_code", ""),
                        address=row.get("address", ""),
                        photo_url=logo_url,
                        role=Role.objects.get(name=row.get("role", "employee")),
                    )
                    
                    # Create EmployeeProfile
                    EmployeeProfile.objects.create(
                        user=user,
                        date_of_joining=row.get("date_of_joining"),
                        date_of_leaving=row.get("date_of_leaving", None),
                        referred_by=row.get("referred_by", ""),
                        designation=row.get("designation", ""),
                        is_active=row.get("is_active", True),
                        login_enabled=row.get("login_enabled", True),
                    )
                    
                    # Create ReportingUser
                    if row.get("reporting_to") and row.get("working_under"):
                        reporting_to_user = CustomUser.objects.get(id=row["reporting_to"])
                        working_under_user = CustomUser.objects.get(id=row["working_under"])
                        ReportingUser.objects.create(
                            user=user,
                            reporting_to=reporting_to_user,
                            working_under=working_under_user,
                            is_active=True,
                        )
                    
                    created_users.append({"username": user.username, "email": user.email})
                except Exception as e:
                    errors.append({"username": row.get("username"), "error": str(e)})
            
            return Response({"created_users": created_users, "errors": errors}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
