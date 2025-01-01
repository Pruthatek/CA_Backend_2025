from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import CustomUser, Permission, Role, RolePermission
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAdminUser,AllowAny, IsAuthenticated


class CreateUserView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        data = request.data
        try:
            # Create the user
            user = CustomUser.objects.create(
                username=data['username'],
                email=data['email'],
                password=make_password(data['password']),
                first_name=data.get('first_name', ''),
                last_name=data.get('last_name', ''),
            )

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            return Response(
                {
                    'user_id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                },
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


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
            return Response(
                {
                    'user_id': user.id,
                    'username': user.username,
                    'email': user.email,
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
