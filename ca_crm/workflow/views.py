from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import (
    Department,
    WorkCategory,
    WorkCategoryFilesRequired,
    WorkCategoryActivityList,
    WorkCategoryActivityStages,
    WorkCategoryUploadDocumentRequired,
    ClientWorkCategoryAssignment,
    AssignedWorkRequiredFiles,
    AssignedWorkActivity,
    AssignedWorkActivityStages,
    AssignedWorkOutputFiles,
)
from datetime import datetime, time
from rest_framework.permissions import IsAuthenticated
import jwt 
from django.conf import settings
from custom_auth.models import CustomUser
from clients.models import Customer
from django.db import transaction

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

            if not name:
                return Response({"error": "Name is required"}, status=status.HTTP_400_BAD_REQUEST)

            department = Department.objects.create(
                name=name,
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
                    "name": department.name
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
            department = Department.objects.filter(id=id, is_active=True).first()
            if not department:
                return Response({"error": "Department not found"}, status=status.HTTP_404_NOT_FOUND)

            data = request.data
            department.name = data.get("name", department.name)
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
            department_id = data.get("department")
            fees = data.get("fees", 0)

            department = Department.objects.filter(id=department_id, is_active=True).first()
            if not name or not department:
                return Response(
                    {"error": "Name and Department are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            work_category = WorkCategory.objects.create(
                name=name,
                department=department,
                fees=fees,
                created_by=user,
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
            work_category = WorkCategory.objects.filter(id=id, is_active=True).first()
            if not work_category:
                return Response({"error": "Work category not found"}, status=status.HTTP_404_NOT_FOUND)

            data = request.data
            work_category.name = data.get("name", work_category.name)
            work_category.fees = data.get("fees", work_category.fees)
            work_category.save()

            return Response({"message": "Work category updated"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetDepartmentWorkCategoriesAPIView(ModifiedApiview):
    def get(self, request, id):
        try:
            user = self.get_user_from_token(request)
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

            if not work_category or not file_name:
                return Response(
                    {"error": "Work Category and File Name are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            file_required = WorkCategoryFilesRequired.objects.create(
                work_category_id=work_category,
                file_name=file_name,
                created_by=user,
            )
            return Response(
                {"message": "File required created", "file_name": file_required.file_name},
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
                    "work_category": work_category_files.work_category.name,
                }
                return Response(data, status=status.HTTP_200_OK)
            work_categories = WorkCategoryFilesRequired.objects.filter(is_active=True).values("id", "file_name", "work_category")
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
            assigned_percentage = data.get("assigned_percentage", 0)
            created_by = data.get("created_by")

            if not work_category or not activity_name:
                return Response(
                    {"error": "Work Category and Activity Name are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            activity_list = WorkCategoryActivityList.objects.create(
                work_category_id=work_category,
                activity_name=activity_name,
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
                    "assigned_percentage": work_category.assigned_percentage,
                    "work_category": work_category.work_category.name,
                }
                return Response(data, status=status.HTTP_200_OK)
            work_categories = WorkCategoryActivityList.objects.filter(is_active=True).values("id", "activity_name", 
                    "assigned_percentage", "work_category")
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
            work_category.assigned_percentage = data.get("assigned_percentage", work_category.assigned_percentage)
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


class WorkCategoryActivityStagesCreateAPIView(ModifiedApiview):
    def post(self, request):
        user = self.get_user_from_token(request)
        try:
            data = request.data
            work_category = data.get("work_category")
            activity_stage = data.get("activity_stage")
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
                created_by=request.user,
            )
            return Response(
                {"message": "Activity stage created", "id": activity_stages.id},
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WorkCategoryActivityStagesGetAPIView(ModifiedApiview):
    def get(self, request, id=None):
        try:
            user = self.get_user_from_token(request)
            if id:
                work_category = WorkCategoryActivityStages.objects.filter(id=id, is_active=True).first()
                if not work_category:
                    return Response({"error": "Work category not found"}, status=status.HTTP_404_NOT_FOUND)
                data = {
                    "id": work_category.id,
                    "activity_stage": work_category.activity_stage,
                    "work_category": work_category.work_category.name,
                    "description": work_category.description,
                }
                return Response(data, status=status.HTTP_200_OK)
            work_categories = WorkCategoryActivityStages.objects.filter(is_active=True).values("id", "activity_stage", 
                     "work_category")
            return Response(list(work_categories), status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class WorkCategoryActivityStagesUpdateAPIView(ModifiedApiview):
    def put(self, request, id):
        try:
            user = self.get_user_from_token(request)
            work_category = WorkCategoryActivityStages.objects.filter(id=id, is_active=True).first()
            if not work_category:
                return Response({"error": "Work category not found"}, status=status.HTTP_404_NOT_FOUND)

            data = request.data
            work_category.activity_stage = data.get("activity_stage", work_category.activity_stage)
            work_category.description = data.get("description", work_category.description)
            work_category.updated_by = user
            work_category.save()

            return Response({"message": "Work category updated"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WorkCategoryActivityStagesDeactivateAPIView(ModifiedApiview):
    def delete(self, request, id):
        try:
            user = self.get_user_from_token(request)
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
            data = request.data
            work_category = data.get("work_category")
            file_name = data.get("file_name")

            if not work_category or not file_name:
                return Response(
                    {"error": "Work Category and File Name are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            upload_document = WorkCategoryUploadDocumentRequired.objects.create(
                work_category_id=work_category,
                file_name=file_name,
                created_by=user,
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
                work_category = WorkCategoryUploadDocumentRequired.objects.filter(id=id, is_active=True).first()
                if not work_category:
                    return Response({"error": "Work category not found"}, status=status.HTTP_404_NOT_FOUND)
                data = {
                    "id": work_category.id,
                    "file_name": work_category.file_name,
                    "work_category": work_category.work_category.name,
                }
                return Response(data, status=status.HTTP_200_OK)
            work_categories = WorkCategoryUploadDocumentRequired.objects.filter(is_active=True).values("id", "file_name", 
                     "work_category")
            return Response(list(work_categories), status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WorkCategoryUploadDocumentRequiredUpdateAPIView(ModifiedApiview):
    def put(self, request, id):
        try:
            user = self.get_user_from_token(request)
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


class ClientWorkCategoryAssignmentCreateView(APIView):
    def post(self, request):
        data = request.data
        try:
            customer_id = data.get("customer_id")
            work_category_id = data.get("work_category_id")
            assigned_to_id = data.get("assigned_to_id", "")
            if assigned_to_id:
                assigned_to = CustomUser.objects.get(id=assigned_to_id)
                assigned_by = CustomUser.objects.get(id=data.get("assigned_by_id"))
                review_by = CustomUser.objects.get(id=data.get("review_by_id"))
            else:
                assigned_to = None
                assigned_by = None
                review_by = None
            
            assigned_by = request.user

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
                    progress=data.get("status", "pending_from_client_side"),
                    priority=data.get("priority", 1),
                    start_date=data.get("start_date"),
                    completion_date=data.get("completion_date"),
                    created_date=datetime.now(),
                    created_by=request.user,
                    updated_by=request.user
                )
                required_files = WorkCategoryFilesRequired.objects.filter(work_category=work_category)
                for file in required_files:
                    assigned_file = AssignedWorkRequiredFiles.objects.create(
                        assignment=assignment,
                        file_name=file.file_name,
                        is_active=True
                    )

                # Copy activity list
                activities = WorkCategoryActivityList.objects.filter(work_category=work_category)
                for activity in activities:
                    assigned_task = AssignedWorkActivity.objects.create(
                        assignment=assignment,
                        activity=activity.activity_name,
                        assigned_percentage=activity.assigned_percentage,
                        is_active=True
                    )

                # copy activity stages
                activity_stages = WorkCategoryActivityStages.objects.filter(work_category=work_category)
                for stage in activity_stages:
                    assigned_stage = AssignedWorkActivityStages.objects.create(
                        assignment=assignment,
                        activity_stage=stage.activity_stage,
                        is_active=True
                    )

                # Copy output document requirements
                output_files = WorkCategoryUploadDocumentRequired.objects.filter(work_category=work_category)
                for file in output_files:
                    assigned_file = AssignedWorkOutputFiles.objects.create(
                        assignment=assignment,
                        file_name=file.file_name,
                        is_active=True
                    )

            return Response({"message": "Assignment created successfully", "id": assignment.assignment_id}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ClientWorkCategoryAssignmentListView(APIView):
    def get(self, request):
        try:
            assignments = ClientWorkCategoryAssignment.objects.filter(is_active=True)
            data = []
            for assignment in assignments:
                data.append({
                    "id": assignment.assignment_id,
                    "customer": assignment.customer.name_of_business,
                    "work_category": assignment.work_category.name,
                    "assigned_to": assignment.assigned_to.username if assignment.assigned_to else "",
                    "assigned_by": assignment.assigned_by.username if assignment.assigned_by else "",
                    "review_by": assignment.review_by.username if assignment.review_by else "",
                    "progress": assignment.progress,
                    "priority": assignment.priority,
                    "start_date": assignment.start_date,
                    "completion_date": assignment.completion_date,
                })
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ClientWorkCategoryAssignmentRetrieveView(APIView):
    def get(self, request, assignment_id):
        try:
            assignment = ClientWorkCategoryAssignment.objects.get(assignment_id=assignment_id, is_active=True)
            data = {
                "id": assignment.assignment_id,
                "customer": assignment.customer.name_of_business,
                "work_category": assignment.work_category.name,
                "progress": assignment.progress,
                "priority": assignment.priority,
                "assigned_to": assignment.assigned_to.username if assignment.assigned_to else "",
                "assigned_by": assignment.assigned_by.username if assignment.assigned_by else "",
                "review_by": assignment.review_by.username if assignment.review_by else "",
                "start_date": assignment.start_date,
                "completion_date": assignment.completion_date,
                "required_files": list(assignment.required_files.values("file_name", "file_path")),
                "activities": list(assignment.activities.values("activity", "assigned_percentage", "status")),
                "output_files": list(assignment.output_files.values("file_name", "file_path")),
            }
            return Response(data, status=status.HTTP_200_OK)
        except ClientWorkCategoryAssignment.DoesNotExist:
            return Response({"error": "Assignment not found"}, status=status.HTTP_404_NOT_FOUND)


class ClientWorkCategoryAssignmentUpdateView(APIView):
    def put(self, request, assignment_id):
        try:
            assignment = ClientWorkCategoryAssignment.objects.get(assignment_id=assignment_id, is_active=True)
            data = request.data
            assigned_to = CustomUser.objects.get(id=data.get("assigned_to",""))
            if assigned_to:
                assigned_by = request.user
                review_by = CustomUser.objects.get(id=data.get("review_by", ""))
            else:
                assigned_to = assignment.assigned_to
                assigned_by = assignment.assigned_by
                review_by = assignment.review_by
            assignment.assigned_to = assigned_to
            assignment.review_by = review_by
            assignment.assigned_by = assigned_by
            assignment.progress = data.get("progress", assignment.progress)
            assignment.priority = data.get("priority", assignment.priority)
            assignment.start_date = data.get("start_date", assignment.start_date)
            assignment.completion_date = data.get("completion_date", assignment.completion_date)
            assignment.updated_by = request.user
            assignment.save()
            return Response({"message": "Assignment updated successfully"}, status=status.HTTP_200_OK)
        except ClientWorkCategoryAssignment.DoesNotExist:
            return Response({"error": "Assignment not found"}, status=status.HTTP_404_NOT_FOUND)


class ClientWorkCategoryAssignmentDeleteView(APIView):
    def delete(self, request, assignment_id):
        try:
            assignment = ClientWorkCategoryAssignment.objects.get(assignment_id=assignment_id, is_active=True)
            assignment.is_active = False
            assignment.updated_by = request.user
            assignment.save()
            return Response({"message": "Assignment deleted successfully"}, status=status.HTTP_200_OK)
        except ClientWorkCategoryAssignment.DoesNotExist:
            return Response({"error": "Assignment not found"}, status=status.HTTP_404_NOT_FOUND)


class AssignTaskView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        try:
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


class EditAssignedTaskView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, assignment_id):
        data = request.data
        try:
            assignment = ClientWorkCategoryAssignment.objects.get(id=assignment_id)

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


class DeleteAssignedTaskView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, assignment_id):
        try:
            assignment = ClientWorkCategoryAssignment.objects.get(id=assignment_id)
            assignment.delete()
            return Response({"message": "Assignment deleted successfully."}, status=status.HTTP_200_OK)
        except ClientWorkCategoryAssignment.DoesNotExist:
            return Response({"error": "Assignment not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class RetrieveAssignedTaskView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, assignment_id=None):
        try:
            if assignment_id:
                assignment = ClientWorkCategoryAssignment.objects.get(id=assignment_id)
                data = {
                    "id": assignment.id,
                    "customer": assignment.customer.name_of_business,
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


class RetrieveAssignedTaskByUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        try:
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
    

class RetrieveAssignedTaskByReviewByView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        try:
            user = CustomUser.objects.get(id=user_id)
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


class SubmitReviewByView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, assignment_id):
        data = request.data
        try:
            assignment = ClientWorkCategoryAssignment.objects.get(id=assignment_id)
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
                        "id": assignment.id,
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
            

