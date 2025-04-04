from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from rest_framework import status
from openpyxl import load_workbook
from ca_crm.email_service import send_email
import pandas as pd
from .models import (
    Department,
    WorkCategory,
    WorkCategoryFilesRequired,
    WorkCategoryActivityList,
    WorkCategoryActivityStages,
    WorkCategoryDate,
    WorkCategoryUploadDocumentRequired,
    ClientWorkCategoryAssignment,
    AssignedWorkRequiredFiles,
    AssignedWorkActivity,
    AssignedWorkActivityStages,
    AssignedWorkOutputFiles,
    ScheduleTaskTime,
    ClientWorkReminder,
)
from employees.models import TimeTracking 
from datetime import datetime, time
from rest_framework.permissions import IsAuthenticated
import jwt 
from django.conf import settings
from custom_auth.models import CustomUser
from django.db import models
from clients.models import Customer
from django.db import transaction
import os
import uuid
from django.core.files.storage import FileSystemStorage
import posixpath
from django.db.models import Sum, F, OuterRef, Subquery, Prefetch, Count
from billing.models import (
    ClientWorkCategoryAssignment, Expense, Billing, BillItems, ExpenseItems, Receipt, ReceiptInvoice
)

import cloudinary.uploader
import cloudinary.api


def upload_to_cloudinary(file):
    """Uploads a file to Cloudinary and returns the file URL."""
    try:
        result = cloudinary.uploader.upload(file)
        return result.get("secure_url")  # Returns the public URL of the uploaded file
    except Exception as e:
        raise Exception(f"Cloudinary Upload Error: {e}")


def get_cloudinary_file(file_url):
    """Fetches a specific file from Cloudinary."""
    try:
        public_id = file_url.split("/")[-1].split(".")[0]  # Extract public ID from URL
        resource = cloudinary.api.resource(public_id)
        return resource.get("secure_url")  # Return the file URL
    except Exception as e:
        raise Exception(f"Cloudinary Fetch Error: {e}")



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
            if not user:
                return Response({"Error":"You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            data = request.data
            name = data.get("name")
            manager = data.get("manager")

            if not name:
                return Response({"error": "Name is required"}, status=status.HTTP_400_BAD_REQUEST)

            if manager:
                manager_details = CustomUser.objects.filter(id=manager, is_active=True).first()
            else:
                manager_details = None

            department = Department.objects.create(
                name=name,
                created_by=user,
                manager=manager_details
            )
            return Response({"message": "Department created", "id": department.id}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DepartmentGetAPIView(ModifiedApiview):
    def get(self, request, id=None):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            if id:
                department = Department.objects.filter(id=id, is_active=True).first()
                if not department:
                    return Response({"error": "Department not found"}, status=status.HTTP_404_NOT_FOUND)
                data = {
                    "id": department.id,
                    "name": department.name,
                    "manager":department.manager.username
                }
                return Response(data, status=status.HTTP_200_OK)
            departments = Department.objects.filter(is_active=True).values("id", "name")
            return Response(list(departments), status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DepartmentUpdateAPIView(ModifiedApiview):
    def put(self, request, id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            department = Department.objects.filter(id=id, is_active=True).first()
            if not department:
                return Response({"error": "Department not found"}, status=status.HTTP_404_NOT_FOUND)

            data = request.data
            manager = data.get("manager")
            if manager:
                manager_details = CustomUser.objects.filter(id=manager, is_active=True).first()
            else:
                manager_details = department.manager
            department.name = data.get("name", department.name)
            department.updated_by = user
            department.manager = manager_details
            department.updated_date = datetime.now()
            department.save()

            return Response({"message": "Department updated"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DepartmentDeactivateAPIView(ModifiedApiview):
    def delete(self, request, id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
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
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)

            data = request.data
            name = data.get("name")
            department_id = data.get("department")
            fees = data.get("fees", 0)
            dates = data.get("dates", [])  # List of date entries

            # Validate required fields
            if not name or not department_id:
                return Response(
                    {"error": "Name and Department are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Fetch department
            department = Department.objects.filter(id=department_id, is_active=True).first()
            if not department:
                return Response(
                    {"error": "Invalid Department"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Use a transaction to ensure atomicity
            with transaction.atomic():
                # Create WorkCategory
                work_category = WorkCategory.objects.create(
                    name=name,
                    department=department,
                    fees=fees,
                    created_by=user,
                )

                # Create WorkCategoryDate entries
                for date_entry in dates:
                    date_type = date_entry.get("date_type")
                    day = date_entry.get("day")
                    month = date_entry.get("month", None)  # Optional for monthly

                    # Validate date_type and day
                    if not date_type or not day:
                        raise ValueError("date_type and day are required for each date entry")

                    # Validate month for yearly type
                    if date_type == "yearly" and not month:
                        raise ValueError("month is required for yearly date_type")

                    # Create WorkCategoryDate
                    WorkCategoryDate.objects.create(
                        work_category=work_category,
                        date_type=date_type,
                        day=day,
                        month=month,
                    )

            return Response(
                {
                    "message": "Work category created successfully",
                    "id": work_category.id,
                },
                status=status.HTTP_201_CREATED,
            )

        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class WorkCategoryGetAPIView(ModifiedApiview):
    def get(self, request, id=None):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            if id:
                work_category = WorkCategory.objects.filter(id=id, is_active=True).first()
                if not work_category:
                    return Response({"error": "Work category not found"}, status=status.HTTP_404_NOT_FOUND)
                data = {
                    "id": work_category.id,
                    "name": work_category.name,
                    "fees": work_category.fees,
                    "department": work_category.department.name,
                }
                return Response(data, status=status.HTTP_200_OK)
            work_categories = WorkCategory.objects.filter(is_active=True).values("id", "name", "department")
            return Response(list(work_categories), status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WorkCategoryUpdateAPIView(ModifiedApiview):
    def put(self, request, id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)

            work_category = WorkCategory.objects.filter(id=id, is_active=True).first()
            if not work_category:
                return Response({"error": "Work category not found"}, status=status.HTTP_404_NOT_FOUND)

            data = request.data
            name = data.get("name")
            fees = data.get("fees")
            dates = data.get("dates", [])  # List of date entries

            # Use a transaction to ensure atomicity
            with transaction.atomic():
                # Update WorkCategory fields if provided
                if name is not None:
                    work_category.name = name
                if fees is not None:
                    work_category.fees = fees
                work_category.updated_by = user
                work_category.save()

                # Delete existing WorkCategoryDate entries
                work_category.dates.all().delete()

                # Create new WorkCategoryDate entries
                for date_entry in dates:
                    date_type = date_entry.get("date_type")
                    day = date_entry.get("day")
                    month = date_entry.get("month", None)  # Optional for monthly

                    # Validate date_type and day
                    if not date_type or not day:
                        raise ValueError("date_type and day are required for each date entry")

                    # Validate month for yearly type
                    if date_type == "yearly" and not month:
                        raise ValueError("month is required for yearly date_type")

                    # Create WorkCategoryDate
                    WorkCategoryDate.objects.create(
                        work_category=work_category,
                        date_type=date_type,
                        day=day,
                        month=month,
                    )

            return Response(
                {"message": "Work category updated successfully"},
                status=status.HTTP_200_OK,
            )

        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class GetDepartmentWorkCategoriesAPIView(ModifiedApiview):
    def get(self, request, id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            work_categories = WorkCategory.objects.filter(department_id=id, is_active=True).values("id", "name", "fees")
            data = []
            for work_category in work_categories:
                wc_data = {
                    "id": work_category["id"],
                    "name": work_category["name"],
                    "fees": work_category["fees"],
                    "files_required": list(WorkCategoryFilesRequired.objects.filter(work_category_id=work_category["id"], is_active=True).values("file_name", "id")),
                    "activities": list(WorkCategoryActivityList.objects.filter(work_category_id=work_category["id"], is_active=True).values("activity_name", "assigned_percentage", "id")),
                    "activity_stages": list(WorkCategoryActivityStages.objects.filter(work_category_id=work_category["id"], is_active=True).values("activity_stage", "description", "id")),
                    "output_files": list(WorkCategoryUploadDocumentRequired.objects.filter(work_category_id=work_category["id"], is_active=True).values("file_name", "id")),
                }
                data.append(wc_data)
            return Response(data, status=status.HTTP_200_OK)        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WorkCategoryRetrieveAPIView(ModifiedApiview):
    def get(self, request, id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            work_category = WorkCategory.objects.filter(id=id, is_active=True).first()
            if not work_category:
                return Response({"error": "Work category not found"}, status=status.HTTP_404_NOT_FOUND)
            data = {
                "id": work_category.id,
                "name": work_category.name,
                "fees": work_category.fees,
                "department": work_category.department.name,
                "files_required": list(work_category.files_required.values("file_name", "id")),
                "activities": list(work_category.activity_list.values("activity_name", "assigned_percentage", "id")),
                "activity_stages": list(work_category.activity_stage.values("activity_stage", "description", "id")),
                "output_files": list(work_category.upload_document.values("file_name", "id")),
            }
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WorkCategoryDeactivateAPIView(ModifiedApiview):
    def delete(self, request, id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
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
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            data = request.data
            work_category = data.get("work_category")
            file_name = data.get("file_name")
            display_order = data.get("display_order")

            if not work_category or not file_name:
                return Response(
                    {"error": "Work Category and File Name are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            file_required = WorkCategoryFilesRequired.objects.create(
                work_category_id=work_category,
                file_name=file_name,
                display_order=display_order,
                created_by=user,
            )
            return Response(
                {"message": "File required created", "file_name": file_required.file_name},
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WorkCategoryFilesRequiredGetAPIView(ModifiedApiview):
    def get(self, request):
        try:
            id = request.GET.get("id", None)
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            if id:
                work_category_files = WorkCategoryFilesRequired.objects.filter(id=id, is_active=True).first()
                if not work_category_files:
                    return Response({"error": "Work category not found"}, status=status.HTTP_404_NOT_FOUND)
                data = {
                    "id": work_category_files.id,
                    "file_name": work_category_files.file_name,
                    "work_category": work_category_files.work_category.name,
                }
                return Response(data, status=status.HTTP_200_OK)
            work_categories = WorkCategoryFilesRequired.objects.filter(is_active=True).order_by(
                'display_order'
            ).values("id", "file_name", "work_category")
            return Response(list(work_categories), status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WorkCategoryFilesRequiredUpdateAPIView(ModifiedApiview):
    def put(self, request, id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            work_category_file = WorkCategoryFilesRequired.objects.filter(id=id, is_active=True).first()
            if not work_category_file:
                return Response({"error": "Work category file not found"}, status=status.HTTP_404_NOT_FOUND)

            data = request.data
            work_category_file.file_name = data.get("file_name", work_category_file.file_name)
            work_category_file.display_order = data.get("display_order", work_category_file.display_order)
            work_category_file.updated_by = user
            work_category_file.save()

            return Response({"message": "Work category updated"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WorkCategoryFilesRequiredDeactivateAPIView(ModifiedApiview):
    def delete(self, request, id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
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
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            data = request.data
            work_category = data.get("work_category")
            activity_name = data.get("activity_name")
            assigned_percentage = data.get("assigned_percentage", 0)
            display_order = data.get("display_order")
            created_by = data.get("created_by")

            if not work_category or not activity_name:
                return Response(
                    {"error": "Work Category and Activity Name are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            activity_list = WorkCategoryActivityList.objects.create(
                work_category_id=work_category,
                activity_name=activity_name,
                display_order=display_order,
                assigned_percentage=assigned_percentage,
                created_by_id=created_by,
            )
            return Response(
                {"message": "Activity list created", "id": activity_list.id},
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WorkCategoryActivityListGetAPIView(ModifiedApiview):
    def get(self, request):
        try:
            id = request.GET.get("id", None)
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            if id:
                work_category = WorkCategoryActivityList.objects.filter(id=id, is_active=True).first()
                if not work_category:
                    return Response({"error": "Work category not found"}, status=status.HTTP_404_NOT_FOUND)
                data = {
                    "id": work_category.id,
                    "activity_name": work_category.activity_name,
                    "assigned_percentage": work_category.assigned_percentage,
                    "work_category": work_category.work_category.name,
                }
                return Response(data, status=status.HTTP_200_OK)
            work_categories = WorkCategoryActivityList.objects.filter(is_active=True).order_by('display_order'
                            ).values("id", "activity_name", 
                    "assigned_percentage", "work_category")
            return Response(list(work_categories), status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WorkCategoryActivityListUpdateAPIView(ModifiedApiview):
    def put(self, request, id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            work_category = WorkCategoryActivityList.objects.filter(id=id, is_active=True).first()
            if not work_category:
                return Response({"error": "Work category not found"}, status=status.HTTP_404_NOT_FOUND)

            data = request.data
            work_category.activity_name = data.get("activity_name", work_category.activity_name)
            work_category.assigned_percentage = data.get("assigned_percentage", work_category.assigned_percentage)
            work_category.display_order = data.get("display_order", work_category.display_order)
            work_category.updated_by = user
            work_category.save()

            return Response({"message": "Work category updated"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WorkCategoryActivityListDeactivateAPIView(ModifiedApiview):
    def delete(self, request, id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            work_category = WorkCategoryActivityList.objects.filter(id=id, is_active=True).first()
            if not work_category:
                return Response({"error": "Work category not found"}, status=status.HTTP_404_NOT_FOUND)
            work_category.is_active = False
            work_category.updated_by = user
            work_category.save()
            return Response({"message": "Work category deactivated"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WorkCategoryActivityStagesCreateAPIView(ModifiedApiview):
    def post(self, request):
        try:
            data = request.data
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            work_category = data.get("work_category")
            activity_stage = data.get("activity_stage")
            display_order = data.get("display_order")
            description = data.get("description")

            if not work_category or not activity_stage:
                return Response(
                    {"error": "Work Category and Activity Stage are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            activity_stages = WorkCategoryActivityStages.objects.create(
                work_category_id=work_category,
                activity_stage=activity_stage,
                description=description,
                display_order=display_order,
                created_by=user,
            )
            return Response(
                {"message": "Activity stage created", "id": activity_stages.id},
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WorkCategoryActivityStagesGetAPIView(ModifiedApiview):
    def get(self, request):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            id = request.GET.get("id", None)
            if id:
                work_category = WorkCategoryActivityStages.objects.filter(id=id, is_active=True).first()
                if not work_category:
                    return Response({"error": "Work category not found"}, status=status.HTTP_404_NOT_FOUND)
                data = {
                    "id": work_category.id,
                    "activity_stage": work_category.activity_stage,
                    "description": work_category.description,
                    "work_category": work_category.work_category.name,
                }
                return Response(data, status=status.HTTP_200_OK)
            work_categories = WorkCategoryActivityStages.objects.filter(is_active=True).order_by('display_order').values("id", "activity_stage", 
                    "description", "work_category")
            return Response(list(work_categories), status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class WorkCategoryActivityStagesUpdateAPIView(ModifiedApiview):
    def put(self, request, id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            work_category = WorkCategoryActivityStages.objects.filter(id=id, is_active=True).first()
            if not work_category:
                return Response({"error": "Work category not found"}, status=status.HTTP_404_NOT_FOUND)

            data = request.data
            work_category.activity_stage = data.get("activity_stage", work_category.activity_stage)
            work_category.description = data.get("description", work_category.description)
            work_category.display_order = data.get("display_order", work_category.display_order)
            work_category.updated_by = user
            work_category.save()

            return Response({"message": "Work category updated"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WorkCategoryActivityStagesDeactivateAPIView(ModifiedApiview):
    def delete(self, request, id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            work_category = WorkCategoryActivityStages.objects.filter(id=id, is_active=True).first()
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
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            data = request.data
            work_category = data.get("work_category")
            file_name = data.get("file_name")
            display_order = data.get("display_order")

            if not work_category or not file_name:
                return Response(
                    {"error": "Work Category and File Name are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            upload_document = WorkCategoryUploadDocumentRequired.objects.create(
                work_category_id=work_category,
                file_name=file_name,
                display_order=display_order,
                created_by=user,
            )
            return Response(
                {"message": "Upload document required created", "id": upload_document.id},
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WorkCategoryUploadDocumentRequiredGetAPIView(ModifiedApiview):
    def get(self, request):
        try:
            id = request.GET.get("id")
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            if id:
                work_category = WorkCategoryUploadDocumentRequired.objects.filter(id=id, is_active=True).first()
                if not work_category:
                    return Response({"error": "Work category not found"}, status=status.HTTP_404_NOT_FOUND)
                data = {
                    "id": work_category.id,
                    "file_name": work_category.file_name,
                    "work_category": work_category.work_category.name,
                }
                return Response(data, status=status.HTTP_200_OK)
            work_categories = WorkCategoryUploadDocumentRequired.objects.filter(is_active=True).order_by('display_order'
                        ).values("id", "file_name", 
                     "work_category")
            return Response(list(work_categories), status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WorkCategoryUploadDocumentRequiredUpdateAPIView(ModifiedApiview):
    def put(self, request, id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            work_category = WorkCategoryUploadDocumentRequired.objects.filter(id=id, is_active=True).first()
            if not work_category:
                return Response({"error": "Work category required file not found"}, status=status.HTTP_404_NOT_FOUND)

            data = request.data
            work_category.file_name = data.get("file_name", work_category.file_name)
            work_category.updated_by = user
            work_category.save()

            return Response({"message": "Work category required file updated"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WorkCategoryUploadDocumentRequiredDeactivateAPIView(ModifiedApiview):
    def delete(self, request, id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            work_category = WorkCategoryUploadDocumentRequired.objects.filter(id=id, is_active=True).first()
            if not work_category:
                return Response({"error": "Work category required file not found"}, status=status.HTTP_404_NOT_FOUND)
            work_category.is_active = False
            work_category.updated_by = user
            work_category.save()
            return Response({"message": "Work category required file deactivated"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def assign_activities_and_files(assignment, work_category):
    try:
        required_files = WorkCategoryFilesRequired.objects.filter(work_category=work_category)
        for file in required_files:
            assigned_file = AssignedWorkRequiredFiles.objects.create(
                assignment=assignment,
                file_name=file.file_name,
                is_active=True
            )
            assigned_file.save()

        # Copy activity list
        activities = WorkCategoryActivityList.objects.filter(work_category=work_category)
        for activity in activities:
            assigned_task = AssignedWorkActivity.objects.create(
                assignment=assignment,
                activity=activity.activity_name,
                assigned_percentage=activity.assigned_percentage,
                is_active=True
            )
            assigned_task.save()

        # Copy output document requirements
        output_files = WorkCategoryUploadDocumentRequired.objects.filter(work_category=work_category)
        for file in output_files:
            assigned_file = AssignedWorkOutputFiles.objects.create(
                assignment=assignment,
                file_name=file.file_name,
                is_active=True
            )
            assigned_file.save()
        return True    
    except Exception as e:
        return False


class ClientWorkCategoryAssignmentCreateView(ModifiedApiview):
    def post(self, request):
        data = request.data
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            customer_id = data.get("customer_id")
            work_category_id = data.get("work_category_id")
            assigned_to_id = data.get("assigned_to_id", "")
            is_repetitive = data.get("is_repetitive", False)
            
            if isinstance(is_repetitive, str):
                is_repetitive = is_repetitive.lower() == 'true'


            if assigned_to_id:
                assigned_to = CustomUser.objects.get(id=assigned_to_id)
                assigned_by = CustomUser.objects.get(id=data.get("assigned_by_id"))
                review_by = CustomUser.objects.get(id=data.get("review_by_id"))
            else:
                assigned_to = None
                assigned_by = None
                review_by = None

            if not all([customer_id, work_category_id]):
                return Response(
                    {"error": "customer_id and work_category_id are required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Fetch related objects
            customer = Customer.objects.get(id=customer_id)
            work_category = WorkCategory.objects.get(id=work_category_id)

            with transaction.atomic():
                assignment = ClientWorkCategoryAssignment.objects.create(
                    customer=customer,
                    work_category=work_category,
                    assigned_to=assigned_to,
                    assigned_by=assigned_by,
                    review_by=review_by,
                    allocated_hours=data.get("allocated_hours", 0),
                    task_name=data.get("task_name", ""),
                    progress=data.get("status", "pending_from_client_side"),
                    priority=data.get("priority", 1),
                    start_date=data.get("start_date"),
                    instructions=data.get("instructions", ""),
                    completion_date=data.get("completion_date"),
                    is_repetitive=is_repetitive,
                    created_date=datetime.now(),
                    created_by=request.user,
                    updated_by=request.user
                )
                required_files = WorkCategoryFilesRequired.objects.filter(work_category=work_category)
                for file in required_files:
                    assigned_file = AssignedWorkRequiredFiles.objects.create(
                        assignment=assignment,
                        file_name=file.file_name,
                        display_order=file.display_order,
                        is_active=True
                    )

                # Copy activity list
                activities = WorkCategoryActivityList.objects.filter(work_category=work_category)
                for activity in activities:
                    assigned_task = AssignedWorkActivity.objects.create(
                        assignment=assignment,
                        activity=activity.activity_name,
                        assigned_percentage=activity.assigned_percentage,
                        display_order=activity.display_order,
                        is_active=True
                    )

                # copy activity stages
                activity_stages = WorkCategoryActivityStages.objects.filter(work_category=work_category)
                for stage in activity_stages:
                    assigned_stage = AssignedWorkActivityStages.objects.create(
                        assignment=assignment,
                        activity_stage=stage.activity_stage,
                        display_order=stage.display_order,
                        is_active=True
                    )

                # Copy output document requirements
                output_files = WorkCategoryUploadDocumentRequired.objects.filter(work_category=work_category)
                for file in output_files:
                    assigned_file = AssignedWorkOutputFiles.objects.create(
                        assignment=assignment,
                        file_name=file.file_name,
                        display_order=file.display_order,
                        is_active=True
                    )

            return Response({"message": "Assignment created successfully", "id": assignment.assignment_id}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class BulkClientWorkCategoryAssignmentCreateView(ModifiedApiview):
    def post(self, request):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)

            department_id = request.data.get("department_id")
            work_category_id = request.data.get("work_category_id")
            excel_file = request.FILES.get("excel_file")

            if not all([department_id, work_category_id, excel_file]):
                return Response(
                    {"error": "department_id, work_category_id, and excel_file are required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Save the uploaded file temporarily
            file_name = default_storage.save(excel_file.name, ContentFile(excel_file.read()))
            file_path = default_storage.path(file_name)

            # Read the Excel file
            df = pd.read_excel(file_path)

            # Fetch related objects
            work_category = WorkCategory.objects.get(id=work_category_id)

            with transaction.atomic():
                for index, row in df.iterrows():
                    customer_id = row.get("customer_id")
                    assigned_to_id = row.get("assigned_to_id", "")
                    assigned_by_id = row.get("assigned_by_id", "")
                    review_by_id = row.get("review_by_id", "")
                    is_repetitive = row.get("is_repetitive", False)

                    if assigned_to_id:
                        assigned_to = CustomUser.objects.get(id=assigned_to_id)
                        assigned_by = CustomUser.objects.get(id=assigned_by_id)
                        review_by = CustomUser.objects.get(id=review_by_id)
                    else:
                        assigned_to = None
                        assigned_by = None
                        review_by = None

                    if isinstance(is_repetitive,str):
                        is_repetitive = is_repetitive.lower() == 'true'
                        
                    assigned_by = user

                    customer = Customer.objects.get(id=customer_id)

                    assignment = ClientWorkCategoryAssignment.objects.create(
                        customer=customer,
                        work_category=work_category,
                        assigned_to=assigned_to,
                        assigned_by=assigned_by,
                        review_by=review_by,
                        task_name=row.get("task_name", ""),
                        progress=row.get("status", "pending_from_client_side"),
                        priority=row.get("priority", 1),
                        start_date=row.get("start_date"),
                        instructions=row.get("instructions", ""),
                        completion_date=row.get("completion_date"),
                        is_repetitive=is_repetitive,
                        created_date=datetime.now(),
                        created_by=user,
                        updated_by=user
                    )

                    # Copy required files
                    required_files = WorkCategoryFilesRequired.objects.filter(work_category=work_category)
                    for file in required_files:
                        AssignedWorkRequiredFiles.objects.create(
                            assignment=assignment,
                            file_name=file.file_name,
                            display_order=file.display_order,
                            is_active=True
                        )

                    # Copy activity list
                    activities = WorkCategoryActivityList.objects.filter(work_category=work_category)
                    for activity in activities:
                        AssignedWorkActivity.objects.create(
                            assignment=assignment,
                            activity=activity.activity_name,
                            assigned_percentage=activity.assigned_percentage,
                            display_order=activity.display_order,
                            is_active=True
                        )

                    # Copy activity stages
                    activity_stages = WorkCategoryActivityStages.objects.filter(work_category=work_category)
                    for stage in activity_stages:
                        AssignedWorkActivityStages.objects.create(
                            assignment=assignment,
                            activity_stage=stage.activity_stage,
                            display_order=stage.display_order,
                            is_active=True
                        )

                    # Copy output document requirements
                    output_files = WorkCategoryUploadDocumentRequired.objects.filter(work_category=work_category)
                    for file in output_files:
                        AssignedWorkOutputFiles.objects.create(
                            assignment=assignment,
                            file_name=file.file_name,
                            display_order=file.display_order,
                            is_active=True
                        )

            # Delete the temporary file
            default_storage.delete(file_name)

            return Response({"message": "Bulk assignments created successfully"}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ClientWorkCategoryAssignmentListView(ModifiedApiview):
    def get(self, request):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            assignments = ClientWorkCategoryAssignment.objects.filter(is_active=True)
            data = []
            for assignment in assignments:
                data.append({
                    "id": assignment.assignment_id,
                    "task_name": assignment.task_name,
                    "customer_id": assignment.customer.id,
                    "customer": assignment.customer.name_of_business,
                    "work_category": assignment.work_category.name,
                    "work_category_id": assignment.work_category.id,
                    "department_name": assignment.work_category.department.name,
                    "allocated_hours": assignment.allocated_hours,
                    "department_id": assignment.work_category.department.id,
                    "assigned_to": assignment.assigned_to.username if assignment.assigned_to else "",
                    "assigned_by": assignment.assigned_by.username if assignment.assigned_by else "",
                    "review_by": assignment.review_by.username if assignment.review_by else "",
                    "progress": assignment.progress,
                    "progress_display": assignment.get_progress_display(),
                    "priority": assignment.priority,
                    "priority_display": assignment.get_priority_display(),
                    "start_date": assignment.start_date,
                    "completion_date": assignment.completion_date,
                })
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ClientWorkCategoryAssignmentFilteredListView(ModifiedApiview):
    def get(self, request):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            client_id = request.GET.get("client_id", None)
            assignments = ClientWorkCategoryAssignment.objects.filter(is_active=True)
            if client_id:
                assignments = assignments.filter(customer__id=client_id)
            data = []
            for assignment in assignments:
                data.append({
                    "id": assignment.assignment_id,
                    "task_name": assignment.task_name,
                    "customer": assignment.customer.name_of_business,
                    "work_category": assignment.work_category.name,
                    "work_category_id":assignment.work_category.id,
                    "department_name": assignment.work_category.department.name,
                    "department_id": assignment.work_category.department.id,
                    "allocated_hours": assignment.allocated_hours,
                    "assigned_to": assignment.assigned_to.username if assignment.assigned_to else "",
                    "assigned_by": assignment.assigned_by.username if assignment.assigned_by else "",
                    "review_by": assignment.review_by.username if assignment.review_by else "",
                    "progress": assignment.progress,
                    "progress_display": assignment.get_progress_display(),
                    "priority": assignment.priority,
                    "priority_display": assignment.get_priority_display(),
                    "start_date": assignment.start_date,
                    "completion_date": assignment.completion_date,
                })
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ClientWorkCategoryAssignmentRetrieveView(ModifiedApiview):
    def get(self, request, assignment_id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            assignment = ClientWorkCategoryAssignment.objects.get(assignment_id=assignment_id, is_active=True)
            data = {
                "id": assignment.assignment_id,
                "task_name": assignment.task_name,
                "customer": assignment.customer.name_of_business,
                "customer_id": assignment.customer.id,
                "work_category": assignment.work_category.name,
                "work_category_id":assignment.work_category.id,
                "department_name": assignment.work_category.department.name,
                "department_id": assignment.work_category.department.id,
                "progress": assignment.progress,
                "progress_display": assignment.get_progress_display(),
                "priority": assignment.priority,
                "priority_display": assignment.get_priority_display(),
                "instructions": assignment.instructions,
                "is_repetitive": assignment.is_repetitive,
                "allocated_hours": assignment.allocated_hours,
                "assigned_to": assignment.assigned_to.username if assignment.assigned_to else "",
                "assigned_to_id": assignment.assigned_to.id if assignment.assigned_to else "",
                "assigned_by": assignment.assigned_by.username if assignment.assigned_by else "",
                "assigned_by_id": assignment.assigned_by.id if assignment.assigned_by else "",
                "review_by": assignment.review_by.username if assignment.review_by else "",
                "review_by_id": assignment.review_by.id if assignment.review_by else "",
                "start_date": assignment.start_date,
                "completion_date": assignment.completion_date,
                "required_files": list(assignment.required_files.values("file_name", "file_path", "id")),
                "activities": list(assignment.activities.values("activity", "assigned_percentage", "status", "id")),
                "activity_stage": list(assignment.activity_stages.values("activity_stage", "status", "id")),
                "output_files": list(assignment.output_files.values("file_name", "file_path", "id")),
            }
            return Response(data, status=status.HTTP_200_OK)
        except ClientWorkCategoryAssignment.DoesNotExist:
            return Response({"error": "Assignment not found"}, status=status.HTTP_404_NOT_FOUND)


class ClientWorkCategoryAssignmentUpdateView(ModifiedApiview):
    def put(self, request, assignment_id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            assignment = ClientWorkCategoryAssignment.objects.get(assignment_id=assignment_id, is_active=True)
            data = request.data
            assigned_to = CustomUser.objects.get(id=data.get("assigned_to_id",""))
            if assigned_to:
                assigned_by = CustomUser.objects.get(id=data.get("assigned_by_id", ""))
                review_by = CustomUser.objects.get(id=data.get("review_by_id", ""))
            else:
                assigned_to = assignment.assigned_to
                assigned_by = assignment.assigned_by
                review_by = assignment.review_by
            assignment.assigned_to = assigned_to
            assignment.review_by = review_by
            assignment.assigned_by = assigned_by
            assignment.task_name = data.get("task_name", assignment.task_name)
            assignment.progress = data.get("progress", assignment.progress)
            assignment.priority = data.get("priority", assignment.priority)
            assignment.instructions = data.get("instructions", assignment.instructions)
            assignment.allocated_hours = data.get("allocated_hours", assignment.allocated_hours)
            assignment.is_repetitive = data.get("is_repetitive", assignment.is_repetitive)
            assignment.start_date = data.get("start_date", assignment.start_date)
            assignment.completion_date = data.get("completion_date", assignment.completion_date)
            assignment.updated_by = request.user
            assignment.save()
            return Response({"message": "Assignment updated successfully"}, status=status.HTTP_200_OK)
        except ClientWorkCategoryAssignment.DoesNotExist:
            return Response({"error": "Assignment not found"}, status=status.HTTP_404_NOT_FOUND)


class ClientWorkCategoryAssignmentDeleteView(ModifiedApiview):
    def delete(self, request, assignment_id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            assignment = ClientWorkCategoryAssignment.objects.get(assignment_id=assignment_id, is_active=True)
            assignment.is_active = False
            assignment.updated_by = request.user
            assignment.save()
            return Response({"message": "Assignment deleted successfully"}, status=status.HTTP_200_OK)
        except ClientWorkCategoryAssignment.DoesNotExist:
            return Response({"error": "Assignment not found"}, status=status.HTTP_404_NOT_FOUND)


class SubmitClientWorkRequiredFiles(ModifiedApiview):
    def put(self, request, assignment_id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            assignment = ClientWorkCategoryAssignment.objects.get(assignment_id=assignment_id, is_active=True)
            data = request.data
            for file_data in data.get("required_files", []):
                assigned_file = AssignedWorkRequiredFiles.objects.get(id=file_data.get("id"), is_active=True)
                attachment_file = file_data.get("file")
                if attachment_file:
                    ext = os.path.splitext(attachment_file)[1]
                    short_unique_filename = f"{uuid.uuid4().hex}{ext}"
                    fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'requiredfiles'))
                    logo_path = fs.save(short_unique_filename, attachment_file)
                    attachments_url = posixpath.join('media/invoice_attachments', logo_path)
                else:
                    attachments_url = None
                assigned_file.file_path = attachments_url
                assigned_file.save()

            return Response({"message": "Assignment updated successfully"}, status=status.HTTP_200_OK)
        except ClientWorkCategoryAssignment.DoesNotExist:
            return Response({"error": "Assignment not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error":f"{e}"}, status=status.HTTP_400_BAD_REQUEST)


class SubmitClientWorkActivityList(ModifiedApiview):
    def put(self, request, assignment_id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            assignment = ClientWorkCategoryAssignment.objects.get(assignment_id=assignment_id, is_active=True)
            data = request.data
            for file_data in data.get("required_files", []):
                assigned_file = AssignedWorkActivity.objects.get(id=file_data.get("id"), is_active=True)
                assigned_file.status = file_data.get("status")
                assigned_file.note = file_data.get("note")
                assigned_file.save()

            return Response({"message": "Assignment updated successfully"}, status=status.HTTP_200_OK)
        except ClientWorkCategoryAssignment.DoesNotExist:
            return Response({"error": "Assignment not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error":f"{e}"}, status=status.HTTP_400_BAD_REQUEST)


class SubmitClientWorkActivityStage(ModifiedApiview):
    def put(self, request, assignment_id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            assignment = ClientWorkCategoryAssignment.objects.get(assignment_id=assignment_id, is_active=True)
            data = request.data
            for file_data in data.get("required_files", []):
                assigned_file = AssignedWorkActivityStages.objects.get(id=file_data.get("id"), is_active=True)
                assigned_file.status = file_data.get("status")
                assigned_file.note = file_data.get("note")
                assigned_file.save()

            return Response({"message": "Assignment updated successfully"}, status=status.HTTP_200_OK)
        except ClientWorkCategoryAssignment.DoesNotExist:
            return Response({"error": "Assignment not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error":f"{e}"}, status=status.HTTP_400_BAD_REQUEST)


class SubmitClientWorkOutputFiles(ModifiedApiview):
    def put(self, request, assignment_id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)

            assignment = ClientWorkCategoryAssignment.objects.get(assignment_id=assignment_id, is_active=True)
            data = request.data
            required_files = data.get("required_files", [])
            if not required_files:
                return Response({"error": "No files provided"}, status=status.HTTP_400_BAD_REQUEST)
            for file_data in required_files:
                assigned_file = AssignedWorkOutputFiles.objects.get(id=file_data.get("id"), is_active=True)
                attachment_file = file_data.get("file")

                if attachment_file:
                    assigned_file.file_path = upload_to_cloudinary(attachment_file)
                else:
                    assigned_file.file_path = None

                assigned_file.save()

            return Response({"message": "Assignment updated successfully"}, status=status.HTTP_200_OK)

        except ClientWorkCategoryAssignment.DoesNotExist:
            return Response({"error": "Assignment not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"{e}"}, status=status.HTTP_400_BAD_REQUEST)


class SubmitClientWorkAdditionalActivity(ModifiedApiview):
    def put(self, request, assignment_id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            assignment = ClientWorkCategoryAssignment.objects.get(assignment_id=assignment_id, is_active=True)
            data = request.data
            for file_data in data.get("required_files", []):
                assigned_file = AssignedWorkActivity.objects.create(activity=file_data.get("activity"),
                                        assignment=assignment, 
                                        status=file_data.get("status"),
                                        note=file_data.get("note"),
                                        is_active=True)

            return Response({"message": "Assignment updated successfully", "id":assigned_file.id}, status=status.HTTP_200_OK)
        except ClientWorkCategoryAssignment.DoesNotExist:
            return Response({"error": "Assignment not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error":f"{e}"}, status=status.HTTP_400_BAD_REQUEST)


class SubmitClientWorkAdditionalFiles(ModifiedApiview):
    def put(self, request, assignment_id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            assignment = ClientWorkCategoryAssignment.objects.get(assignment_id=assignment_id, is_active=True)
            data = request.data
            for file_data in data.get("required_files", []):
                attachment_file = file_data.get("file")
                if attachment_file:
                    ext = os.path.splitext(attachment_file)[1]
                    short_unique_filename = f"{uuid.uuid4().hex}{ext}"
                    fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'requiredfiles'))
                    logo_path = fs.save(short_unique_filename, attachment_file)
                    attachments_url = posixpath.join('media/invoice_attachments', logo_path)
                else:
                    attachments_url = None
                assigned_file = AssignedWorkOutputFiles.objects.create(file_name=file_data.get("file_name"),
                    assignment=assignment,
                    file_path=attachments_url,
                    is_active=True)

            return Response({"message": "Assignment updated successfully", "id":assigned_file.id}, status=status.HTTP_200_OK)
        except ClientWorkCategoryAssignment.DoesNotExist:
            return Response({"error": "Assignment not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error":f"{e}"}, status=status.HTTP_400_BAD_REQUEST)


class SendFilesToClientAPIView(ModifiedApiview):
    def post(self, request):
        try:
            # Extract data from the request
            email_subject = request.data.get('email_subject')
            email_body = request.data.get('email_body')
            to_email = request.data.get('to_email')
            file_ids = request.data.get('file_ids', [])  # List of file IDs

            # Validate required fields
            if not all([email_subject, email_body, to_email, file_ids]):
                return Response(
                    {"error": "Missing required fields: email_subject, email_body, to_email, file_ids."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            to_email = str(to_email)
            to_email = to_email.split(",")
            
            # Retrieve files
            files = AssignedWorkOutputFiles.objects.filter(id__in=file_ids, is_active=True)

            if not files.exists():
                return Response(
                    {"error": "No valid files found for the given IDs."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Get Cloudinary file URLs
            attachments = []
            for file in files:
                if file.file_path:
                    try:
                        cloudinary_url = get_cloudinary_file(file.file_path)
                        attachments.append(cloudinary_url)
                    except Exception as e:
                        print(f"Error fetching Cloudinary file: {e}")

            # Send email with attachments
            email_sent = send_email(
                subject=email_subject,
                body=email_body,
                to_emails=to_email,
                attachment=attachments
            )

            if email_sent:
                return Response({"message": "Email sent successfully."}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Failed to send email."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SendActivityReportPDFAPIView(ModifiedApiview):
    def post(self, request, assignment_id):
        try:
            # Get user
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            attachments = request.FILES.get("task_update")
            if not attachments:
                Response({"message":"Error while fetching file"}, status=status.HTTP_400_BAD_REQUEST)
            extension = os.path.splitext(attachments.name)[1]
            if extension != ".pdf":
                Response({"message":"Unsupported file format"}, status=status.HTTP_400_BAD_REQUEST)
            email_body = request.data.get("email_body")
            email_subject = request.data.get("email_subject")
            to_email = request.data.get("to_email")
            if isinstance(to_email, str):
                to_email = to_email.split(",")
            else:
                to_email = to_email
            email = send_email(subject=email_subject,
                               body=email_body,
                               to_emails=to_email,
                               attachment=attachments
                               )
            if email:
                return Response({"message":"Email sent successfully"}, status=status.HTTP_200_OK)
            else:
                return Response({"message":"Error while sending email"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"{e}"}, status=status.HTTP_400_BAD_REQUEST)


class SendActivityReportAPIView(ModifiedApiview):
    def put(self, request, assignment_id):
        try:
            # Get user
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)

            to_email = request.data.get("to_email")
            to_email = str(to_email)
            to_email = to_email.split(",")
            # Fetch assignment
            assignment = ClientWorkCategoryAssignment.objects.get(assignment_id=assignment_id, is_active=True)

            # Get activities
            completed_activities = AssignedWorkActivity.objects.filter(assignment=assignment, status="completed", is_active=True)
            incomplete_activities = AssignedWorkActivity.objects.filter(assignment=assignment).exclude(status="completed").filter(is_active=True)

            # Prepare email content
            email_subject = f"Activity Report - {assignment.task_name} - {assignment.customer.name_of_business}"
            email_body = f"Activity Report for {assignment.customer.name_of_business}\n\n"

            email_body += "**Completed Activities:**\n"
            for activity in completed_activities:
                email_body += f"- {activity.activity} (Completed on: {activity.completion_date})\n"

            email_body += "\n**Incomplete Activities:**\n"
            for activity in incomplete_activities:
                email_body += f"- {activity.activity} (Status: {activity.status}, Note: {activity.note})\n"

            # Send email
            email_sent = send_email(
                subject=email_subject,
                body=email_body,
                to_emails=to_email
            )

            if email_sent:
                return Response({"message": "Report sent successfully."}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Failed to send email."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except ClientWorkCategoryAssignment.DoesNotExist:
            return Response({"error": "Assignment not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"{e}"}, status=status.HTTP_400_BAD_REQUEST)


# class SendInvoiceAPIView(ModifiedApiview):
#     def put(self, request, assignment_id):
#         try:
#             # Get user
#             user = self.get_user_from_token(request)
#             if not user:
#                 return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
#             attachments = request.FILES.get("invoice_pdf")
#             if not attachments:
#                 Response({"message":"Error while fetching file"}, status=status.HTTP_400_BAD_REQUEST)
#             extension = os.path.splitext(attachments.name)[1]
#             if extension != "pdf":
#                 Response({"message":"Unsupported file format"}, status=status.HTTP_400_BAD_REQUEST)
#             email_body = request.data.get("email_body")
#             email_subject = request.data.get("email_subject")
#             to_email = request.data.get("to_email")
#             if isinstance(to_email, str):
#                 to_email = to_email.split(",")
#             else:
#                 to_email = to_email
#             print(to_email)
#             email = send_email(subject=email_subject,
#                                body=email_body,
#                                to_emails=to_email,
#                                attachment=attachments
#                                )
#             if email:
#                 return Response({"message":"Invoice Email sent successfully"}, status=status.HTTP_200_OK)
#             else:
#                 return Response({"message":"Error while sending email"}, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             return Response({"error": f"{e}"}, status=status.HTTP_400_BAD_REQUEST)


class AssignTaskView(ModifiedApiview):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            # Validate required fields
            customer_id = data.get("customer_id")
            work_category_id = data.get("work_category_id")
            assigned_to_id = data.get("assigned_to_id")
            
            assigned_by = request.user

            if not all([customer_id, work_category_id, assigned_to_id]):
                return Response(
                    {"error": "customer_id, work_category_id, and assigned_to_id are required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Fetch related objects
            customer = Customer.objects.get(id=customer_id)
            work_category = WorkCategory.objects.get(id=work_category_id)
            assigned_to = CustomUser.objects.get(id=assigned_to_id)

            # Create the assignment
            assignment = ClientWorkCategoryAssignment.objects.create(
                customer=customer,
                work_category=work_category,
                assigned_to=assigned_to,
                assigned_by=assigned_by,
                is_active=data.get("is_active", True),
            )

            return Response(
                {
                    "message": "Task assigned successfully.",
                    "assignment": {
                        "id": assignment.id,
                        "customer": assignment.customer.name_of_business,
                        "work_category": assignment.work_category.name,
                        "assigned_to": assignment.assigned_to.username,
                        "assigned_by": assignment.assigned_by.username,
                        "created_date": assignment.created_date,
                        "is_active": assignment.is_active,
                    },
                },
                status=status.HTTP_201_CREATED,
            )

        except Customer.DoesNotExist:
            return Response({"error": "Customer not found."}, status=status.HTTP_404_NOT_FOUND)
        except WorkCategory.DoesNotExist:
            return Response({"error": "Work category not found."}, status=status.HTTP_404_NOT_FOUND)
        except CustomUser.DoesNotExist:
            return Response({"error": "Assigned user not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class EditAssignedTaskView(ModifiedApiview):
    permission_classes = [IsAuthenticated]

    def put(self, request, assignment_id):
        data = request.data
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            assignment = ClientWorkCategoryAssignment.objects.get(assignment_id=assignment_id)

            # Update fields only if they are provided
            if "customer_id" in data:
                assignment.customer = Customer.objects.get(id=data["customer_id"])
            if "work_category_id" in data:
                assignment.work_category = WorkCategory.objects.get(id=data["work_category_id"])
            if "assigned_to_id" in data:
                assignment.assigned_to = CustomUser.objects.get(id=data["assigned_to_id"])
            if "is_active" in data:
                assignment.is_active = data["is_active"]

            assignment.updated_date = datetime.now()
            assignment.save()

            return Response(
                {
                    "message": "Assignment updated successfully.",
                    "assignment": {
                        "id": assignment.id,
                        "customer": assignment.customer.name_of_business,
                        "work_category": assignment.work_category.name,
                        "assigned_to": assignment.assigned_to.username if assignment.assigned_to else None,
                        "assigned_by": assignment.assigned_by.username if assignment.assigned_by else None,
                        "updated_date": assignment.updated_date,
                        "is_active": assignment.is_active,
                    },
                },
                status=status.HTTP_200_OK,
            )
        except ClientWorkCategoryAssignment.DoesNotExist:
            return Response({"error": "Assignment not found."}, status=status.HTTP_404_NOT_FOUND)
        except Customer.DoesNotExist:
            return Response({"error": "Customer not found."}, status=status.HTTP_404_NOT_FOUND)
        except WorkCategory.DoesNotExist:
            return Response({"error": "Work category not found."}, status=status.HTTP_404_NOT_FOUND)
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class DeleteAssignedTaskView(ModifiedApiview):
    permission_classes = [IsAuthenticated]

    def delete(self, request, assignment_id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            assignment = ClientWorkCategoryAssignment.objects.get(id=assignment_id)
            assignment.delete()
            return Response({"message": "Assignment deleted successfully."}, status=status.HTTP_200_OK)
        except ClientWorkCategoryAssignment.DoesNotExist:
            return Response({"error": "Assignment not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class RetrieveAssignedTaskView(ModifiedApiview):
    permission_classes = [IsAuthenticated]

    def get(self, request, assignment_id=None):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            if assignment_id:
                assignment = ClientWorkCategoryAssignment.objects.get(assignment_id=assignment_id)
                data = {
                    "id": assignment.id,
                    "customer": assignment.customer.name_of_business,
                    "customer_id": assignment.customer.id,
                    "work_category": assignment.work_category.name,
                    "assigned_to": assignment.assigned_to.username if assignment.assigned_to else None,
                    "assigned_by": assignment.assigned_by.username if assignment.assigned_by else None,
                    "created_date": assignment.created_date,
                    "updated_date": assignment.updated_date,
                    "is_active": assignment.is_active,
                }
            else:
                assignments = ClientWorkCategoryAssignment.objects.all()
                data = [
                    {
                        "id": a.id,
                        "customer": a.customer.name_of_business,
                        "work_category": a.work_category.name,
                        "assigned_to": a.assigned_to.username if a.assigned_to else None,
                        "assigned_by": a.assigned_by.username if a.assigned_by else None,
                        "created_date": a.created_date,
                        "updated_date": a.updated_date,
                        "is_active": a.is_active,
                    }
                    for a in assignments
                ]

            return Response(data, status=status.HTTP_200_OK)
        except ClientWorkCategoryAssignment.DoesNotExist:
            return Response({"error": "Assignment not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class RetrieveAssignedTaskByUserView(ModifiedApiview):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            user = CustomUser.objects.get(id=user_id)
            assignments = ClientWorkCategoryAssignment.objects.filter(assigned_to=user, is_active=True)
            data = [
                {
                    "id": a.id,
                    "customer": a.customer.name_of_business,
                    "work_category": a.work_category.name,
                    "assigned_to": a.assigned_to.username if a.assigned_to else None,
                    "assigned_by": a.assigned_by.username if a.assigned_by else None,
                    "created_date": a.created_date,
                    "updated_date": a.updated_date,
                    "progress": a.progress,
                    "is_active": a.is_active,
                }
                for a in assignments
            ]

            return Response(data, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    

class RetrieveAssignedTaskByReviewByView(ModifiedApiview):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            assignments = ClientWorkCategoryAssignment.objects.filter(review_by=user, is_active=True)
            data = [
                {
                    "id": a.id,
                    "customer": a.customer.name_of_business,
                    "work_category": a.work_category.name,
                    "assigned_to": a.assigned_to.username if a.assigned_to else None,
                    "assigned_by": a.assigned_by.username if a.assigned_by else None,
                    "created_date": a.created_date,
                    "updated_date": a.updated_date,
                    "progress": a.progress,
                    "is_active": a.is_active,
                }
                for a in assignments
            ]

            return Response(data, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class SubmitReviewByView(ModifiedApiview):
    permission_classes = [IsAuthenticated]

    def put(self, request, assignment_id):
        data = request.data
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            assignment = ClientWorkCategoryAssignment.objects.get(assignment_id=assignment_id)
            assignment.review_by = request.user
            assignment.review_notes = data.get("review_notes", assignment.review_notes)
            assignment.progress = data.get("progress", assignment.progress)
            assignment.priority = data.get("priority", assignment.priority)
            assignment.updated_by = request.user
            assignment.save()

            return Response(
                {
                    "message": "Assignment updated successfully.",
                    "assignment": {
                        "id": assignment.assignment_id,
                        "customer": assignment.customer.name_of_business,
                        "work_category": assignment.work_category.name,
                        "assigned_to": assignment.assigned_to.username if assignment.assigned_to else None,
                        "assigned_by": assignment.assigned_by.username if assignment.assigned_by else None,
                        "review_by": assignment.review_by.username if assignment.review_by else None,
                        "progress": assignment.progress,
                        "priority": assignment.priority,
                        "start_date": assignment.start_date,
                        "completion_date": assignment.completion_date,
                    },
                },
                status=status.HTTP_200_OK,
            )
        except ClientWorkCategoryAssignment.DoesNotExist:
            return Response({"error": "Assignment not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class WorkCategoryUploadDocumentRequiredBulkCreateAPIView(ModifiedApiview):
    def post(self, request):
        try:
            # Get the authenticated user
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)

            # Get the uploaded file and work category from the request
            uploaded_file = request.FILES.get("file")
            work_category_id = request.data.get("work_category")

            if not uploaded_file or not work_category_id:
                return Response(
                    {"error": "File and Work Category are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Validate the work category
            try:
                work_category = WorkCategory.objects.get(id=work_category_id)
            except WorkCategory.DoesNotExist:
                return Response(
                    {"error": "Invalid Work Category"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Read the XLSX file using pandas
            df = pd.read_excel(uploaded_file)

            # Validate the required columns
            if "File Name" not in df.columns:
                return Response(
                    {"error": "The XLSX file must contain a 'File Name' column"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Prepare a list to hold the records to be created
            records_to_create = []

            # Iterate through the rows in the DataFrame
            for _, row in df.iterrows():
                file_name = row.get("File Name")
                display_order = row.get("Display Order", 0)  # Default to 0 if missing

                # Validate the row data
                if not file_name:
                    continue  # Skip rows with missing file_name

                # Create a new WorkCategoryFilesRequired instance
                record = WorkCategoryFilesRequired(
                    work_category=work_category,
                    file_name=file_name,
                    display_order=display_order,
                    created_by=user,
                )
                records_to_create.append(record)
            # Bulk create the records
            WorkCategoryFilesRequired.objects.bulk_create(records_to_create)

            return Response(
                {"message": f"{len(records_to_create)} records created successfully"},
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class WorkCategoryActivityListBulkCreateAPIView(ModifiedApiview):
    def post(self, request):
        try:
            # Get the authenticated user
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)

            # Get the uploaded file and work category from the request
            uploaded_file = request.FILES.get("file")
            work_category_id = request.data.get("work_category")

            if not uploaded_file or not work_category_id:
                return Response(
                    {"error": "File and Work Category are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Validate the work category
            try:
                work_category = WorkCategory.objects.get(id=work_category_id)
            except WorkCategory.DoesNotExist:
                return Response(
                    {"error": "Invalid Work Category"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Read the XLSX file using pandas
            df = pd.read_excel(uploaded_file)

            # Validate the required columns
            if not all(col in df.columns for col in ["Activity Name", "Activity Percentage", "Display Order"]):
                return Response(
                    {"error": "The XLSX file must contain a 'Activity Name', 'Activity Percentage' and 'Display Order' column"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Prepare a list to hold the records to be created
            records_to_create = []

            # Iterate through the rows in the DataFrame
            for _, row in df.iterrows():
                activity_name = row.get("Activity Name")
                assigned_percentage = row.get("Activity Percentage")
                display_order = row.get("Display Order", 0)  # Default to 0 if missing

                # Create a new WorkCategoryFilesRequired instance
                record = WorkCategoryActivityList(
                    work_category=work_category,
                    activity_name=activity_name,
                    assigned_percentage=assigned_percentage,
                    display_order=display_order,
                    created_by=user,
                )
                records_to_create.append(record)
            # Bulk create the records
            WorkCategoryActivityList.objects.bulk_create(records_to_create)

            return Response(
                {"message": f"{len(records_to_create)} records created successfully"},
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class WorkCategoryOutputFileBulkCreateAPIView(ModifiedApiview):
    def post(self, request):
        try:
            # Get the authenticated user
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)

            # Get the uploaded file and work category from the request
            uploaded_file = request.FILES.get("file")
            work_category_id = request.data.get("work_category")

            if not uploaded_file or not work_category_id:
                return Response(
                    {"error": "File and Work Category are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Validate the work category
            try:
                work_category = WorkCategory.objects.get(id=work_category_id)
            except WorkCategory.DoesNotExist:
                return Response(
                    {"error": "Invalid Work Category"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Read the XLSX file using pandas
            df = pd.read_excel(uploaded_file)

            # Validate the required columns
            if "File Name" not in df.columns:
                return Response(
                    {"error": "The XLSX file must contain a 'File Name' and 'Display Order' column"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Prepare a list to hold the records to be created
            records_to_create = []

            # Iterate through the rows in the DataFrame
            for _, row in df.iterrows():
                file_name = row.get("File Name")
                display_order = row.get("Display Order", 0)  # Default to 0 if missing

                # Validate the row data
                if not file_name:
                    continue  # Skip rows with missing file_name

                # Create a new WorkCategoryFilesRequired instance
                record = WorkCategoryUploadDocumentRequired(
                    work_category=work_category,
                    file_name=file_name,
                    display_order=display_order,
                    created_by=user,
                )
                records_to_create.append(record)
            # Bulk create the records
            WorkCategoryUploadDocumentRequired.objects.bulk_create(records_to_create)

            return Response(
                {"message": f"{len(records_to_create)} records created successfully"},
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class ConsolidatedTaskDetailsWithExpensesAndBillingView(ModifiedApiview):
    def get(self, request):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)

            # Subquery to calculate total expenses for each task
            total_expenses_subquery = Expense.objects.filter(
                work_id=OuterRef('assignment_id')
            ).values('work_id').annotate(
                total_expenses=Sum('expense_amount')
            ).values('total_expenses')

            # Subquery to calculate total hours spent on each task
            hours_spent_subquery = TimeTracking.objects.filter(
                work_id=OuterRef('assignment_id')
            ).values('work_id').annotate(
                total_hours_spent=Sum(F('duration'))
            ).values('total_hours_spent')

            # Prefetch related billing and receipt data
            billing_prefetch = Prefetch(
                'bill_task',
                queryset=Billing.objects.annotate(
                    total_paid=Sum('paid_amount')
                )
            )

            # Fetch all tasks with consolidated details
            tasks = ClientWorkCategoryAssignment.objects.annotate(
                customer_name=F('customer__name_of_business'),
                task_title=F('task_name'),
                assigned_to_username=F('assigned_to__username'),
                total_hours_spent=Subquery(hours_spent_subquery, output_field=models.DurationField()),
                total_expenses=Subquery(total_expenses_subquery, output_field=models.FloatField())
            ).prefetch_related(
                billing_prefetch,
                Prefetch('task_expense', queryset=Expense.objects.all())
            ).values(
                'assignment_id',
                'customer_name',
                'task_title',
                'start_date',
                'completion_date',
                'assigned_to_username',
                'allocated_hours',
                'total_hours_spent',
                'total_expenses',
                'progress',
                'priority'
            )

            # Convert duration to hours and add billing and expense details
            consolidated_data = []
            for task in tasks:
                task_data = dict(task)
                task_data['total_hours_spent'] = task_data['total_hours_spent'].total_seconds() / 3600 if task_data['total_hours_spent'] else 0
                task_data['total_expenses'] = task_data['total_expenses'] or 0

                # Fetch billing details for the task
                # billing_details = []
                # for bill in ClientWorkCategoryAssignment.objects.get(assignment_id=task['assignment_id']).bill_task.all():
                #     billing_details.append({
                #         'bill_id': bill.id,
                #         'invoice_date': bill.invoice_date,
                #         'total_amount': bill.total,
                #         'paid_amount': bill.paid_amount,
                #         'unpaid_amount': bill.unpaid_amount,
                #         'payment_status': bill.payment_status,
                #         'invoice_status': 'Paid' if bill.payment_status == 'paid' else 'Unpaid'
                #     })

                # task_data['billing_details'] = billing_details
                consolidated_data.append(task_data)

            return Response(consolidated_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class ScheduleTaskTimeCreateView(ModifiedApiview):
    def post(self, request):
        data = request.data
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            
            # Required fields
            customer_id = data.get("customer_id")
            task_id = data.get("task_id")
            start_time = data.get("start_time")
            end_time = data.get("end_time")
            activities = data.get("activities",None)
            instructions = data.get("activities",None)
            
            if not all([customer_id, task_id, start_time, end_time]):
                return Response(
                    {"error": "customer_id, start_time and end_time are required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Fetch related objects
            customer = Customer.objects.get(id=customer_id)
            task = None
            if task_id:
                task = ClientWorkCategoryAssignment.objects.get(assignment_id=task_id)
            assigned_to = CustomUser.objects.get(id=data.get("assigned_to_id")) if data.get("assigned_to_id") else None

            with transaction.atomic():
                schedule = ScheduleTaskTime.objects.create(
                    customer=customer,
                    task=task,
                    assigned_to=assigned_to,
                    start_time=start_time,
                    end_time=end_time,
                    activities=activities,
                    instructions=instructions,
                    mode_of_communication=data.get("mode_of_communication", ""),
                    created_by=user,
                    updated_by=user
                )

            return Response(
                {"message": "Schedule created successfully", "id": schedule.id}, 
                status=status.HTTP_201_CREATED
            )
        except Customer.DoesNotExist:
            return Response({"error": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)
        except ClientWorkCategoryAssignment.DoesNotExist:
            return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)
        except CustomUser.DoesNotExist:
            return Response({"error": "Assigned user not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ScheduleTaskTimeListView(ModifiedApiview):
    def get(self, request):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            
            # You can add filters here based on request parameters
            schedules = ScheduleTaskTime.objects.all().order_by('-created_date')
            
            result = []
            for schedule in schedules:
                result.append({
                    "id": schedule.id,
                    "customer": schedule.customer.name_of_business,
                    "task": schedule.task.task_name if schedule.task else None,
                    "assigned_to": schedule.assigned_to.username if schedule.assigned_to else None,
                    "start_time": schedule.start_time,
                    "end_time": schedule.end_time,
                    "mode_of_communication": schedule.mode_of_communication,
                    "created_date": schedule.created_date,
                    "created_by": schedule.created_by.username if schedule.created_by else None
                })
            
            return Response({"schedules": result}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ScheduleTaskTimeDetailView(ModifiedApiview):
    def get(self, request, id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            
            schedule = ScheduleTaskTime.objects.get(id=id)
            
            response_data = {
                "id": schedule.id,
                "customer_id": schedule.customer.id,
                "customer_name": schedule.customer.name_of_business,
                "task_id": schedule.task.assignment_id if schedule.task else None,
                "task_name": schedule.task.task_name if schedule.task else None,
                "assigned_to_id": schedule.assigned_to.id if schedule.assigned_to else None,
                "assigned_to_name": schedule.assigned_to.username if schedule.assigned_to else None,
                "start_time": schedule.start_time,
                "activities": schedule.activities,
                "instructions": schedule.instructions,
                "end_time": schedule.end_time,
                "mode_of_communication": schedule.mode_of_communication,
                "created_date": schedule.created_date,
                "created_by": schedule.created_by.username if schedule.created_by else None,
                "updated_date": schedule.updated_date,
                "updated_by": schedule.updated_by.username if schedule.updated_by else None
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
        except ScheduleTaskTime.DoesNotExist:
            return Response({"error": "Schedule not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ScheduleTaskTimeUpdateView(ModifiedApiview):
    def put(self, request, id):
        data = request.data
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            
            schedule = ScheduleTaskTime.objects.get(id=id)
            task_details = None
            if "task_id" in data:
                task_details = ClientWorkCategoryAssignment.objects.get(assignment_id=data["task_id"])
            
            with transaction.atomic():
                schedule.customer = Customer.objects.get(id=data["customer_id"])
                schedule.task = task_details
                schedule.assigned_to = CustomUser.objects.get(id=data["assigned_to_id"]) if data["assigned_to_id"] else None
                schedule.start_time = data["start_time"]
                schedule.end_time = data["end_time"]
                schedule.mode_of_communication = data["mode_of_communication"]
                schedule.activities = data.get("activities", schedule.activities)
                schedule.instructions = data.get("instructions", schedule.instructions)
                schedule.updated_by = user
                schedule.save()
            
            return Response({"message": "Schedule updated successfully"}, status=status.HTTP_200_OK)
        except ScheduleTaskTime.DoesNotExist:
            return Response({"error": "Schedule not found"}, status=status.HTTP_404_NOT_FOUND)
        except Customer.DoesNotExist:
            return Response({"error": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)
        except ClientWorkCategoryAssignment.DoesNotExist:
            return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)
        except CustomUser.DoesNotExist:
            return Response({"error": "Assigned user not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ScheduleTaskTimeDeleteView(ModifiedApiview):
    def delete(self, request, id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            
            schedule = ScheduleTaskTime.objects.get(id=id)
            schedule.delete()
            
            return Response({"message": "Schedule deleted successfully"}, status=status.HTTP_200_OK)
        except ScheduleTaskTime.DoesNotExist:
            return Response({"error": "Schedule not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    

class ClientWorkReminderCreateView(ModifiedApiview):
    def post(self, request):
        data = request.data
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            
            # Required fields
            client_id = data.get("client_id")
            
            if not client_id:
                return Response(
                    {"error": "client_id is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Fetch related objects
            client = Customer.objects.get(id=client_id)
            task = None
            if data.get("task_id"):
                task = ClientWorkCategoryAssignment.objects.get(assignment_id=data.get("task_id"))

            with transaction.atomic():
                reminder = ClientWorkReminder.objects.create(
                    client=client,
                    task=task,
                    reminder_note=data.get("reminder_note", ""),
                    status=data.get("status", ""),
                    created_by=user,
                    updated_by=user
                )

            return Response(
                {"message": "Reminder created successfully", "id": reminder.id}, 
                status=status.HTTP_201_CREATED
            )
        except Customer.DoesNotExist:
            return Response({"error": "Client not found"}, status=status.HTTP_404_NOT_FOUND)
        except ClientWorkCategoryAssignment.DoesNotExist:
            return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
    
class ClientWorkReminderRetrieveView(ModifiedApiview):
    def get(self, request, reminder_id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            
            reminder = ClientWorkReminder.objects.get(id=reminder_id)
            data = {
                "id": reminder.id,
                "client_id": reminder.client.id,
                "client_name": reminder.client.name_of_business if reminder.client else None,
                "task_id": reminder.task.assignment_id if reminder.task else None,
                "task_name": reminder.task.task_name if reminder.task else None,
                "reminder_note": reminder.reminder_note,
                "status": reminder.status,
                "created_date": reminder.created_date,
                "created_by": reminder.created_by.id,
                "updated_date": reminder.updated_date,
                "updated_by": reminder.updated_by.id
            }
            return Response(data, status=status.HTTP_200_OK)
        except ClientWorkReminder.DoesNotExist:
            return Response({"error": "Reminder not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        

class ClientWorkReminderUpdateView(ModifiedApiview):
    def put(self, request, reminder_id):
        data = request.data
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            
            reminder = ClientWorkReminder.objects.get(id=reminder_id)
            
            with transaction.atomic():
                if data.get("client_id"):
                    reminder.client = Customer.objects.get(id=data.get("client_id"))
                if data.get("task_id"):
                    reminder.task = ClientWorkCategoryAssignment.objects.get(assignment_id=data.get("task_id"))
                if "reminder_note" in data:
                    reminder.reminder_note = data.get("reminder_note")
                if "status" in data:
                    reminder.status = data.get("status")
                
                reminder.updated_by = user
                reminder.save()

            return Response(
                {"message": "Reminder updated successfully"}, 
                status=status.HTTP_200_OK
            )
        except ClientWorkReminder.DoesNotExist:
            return Response({"error": "Reminder not found"}, status=status.HTTP_404_NOT_FOUND)
        except Customer.DoesNotExist:
            return Response({"error": "Client not found"}, status=status.HTTP_404_NOT_FOUND)
        except ClientWorkCategoryAssignment.DoesNotExist:
            return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        

class ClientWorkReminderListView(ModifiedApiview):
    def get(self, request):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            
            reminders = ClientWorkReminder.objects.all()
            data = [{
                "id": reminder.id,
                "client_id": reminder.client.id,
                "client_name": reminder.client.name_of_business if reminder.client else None,
                "task_id": reminder.task.assignment_id if reminder.task else None,
                "task_name": reminder.task.task_name if reminder.task else None,
                "reminder_note": reminder.reminder_note,
                "status": reminder.status,
                "created_date": reminder.created_date,
                "created_by": reminder.created_by.id,
                "updated_date": reminder.updated_date,
                "updated_by": reminder.updated_by.id
            } for reminder in reminders]
            
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        

class ClientWorkReminderActivityView(ModifiedApiview):
    def get(self, request, assignment_id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            
            reminders = ClientWorkReminder.objects.filter(task__assignment_id=assignment_id).exclude(status="close").all()
            data = [{
                "id": reminder.id,
                "client_id": reminder.client.id if reminder.client else None,
                "client_name": reminder.client.name_of_business if reminder.client else None,
                "task_id": reminder.task.assignment_id if reminder.task else None,
                "task_name": reminder.task.task_name if reminder.task else None,
                "reminder_note": reminder.reminder_note,
                "status": reminder.status,
                "created_date": reminder.created_date,
                "created_by": reminder.created_by.id,
                "updated_date": reminder.updated_date,
                "updated_by": reminder.updated_by.id
            } for reminder in reminders]
            
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ClientWorkReminderDeleteView(ModifiedApiview):
    def delete(self, request, reminder_id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)
            
            reminder = ClientWorkReminder.objects.get(id=reminder_id)
            reminder.delete()
            
            return Response(
                {"message": "Reminder deleted successfully"}, 
                status=status.HTTP_200_OK
            )
        except ClientWorkReminder.DoesNotExist:
            return Response({"error": "Reminder not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        

