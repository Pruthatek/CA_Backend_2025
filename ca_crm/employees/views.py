from django.utils.timezone import now
from django.db import transaction
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from datetime import date, datetime, timedelta
from .models import EmployeeAttendance, CustomUser, Holiday, TimeTracking
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


class ApproveAttendanceAPIView(APIView):
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
        

class ImportHolidayAPIView(APIView):
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


class HolidayListAPIView(APIView):
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


class CreateHolidayAPIView(APIView):
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


class RetrieveHolidayAPIView(APIView):
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


class UpdateHolidayAPIView(APIView):
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


class DeleteHolidayAPIView(APIView):
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
