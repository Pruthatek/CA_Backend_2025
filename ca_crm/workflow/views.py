from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import (
    Department,
    WorkCategory,
    WorkCategoryFilesRequired,
    WorkCategoryActivityList,
    WorkCategoryUploadDocumetRequired,
)
from datetime import datetime, time
from rest_framework.permissions import IsAuthenticated
import jwt 
from django.conf import settings
from custom_auth.models import CustomUser

class ModifiedApiview(APIView):
    permission_classes = [IsAuthenticated]

    def get_user_from_token(self, request):
        token = request.headers.get("Authorization", "").split(" ")[1]
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("user_id")
            user = CustomUser.objects.get(id=user_id)
            return user
        except (jwt.ExpiredSignatureError, jwt.DecodeError, CustomUser.DoesNotExist):
            return None



class DepartmentCreateAPIView(ModifiedApiview):
    def post(self, request):
        try:
            user = self.get_user_from_token(request)
            data = request.data
            name = data.get("name")
            description = data.get("description", "")

            if not name:
                return Response({"error": "Name is required"}, status=status.HTTP_400_BAD_REQUEST)

            department = Department.objects.create(
                name=name,
                description=description,
                created_by_id=user
            )
            return Response({"message": "Department created", "id": department.id}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DepartmentGetAPIView(ModifiedApiview):
    def get(self, request, id=None):
        try:
            user = self.get_user_from_token(request)
            if id:
                department = Department.objects.filter(id=id, is_active=True).first()
                if not department:
                    return Response({"error": "Department not found"}, status=status.HTTP_404_NOT_FOUND)
                data = {
                    "id": department.id,
                    "name": department.name,
                    "description": department.description 
                }
                return Response(data, status=status.HTTP_200_OK)
            departments = Department.objects.filter(is_active=True).values("id", "name", "description")
            return Response(list(departments), status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DepartmentUpdateAPIView(ModifiedApiview):
    def put(self, request, id):
        try:
            user = self.get_user_from_token(request)
            department = Department.objects.filter(id=id, is_active=True).first()
            if not department:
                return Response({"error": "Department not found"}, status=status.HTTP_404_NOT_FOUND)

            data = request.data
            department.name = data.get("name", department.name)
            department.description = data.get("description", department.description)
            department.updated_by = user
            department.updated_date = datetime.now()
            department.save()

            return Response({"message": "Department updated"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DepartmentDeactivateAPIView(ModifiedApiview):
    def delete(self, request, id):
        try:
            user = self.get_user_from_token(request)
            department = Department.objects.filter(id=id, is_active=True).first()
            if not department:
                return Response({"error": "Department not found"}, status=status.HTTP_404_NOT_FOUND)
            department.is_active = False
            department.updated_by = user
            department.save()
            return Response({"message": "Department deactivated"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WorkCategoryCreateAPIView(ModifiedApiview):
    def post(self, request):
        try:
            user = self.get_user_from_token(request)
            data = request.data
            name = data.get("name")
            description = data.get("description", "")
            department = data.get("department")

            if not name or not department:
                return Response(
                    {"error": "Name and Department are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            work_category = WorkCategory.objects.create(
                name=name,
                description=description,
                department_id=department,
                created_by_id=user,
            )
            return Response(
                {"message": "Work category created", "id": work_category.id},
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WorkCategoryGetAPIView(ModifiedApiview):
    def get(self, request, id=None):
        try:
            user = self.get_user_from_token(request)
            if id:
                work_category = WorkCategory.objects.filter(id=id, is_active=True).first()
                if not work_category:
                    return Response({"error": "Work category not found"}, status=status.HTTP_404_NOT_FOUND)
                data = {
                    "id": work_category.id,
                    "name": work_category.name,
                    "description": work_category.description,
                    "department": work_category.department.name,
                }
                return Response(data, status=status.HTTP_200_OK)
            work_categories = WorkCategory.objects.filter(is_active=True).values("id", "name", "description", "department")
            return Response(list(work_categories), status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WorkCategoryUpdateAPIView(ModifiedApiview):
    def put(self, request, id):
        try:
            user = self.get_user_from_token(request)
            work_category = WorkCategory.objects.filter(id=id, is_active=True).first()
            if not work_category:
                return Response({"error": "Work category not found"}, status=status.HTTP_404_NOT_FOUND)

            data = request.data
            work_category.name = data.get("name", work_category.name)
            work_category.description = data.get("description", work_category.description)
            work_category.save()

            return Response({"message": "Work category updated"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WorkCategoryDeactivateAPIView(ModifiedApiview):
    def delete(self, request, id):
        try:
            user = self.get_user_from_token(request)
            work_category = WorkCategory.objects.filter(id=id, is_active=True).first()
            if not work_category:
                return Response({"error": "Work category not found"}, status=status.HTTP_404_NOT_FOUND)
            work_category.is_active = False
            work_category.updated_by = user
            work_category.save()
            return Response({"message": "Work category deactivated"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WorkCategoryFilesRequiredCreateAPIView(ModifiedApiview):
    def post(self, request):
        try:
            user = self.get_user_from_token(request)
            data = request.data
            work_category = data.get("work_category")
            file_name = data.get("file_name")
            description = data.get("description", "")

            if not work_category or not file_name:
                return Response(
                    {"error": "Work Category and File Name are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            file_required = WorkCategoryFilesRequired.objects.create(
                work_category_id=work_category,
                file_name=file_name,
                description=description,
                created_by_id=user,
            )
            return Response(
                {"message": "File required created", "id": file_required.id},
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WorkCategoryFilesRequiredGetAPIView(ModifiedApiview):
    def get(self, request, id=None):
        try:
            user = self.get_user_from_token(request)
            if id:
                work_category_files = WorkCategoryFilesRequired.objects.filter(id=id, is_active=True).first()
                if not work_category_files:
                    return Response({"error": "Work category not found"}, status=status.HTTP_404_NOT_FOUND)
                data = {
                    "id": work_category_files.id,
                    "file_name": work_category_files.file_name,
                    "description": work_category_files.description,
                    "work_category": work_category_files.work_category.name,
                }
                return Response(data, status=status.HTTP_200_OK)
            work_categories = WorkCategoryFilesRequired.objects.filter(is_active=True).values("id", "file_name", "description", "work_category")
            return Response(list(work_categories), status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WorkCategoryFilesRequiredUpdateAPIView(ModifiedApiview):
    def put(self, request, id):
        try:
            user = self.get_user_from_token(request)
            work_category_file = WorkCategoryFilesRequired.objects.filter(id=id, is_active=True).first()
            if not work_category_file:
                return Response({"error": "Work category file not found"}, status=status.HTTP_404_NOT_FOUND)

            data = request.data
            work_category_file.file_name = data.get("file_name", work_category_file.file_name)
            work_category_file.description = data.get("description", work_category_file.description)
            work_category_file.updated_by = user
            work_category_file.save()

            return Response({"message": "Work category updated"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WorkCategoryFilesRequiredDeactivateAPIView(ModifiedApiview):
    def delete(self, request, id):
        try:
            user = self.get_user_from_token(request)
            work_category = WorkCategoryFilesRequired.objects.filter(id=id, is_active=True).first()
            if not work_category:
                return Response({"error": "Work category file not found"}, status=status.HTTP_404_NOT_FOUND)
            work_category.is_active = False
            work_category.updated_by = user
            work_category.save()
            return Response({"message": "Work category file deactivated"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WorkCategoryActivityListCreateAPIView(ModifiedApiview):
    def post(self, request):
        try:
            data = request.data
            work_category = data.get("work_category")
            activity_name = data.get("activity_name")
            description = data.get("description", "")
            created_by = data.get("created_by")

            if not work_category or not activity_name:
                return Response(
                    {"error": "Work Category and Activity Name are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            activity_list = WorkCategoryActivityList.objects.create(
                work_category_id=work_category,
                activity_name=activity_name,
                description=description,
                created_by_id=created_by,
            )
            return Response(
                {"message": "Activity list created", "id": activity_list.id},
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WorkCategoryActivityListGetAPIView(ModifiedApiview):
    def get(self, request, id=None):
        try:
            user = self.get_user_from_token(request)
            if id:
                work_category = WorkCategoryActivityList.objects.filter(id=id, is_active=True).first()
                if not work_category:
                    return Response({"error": "Work category not found"}, status=status.HTTP_404_NOT_FOUND)
                data = {
                    "id": work_category.id,
                    "activity_name": work_category.activity_name,
                    "description": work_category.description,
                    "work_category": work_category.work_category.name,
                }
                return Response(data, status=status.HTTP_200_OK)
            work_categories = WorkCategoryActivityList.objects.filter(is_active=True).values("id", "activity_name", 
                    "description", "work_category")
            return Response(list(work_categories), status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WorkCategoryActivityListUpdateAPIView(ModifiedApiview):
    def put(self, request, id):
        try:
            user = self.get_user_from_token(request)
            work_category = WorkCategoryActivityList.objects.filter(id=id, is_active=True).first()
            if not work_category:
                return Response({"error": "Work category not found"}, status=status.HTTP_404_NOT_FOUND)

            data = request.data
            work_category.activity_name = data.get("activity_name", work_category.activity_name)
            work_category.description = data.get("description", work_category.description)
            work_category.updated_by = user
            work_category.save()

            return Response({"message": "Work category updated"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WorkCategoryActivityListDeactivateAPIView(ModifiedApiview):
    def delete(self, request, id):
        try:
            user = self.get_user_from_token(request)
            work_category = WorkCategoryActivityList.objects.filter(id=id, is_active=True).first()
            if not work_category:
                return Response({"error": "Work category not found"}, status=status.HTTP_404_NOT_FOUND)
            work_category.is_active = False
            work_category.updated_by = user
            work_category.save()
            return Response({"message": "Work category deactivated"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WorkCategoryUploadDocumentRequiredCreateAPIView(ModifiedApiview):
    def post(self, request):
        try:
            user = self.get_user_from_token(request)
            data = request.data
            work_category = data.get("work_category")
            file_name = data.get("file_name")
            description = data.get("description", "")

            if not work_category or not file_name:
                return Response(
                    {"error": "Work Category and File Name are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            upload_document = WorkCategoryUploadDocumetRequired.objects.create(
                work_category_id=work_category,
                file_name=file_name,
                description=description,
                created_by_id=user,
            )
            return Response(
                {"message": "Upload document required created", "id": upload_document.id},
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WorkCategoryUploadDocumentRequiredGetAPIView(ModifiedApiview):
    def get(self, request, id=None):
        try:
            user = self.get_user_from_token(request)
            if id:
                work_category = WorkCategoryUploadDocumetRequired.objects.filter(id=id, is_active=True).first()
                if not work_category:
                    return Response({"error": "Work category not found"}, status=status.HTTP_404_NOT_FOUND)
                data = {
                    "id": work_category.id,
                    "file_name": work_category.file_name,
                    "description": work_category.description,
                    "work_category": work_category.work_category.name,
                }
                return Response(data, status=status.HTTP_200_OK)
            work_categories = WorkCategoryUploadDocumetRequired.objects.filter(is_active=True).values("id", "file_name", 
                    "description", "work_category")
            return Response(list(work_categories), status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WorkCategoryUploadDocumentRequiredUpdateAPIView(ModifiedApiview):
    def put(self, request, id):
        try:
            user = self.get_user_from_token(request)
            work_category = WorkCategoryUploadDocumetRequired.objects.filter(id=id, is_active=True).first()
            if not work_category:
                return Response({"error": "Work category required file not found"}, status=status.HTTP_404_NOT_FOUND)

            data = request.data
            work_category.file_name = data.get("file_name", work_category.file_name)
            work_category.description = data.get("description", work_category.description)
            work_category.updated_by = user
            work_category.save()

            return Response({"message": "Work category required file updated"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WorkCategoryUploadDocumentRequiredDeactivateAPIView(ModifiedApiview):
    def delete(self, request, id):
        try:
            user = self.get_user_from_token(request)
            work_category = WorkCategoryUploadDocumetRequired.objects.filter(id=id, is_active=True).first()
            if not work_category:
                return Response({"error": "Work category required file not found"}, status=status.HTTP_404_NOT_FOUND)
            work_category.is_active = False
            work_category.updated_by = user
            work_category.save()
            return Response({"message": "Work category required filedeactivated"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
