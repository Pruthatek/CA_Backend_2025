from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.core.files.storage import FileSystemStorage
import os
import posixpath
from .models import Expense, CustomUser, ClientWorkCategoryAssignment
from workflow.views import ModifiedApiview
from importexport.views import generate_short_unique_filename
from django.conf import settings



class ExpenseCreateView(ModifiedApiview):
    def post(self, request):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)

            file = request.FILES.get('file')

            # Extract data from the request
            work_id = request.data.get('work')
            expense_name = request.data.get('expense_name')
            expense_amount = request.data.get('expense_amount')
            expense_date = request.data.get('expense_date')

            # Validate required fields
            if not all([work_id, expense_name, expense_amount]):
                return Response(
                    {"error": "work, expense_name, and expense_amount are required fields."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Fetch related objects
            work = get_object_or_404(ClientWorkCategoryAssignment, assignment_id=work_id)

            # Handle file upload
            file_url = ""
            if file:
                extension = os.path.splitext(file.name)[1]  # Get the file extension
                short_unique_filename = generate_short_unique_filename(extension)
                fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'expense_files'))
                file_path = fs.save(short_unique_filename, file)
                file_url = posixpath.join('media/expense_files', file_path)

            # Create the Expense object
            expense_obj = Expense.objects.create(
                work=work,
                expense_name=expense_name,
                expense_amount=expense_amount,
                expense_date=expense_date,
                file=file_url,
                created_by=user,
                updated_by=user
            )

            # Return the created object as a response
            return Response(
                {
                    "id": expense_obj.id,
                    "work": expense_obj.work.assignment_id,
                    "expense_name": expense_obj.expense_name,
                    "expense_amount": expense_obj.expense_amount,
                    "expense_date": expense_obj.expense_date,
                    "file": expense_obj.file,
                    "created_by": expense_obj.created_by.id,
                    "updated_by": expense_obj.updated_by.id,
                    "created_date": expense_obj.created_date,
                    "updated_date": expense_obj.updated_date
                },
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ExpenseListView(ModifiedApiview):
    def get(self, request):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)

            expenses = Expense.objects.all()
            expense_list = []
            for expense in expenses:
                expense_list.append({
                    "id": expense.id,
                    "work": expense.work.assignment_id,
                    "expense_name": expense.expense_name,
                    "expense_amount": expense.expense_amount,
                    "expense_date": expense.expense_date,
                    "file": expense.file,
                    "created_by": expense.created_by.id,
                    "updated_by": expense.updated_by.id,
                    "created_date": expense.created_date,
                    "updated_date": expense.updated_date
                })

            return Response(
                expense_list,
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    
class ExpenseDetailView(ModifiedApiview):
    def get(self, request, id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)

            expense = get_object_or_404(Expense, id=id)
            return Response(
                {
                    "id": expense.id,
                    "work": expense.work.assignment_id,
                    "expense_name": expense.expense_name,
                    "expense_amount": expense.expense_amount,
                    "expense_date": expense.expense_date,
                    "file": expense.file,
                    "created_by": expense.created_by.id,
                    "updated_by": expense.updated_by.id,
                    "created_date": expense.created_date,
                    "updated_date": expense.updated_date
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

class ExpenseUpdateView(ModifiedApiview):
    def put(self, request, id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)

            expense = get_object_or_404(Expense, id=id)

            # Extract data from the request
            work_id = request.data.get('work')
            expense_name = request.data.get('expense_name')
            expense_amount = request.data.get('expense_amount')
            expense_date = request.data.get('expense_date')
            file = request.FILES.get('file')

            # Update fields if provided
            if work_id:
                expense.work = get_object_or_404(ClientWorkCategoryAssignment, assignment_id=work_id)
            if expense_name:
                expense.expense_name = expense_name
            if expense_amount:
                expense.expense_amount = expense_amount
            if expense_date:
                expense.expense_date = expense_date

            # Handle file upload
            if file:
                extension = os.path.splitext(file.name)[1]  # Get the file extension
                short_unique_filename = generate_short_unique_filename(extension)
                fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'expense_files'))
                file_path = fs.save(short_unique_filename, file)
                file_url = posixpath.join('media/expense_files', file_path)
                expense.file = file_url

            expense.updated_by = user
            expense.save()

            return Response(
                {
                    "id": expense.id,
                    "work": expense.work.assignment_id,
                    "expense_name": expense.expense_name,
                    "expense_amount": expense.expense_amount,
                    "expense_date": expense.expense_date,
                    "file": expense.file,
                    "created_by": expense.created_by.id,
                    "updated_by": expense.updated_by.id,
                    "created_date": expense.created_date,
                    "updated_date": expense.updated_date
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

class ExpenseDeleteView(ModifiedApiview):
    def delete(self, request, id):
        try:
            user = self.get_user_from_token(request)
            if not user:
                return Response({"Error": "You don't have permissions"}, status=status.HTTP_401_UNAUTHORIZED)

            expense = get_object_or_404(Expense, id=id)
            expense.delete()

            return Response(
                {"message": "Expense deleted successfully"},
                status=status.HTTP_204_NO_CONTENT
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )