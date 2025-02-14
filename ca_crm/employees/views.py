from django.utils.timezone import now
from django.db import transaction
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
import traceback
from datetime import date, datetime, timedelta
from .models import (EmployeeAttendance, 
                     CustomUser, 
                     Holiday, 
                     TimeTracking, 
                     Customer, 
                     ClientWorkCategoryAssignment, 
                     AssignedWorkActivity)
from django.utils import timezone
from workflow.views import ModifiedApiview
import pytz
import pandas as pd
from django.db.models import Q 
from django.utils.timezone import make_aware
from django.db import transaction
IST = pytz.timezone('Asia/Kolkata')

class ClockInOutAPIView(ModifiedApiview):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            user = self.get_user_from_token(request)  # Get user from token
            employee = user
            today = date.today()

            # Convert current time to IST (Indian Standard Time)
            ist = pytz.timezone('Asia/Kolkata')
            ist_now = now().astimezone(ist)

            with transaction.atomic():
                attendance, created = EmployeeAttendance.objects.get_or_create(
                    employee=employee, date=today,
                    defaults={'status': 'present', 'check_in': ist_now.time(), "is_approved": True}
                )
                
                if not created:
                    if attendance.check_out:
                        attendance.check_out = ist_now.time()
                        attendance.save()
                    attendance.check_out = ist_now.time()
                    attendance.save()
                    return Response({"message": "Clock-out successful"}, status=status.HTTP_status.HTTP_200_OK_OK)

            return Response({"message": "Clock-in successful"}, status=status.HTTP_201_CREATED)

        except CustomUser.DoesNotExist:
            return Response({"error": "Employee profile not found"}, status=status.HTTP_status.HTTP_404_NOT_FOUND_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_status.HTTP_500_INTERNAL_SERVER_ERROR_INTERNAL_SERVER_ERROR)
        

class CheckClockInStatusAPIView(ModifiedApiview):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = self.get_user_from_token(request)
            employee = user
            today = date.today()

            attendance = EmployeeAttendance.objects.filter(employee=employee, date=today).first()
            if not attendance:
                return Response({"clocked_in": False}, status=status.HTTP_200_OK)

            return Response({
                "clocked_in": True,
                "check_in": attendance.check_in.strftime("%H:%M:%S") if attendance.check_in else None,
                "check_out": attendance.check_out.strftime("%H:%M:%S") if attendance.check_out else None,
            }, status=status.HTTP_200_OK)

        except CustomUser.DoesNotExist:
            return Response({"error": "Employee profile not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RequestAttendanceAPIView(ModifiedApiview):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            user = self.get_user_from_token(request)
            employee = user
            request_date = request.data.get("date")
            check_in = request.data.get("check_in")  # Expected format: "HH:MM:SS"
            check_out = request.data.get("check_out")  # Expected format: "HH:MM:SS"
            is_leave_applied = request.data.get("is_leave_applied")

            if not request_date:
                return Response({"error": "Date is required"}, status=status.HTTP_400_BAD_REQUEST)

            request_date = date.fromisoformat(request_date)

            if request_date >= date.today():
                return Response({"error": "Cannot request attendance for future dates"}, status=status.HTTP_400_BAD_REQUEST)

            check_in_time = None
            check_out_time = None

            if check_in:
                check_in_time = make_aware(datetime.strptime(check_in, "%H:%M:%S"), IST).time()

            if check_out:
                check_out_time = make_aware(datetime.strptime(check_out, "%H:%M:%S"), IST).time()

            if is_leave_applied:
                with transaction.atomic():
                    attendance, created = EmployeeAttendance.objects.get_or_create(
                        employee=employee, date=request_date,
                        defaults={"status": "leave", "is_approved": False}
                    )

                    if not created:
                        attendance.save()
                return Response({"message": "Leave requested successfully"}, status=status.HTTP_201_CREATED) 
            else:
                with transaction.atomic():
                    attendance, created = EmployeeAttendance.objects.get_or_create(
                        employee=employee, date=request_date,
                        defaults={"status": "present", "is_approved": False, "check_in": check_in_time, "check_out": check_out_time}
                    )

                    if not created:
                        attendance.check_in = check_in_time if check_in_time else attendance.check_in
                        attendance.check_out = check_out_time if check_out_time else attendance.check_out
                        attendance.save()

            return Response({"message": "Attendance requested successfully"}, status=status.HTTP_201_CREATED)

        except CustomUser.DoesNotExist:
            return Response({"error": "Employee profile not found"}, status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response({"error": "Invalid date or time format. Use YYYY-MM-DD for date and HH:MM:SS for time"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ApplyLeaveAPIView(ModifiedApiview):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            user = self.get_user_from_token(request)
            employee = user
            leave_date = request.data.get("date")
            remarks = request.data.get("remarks", "")

            if not leave_date:
                return Response({"error": "Date is required"}, status=status.HTTP_400_BAD_REQUEST)

            leave_date = date.fromisoformat(leave_date)

            with transaction.atomic():
                attendance, created = EmployeeAttendance.objects.get_or_create(
                    employee=employee, date=leave_date,
                    defaults={"status": "leave", "remarks": remarks, "is_approved":False}
                )

                if not created:
                    attendance.status = "leave"
                    attendance.remarks = remarks
                    attendance.is_approved = False
                    attendance.save()

            return Response({"message": "Leave applied successfully"}, status=status.HTTP_201_CREATED)

        except CustomUser.DoesNotExist:
            return Response({"error": "Employee profile not found"}, status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response({"error": "Invalid date format. Use YYYY-MM-DD"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetAttendanceAPIView(ModifiedApiview):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = self.get_user_from_token(request)
            employee_id = request.GET.get("employee_id")  # Filter by employee
            month = request.GET.get("month")  # Format: YYYY-MM
            filters = Q()

            # Filter by employee if employee_id is provided
            if employee_id:
                filters &= Q(employee__id=employee_id)

            # Filter by month if provided
            if month:
                try:
                    year, month = map(int, month.split("-"))
                    filters &= Q(date__year=year, date__month=month)
                except ValueError:
                    return Response({"error": "Invalid month format. Use YYYY-MM"}, status=status.HTTP_400_BAD_REQUEST)

            # Fetch records with filters
            attendance_records = EmployeeAttendance.objects.filter(filters).select_related("employee")

            # Convert queryset to JSON
            data = [
                {   
                    "record_id":record.id,
                    "employee": record.employee.username,
                    "employee_id": record.employee.id,
                    "date": record.date.strftime("%Y-%m-%d"),
                    "status": record.status,
                    "check_in": record.check_in.strftime("%H:%M:%S") if record.check_in else None,
                    "check_out": record.check_out.strftime("%H:%M:%S") if record.check_out else None,
                    "remarks": record.remarks,
                    "is_approved":record.is_approved,
                }
                for record in attendance_records
            ]

            return Response({"attendance": data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ApproveAttendanceAPIView(ModifiedApiview):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            attendance_id = request.data.get("attendance_id")
            approval_status = request.data.get("status")  # "approved" or "rejected"

            if not attendance_id or approval_status not in ["approved", "rejected"]:
                return Response({"error": "attendance_id and valid status (approved/rejected) are required"}, status=status.HTTP_400_BAD_REQUEST)

            # Fetch attendance record
            try:
                attendance = EmployeeAttendance.objects.get(id=attendance_id)
            except EmployeeAttendance.DoesNotExist:
                return Response({"error": "Attendance request not found"}, status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
                if approval_status == "approved":
                    attendance.is_approved = True
                else:
                    attendance.is_approved = False  # Mark as rejected if needed

                attendance.save()

            return Response({"message": f"Attendance request {approval_status} successfully"}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class ImportHolidayAPIView(ModifiedApiview):
    """API to import holidays from a CSV file using pandas."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            file = request.FILES.get("file")
            if not file:
                return Response({"error": "CSV file is required"}, status=status.HTTP_400_BAD_REQUEST)

            df = pd.read_csv(file)

            required_columns = {"date", "name", "description", "is_optional"}
            if not required_columns.issubset(df.columns):
                return Response({"error": "Invalid CSV format. Required columns: date, name, description, is_optional"}, status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
                for _, row in df.iterrows():
                    try:
                        holiday_date = datetime.strptime(row["date"], "%Y-%m-%d").date()
                        Holiday.objects.get_or_create(
                            date=holiday_date,
                            defaults={
                                "name": row["name"],
                                "description": row.get("description", ""),
                                "is_optional": bool(row["is_optional"])
                            }
                        )
                    except ValueError:
                        continue  # Skip invalid date formats

            return Response({"message": "Holidays imported successfully"}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HolidayListAPIView(ModifiedApiview):
    """API to list all holidays."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        holidays = Holiday.objects.all()
        data = [
            {
                "id": h.id,
                "date": h.date.strftime("%Y-%m-%d"),
                "name": h.name,
                "description": h.description,
                "is_optional": h.is_optional
            }
            for h in holidays
        ]
        return Response({"holidays": data}, status=status.HTTP_200_OK)


class CreateHolidayAPIView(ModifiedApiview):
    """API to create a new holiday."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            date_str = request.data.get("date")
            name = request.data.get("name")
            description = request.data.get("description", "")
            is_optional = request.data.get("is_optional", False)

            if not date_str or not name:
                return Response({"error": "Date and name are required"}, status=status.HTTP_400_BAD_REQUEST)

            holiday_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            is_optional = bool(is_optional)

            holiday, created = Holiday.objects.get_or_create(
                date=holiday_date,
                defaults={"name": name, "description": description, "is_optional": is_optional}
            )

            if not created:
                return Response({"error": "Holiday already exists"}, status=status.HTTP_400_BAD_REQUEST)

            return Response({"message": "Holiday created successfully"}, status=status.HTTP_201_CREATED)

        except ValueError:
            return Response({"error": "Invalid date format. Use YYYY-MM-DD"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RetrieveHolidayAPIView(ModifiedApiview):
    """API to retrieve a single holiday by ID."""
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        try:
            holiday = Holiday.objects.get(id=id)
            data = {
                "id": holiday.id,
                "date": holiday.date.strftime("%Y-%m-%d"),
                "name": holiday.name,
                "description": holiday.description,
                "is_optional": holiday.is_optional
            }
            return Response(data, status=status.HTTP_200_OK)
        except Holiday.DoesNotExist:
            return Response({"error": "Holiday not found"}, status=status.HTTP_404_NOT_FOUND)


class UpdateHolidayAPIView(ModifiedApiview):
    """API to update a holiday by ID."""
    permission_classes = [IsAuthenticated]

    def put(self, request, id):
        try:
            holiday = Holiday.objects.get(id=id)
            holiday.name = request.data.get("name", holiday.name)
            holiday.description = request.data.get("description", holiday.description)
            holiday.is_optional = request.data.get("is_optional", holiday.is_optional)

            date_str = request.data.get("date")
            if date_str:
                holiday.date = datetime.strptime(date_str, "%Y-%m-%d").date()

            holiday.save()
            return Response({"message": "Holiday updated successfully"}, status=status.HTTP_200_OK)

        except Holiday.DoesNotExist:
            return Response({"error": "Holiday not found"}, status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response({"error": "Invalid date format. Use YYYY-MM-DD"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DeleteHolidayAPIView(ModifiedApiview):
    """API to delete a holiday by ID."""
    permission_classes = [IsAuthenticated]

    def delete(self, request, id):
        try:
            holiday = Holiday.objects.get(id=id)
            holiday.delete()
            return Response({"message": "Holiday deleted successfully"}, status=status.HTTP_200_OK)
        except Holiday.DoesNotExist:
            return Response({"error": "Holiday not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BulkTimeTrackingCreateView(APIView):
    def post(self, request, *args, **kwargs):
        # Expect a list of time tracking entries in the request data
        time_tracking_data = request.data

        if not isinstance(time_tracking_data, list):
            return Response(
                {"error": "Expected a list of time tracking entries."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        created_entries = []
        errors = []

        for entry in time_tracking_data:
            try:
                # Validate and extract required fields
                employee_id = entry.get("employee")
                client_id = entry.get("client")
                work_id = entry.get("work")
                work_activity_id = entry.get("work_activity")
                task_type = entry.get("task_type", "non_billable")
                date_str = entry.get("date")  # Date as string
                start_time = entry.get("start_time")
                end_time = entry.get("end_time")
                task_description = entry.get("task_description")
                is_approved = entry.get("is_approved", False)

                # Validate required fields
                if not employee_id or not date_str:
                    errors.append({"error": "Employee and date are required.", "data": entry})
                    continue

                # Convert date string to datetime.date object
                try:
                    date = datetime.strptime(date_str, "%Y-%m-%d").date()
                except ValueError:
                    errors.append({"error": "Invalid date format. Use YYYY-MM-DD.", "data": entry})
                    continue

                # Fetch related objects (if provided)
                employee = CustomUser.objects.filter(id=employee_id).first()
                client = Customer.objects.filter(id=client_id).first() if client_id else None
                work = ClientWorkCategoryAssignment.objects.filter(assignment_id=work_id).first() if work_id else None
                work_activity = AssignedWorkActivity.objects.filter(id=work_activity_id).first() if work_activity_id else None

                # Calculate duration if start_time and end_time are provided
                duration = None
                if start_time and end_time:
                    try:
                        start = datetime.strptime(f"{date_str} {start_time}", "%Y-%m-%d %H:%M:%S")
                        end = datetime.strptime(f"{date_str} {end_time}", "%Y-%m-%d %H:%M:%S")
                        # duration = end - start
                    except ValueError:
                        errors.append({"error": "Invalid time format. Use HH:MM:SS.", "data": entry})
                        continue


                # Create the TimeTracking instance
                time_entry = TimeTracking(
                    employee=employee,
                    client=client,
                    work=work,
                    work_activity=work_activity,
                    task_type=task_type,
                    date=date,  # Use the converted date object
                    start_time=start,
                    end_time=end,
                    task_description=task_description,
                    # duration=duration,
                    is_approved=is_approved,
                )
                time_entry.save()

                created_entries.append({
                    "id": time_entry.id,
                    "employee": employee_id,
                    "client": client_id,
                    "work": work_id,
                    "work_activity": work_activity_id,
                    "task_type": task_type,
                    "date": date_str,  # Return the original date string
                    "start_time": start_time,
                    "end_time": end_time,
                    "task_description": task_description,
                    "duration": str(duration) if duration else None,
                    "is_approved": is_approved,
                })

            except Exception as e:
                print(traceback.format_exc())
                errors.append({"error": str(e), "data": entry})

        if errors:
            return Response(
                {"created_entries": created_entries, "errors": errors},
                status=status.HTTP_207_MULTI_STATUS,
            )

        return Response(
            {"created_entries": created_entries},
            status=status.HTTP_201_CREATED,
        )    


class BulkTimeTrackingUpdateView(APIView):
    def put(self, request, *args, **kwargs):
        # Expect a list of time tracking entries in the request data
        time_tracking_data = request.data

        if not isinstance(time_tracking_data, list):
            return Response(
                {"error": "Expected a list of time tracking entries."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        updated_entries = []
        errors = []

        for entry in time_tracking_data:
            try:
                # Validate that the entry has an ID
                entry_id = entry.get("id")
                if not entry_id:
                    errors.append({"error": "ID is required for updating an entry.", "data": entry})
                    continue

                # Fetch the existing TimeTracking entry
                time_entry = TimeTracking.objects.filter(id=entry_id).first()
                if not time_entry:
                    errors.append({"error": f"TimeTracking entry with ID {entry_id} does not exist.", "data": entry})
                    continue

                # Update fields if they are provided in the request
                if "employee" in entry:
                    employee = CustomUser.objects.filter(id=entry["employee"]).first()
                    if employee:
                        time_entry.employee = employee
                    else:
                        errors.append({"error": f"Employee with ID {entry['employee']} does not exist.", "data": entry})
                        continue

                if "client" in entry:
                    client = Customer.objects.filter(id=entry["client"]).first() if entry["client"] else None
                    time_entry.client = client

                if "work" in entry:
                    work = ClientWorkCategoryAssignment.objects.filter(assignment_id=entry["work"]).first() if entry["work"] else None
                    time_entry.work = work

                if "work_activity" in entry:
                    work_activity = AssignedWorkActivity.objects.filter(id=entry["work_activity"]).first() if entry["work_activity"] else None
                    time_entry.work_activity = work_activity

                if "task_type" in entry:
                    time_entry.task_type = entry["task_type"]

                if "date" in entry:
                    time_entry.date = entry["date"]
                    time_entry.date = datetime.strptime(time_entry.date, "%Y-%m-%d").date()


                if "start_time" in entry:
                    time_entry.start_time = entry["start_time"]

                if "end_time" in entry:
                    time_entry.end_time = entry["end_time"]

                if "task_description" in entry:
                    time_entry.task_description = entry["task_description"]

                if "is_approved" in entry:
                    time_entry.is_approved = entry["is_approved"]

                # Recalculate duration if start_time or end_time is updated
                if "start_time" in entry or "end_time" in entry:
                    if time_entry.start_time and time_entry.end_time:
                        start = datetime.strptime(f"{time_entry.date} {time_entry.start_time}", "%Y-%m-%d %H:%M:%S")
                        end = datetime.strptime(f"{time_entry.date} {time_entry.end_time}", "%Y-%m-%d %H:%M:%S")
                        time_entry.start_time = start
                        time_entry.end_time = end
                        
                # Save the updated entry
                time_entry.save()

                updated_entries.append({
                    "id": time_entry.id,
                    "employee": time_entry.employee.id if time_entry.employee else None,
                    "client": time_entry.client.id if time_entry.client else None,
                    "work": time_entry.work.assignment_id if time_entry.work else None,
                    "work_activity": time_entry.work_activity.id if time_entry.work_activity else None,
                    "task_type": time_entry.task_type,
                    "date": time_entry.date,
                    "start_time": start,
                    "end_time": end,
                    "task_description": time_entry.task_description,
                    "is_approved": time_entry.is_approved,
                })

            except Exception as e:
                errors.append({"error": str(e), "data": entry})

        if errors:
            return Response(
                {"updated_entries": updated_entries, "errors": errors},
                status=status.HTTP_207_MULTI_STATUS,
            )

        return Response(
            {"updated_entries": updated_entries},
            status=status.HTTP_200_OK,
        )


class TimeTrackingListView(APIView):
    def get(self, request, *args, **kwargs):
        # Optional query parameters for filtering
        employee_id = request.query_params.get('employee')
        date = request.query_params.get('date')
        task_type = request.query_params.get('task_type')
        is_approved = request.query_params.get('is_approved')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        # Start with all records
        queryset = TimeTracking.objects.all()

        # Apply filters if provided
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        if date:
            queryset = queryset.filter(date=date)
        if task_type:
            queryset = queryset.filter(task_type=task_type)
        if is_approved:
            queryset = queryset.filter(is_approved=is_approved.lower() == 'true')

        # Handle start_date and end_date filters
        if start_date and end_date:
            queryset = queryset.filter(date__range=[start_date, end_date])
        elif start_date:
            queryset = queryset.filter(date__gte=start_date)
        elif end_date:
            queryset = queryset.filter(date__lte=end_date)

        # If no filters are applied, show only this week's records by default
        if not any([employee_id, date, task_type, is_approved, start_date, end_date]):
            # Calculate the start and end of the current week
            today = datetime.today()
            start_of_week = today - timedelta(days=today.weekday())  # Monday
            end_of_week = start_of_week + timedelta(days=6)          # Sunday
            queryset = queryset.filter(date__range=[start_of_week, end_of_week])

        # Serialize the data
        data = []
        for entry in queryset:
            data.append({
                "id": entry.id,
                "employee": entry.employee.id if entry.employee else None,
                "employee_name": entry.employee.username if entry.employee else None,
                "client_id": entry.client.id if entry.client else None,
                "client": entry.client.name_of_business if entry.client else None,
                "work_id": entry.work.assignment_id if entry.work else None,
                "work": entry.work.work_category.name if entry.work else None,
                "work_activity_id": entry.work_activity.id if entry.work_activity else None,
                "work_activity": entry.work_activity.activity if entry.work_activity else None,
                "task_type": entry.task_type,
                "date": entry.date,
                "start_time": entry.start_time,
                "end_time": entry.end_time,
                "task_description": entry.task_description,
                "duration": str(entry.duration) if entry.duration else None,
                "is_approved": entry.is_approved,
                "created_at": entry.created_at,
            })

        return Response(data, status=status.HTTP_200_OK)    

# Retrieve, update, and delete a single record
class TimeTrackingRetrieveAPIView(ModifiedApiview):
    def get(self, request, id):
        try:
            instance = TimeTracking.objects.get(id=id)
            data = {
                'id': instance.id,
                "employee": instance.employee.id if instance.employee else None,
                "employee_name": instance.employee.username if instance.employee else None,
                "client": instance.client.id if instance.client else None,
                "client": instance.client.name_of_business if instance.client else None,
                "work": instance.work.assignment_id if instance.work else None,
                "work": instance.work.work_category.name if instance.work else None,
                "work_activity": instance.work_activity.id if instance.work_activity else None,
                "work_activity": instance.work_activity.activity if instance.work_activity else None,
                'task_type': instance.task_type,
                'date': instance.date,
                'start_time': instance.start_time,
                'end_time': instance.end_time,
                'task_description': instance.task_description,
                'duration': instance.duration.total_seconds() if instance.duration else None,
                'is_approved': instance.is_approved,
                'created_at': instance.created_at,
            }
            return Response(data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class TimeTrackingDeleteAPIView(ModifiedApiview):
    def delete(self, request, pk, format=None):
        try:
            inst = self.get_object(pk)
            inst.delete()
            return Response({'message': 'Record deleted successfully.'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class TimeTrackingApproveView(ModifiedApiview):
    def post(self, request):
        # Expect a list of record IDs in the request data
        try:
            record_ids = request.data.get('record_ids', [])

            if not isinstance(record_ids, list):
                return Response(
                    {"error": "Expected a list of record IDs."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Fetch the records to be approved
            records_to_approve = TimeTracking.objects.filter(id__in=record_ids)

            if not records_to_approve.exists():
                return Response(
                    {"error": "No records found with the provided IDs."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Approve the records
            records_to_approve.update(is_approved=True)

            # Return the IDs of the approved records
            approved_ids = list(records_to_approve.values_list('id', flat=True))
            return Response(
                {"message": "Records approved successfully.", "approved_ids": approved_ids},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)