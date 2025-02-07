from django.urls import path
from .views import (
    ClockInOutAPIView,
    CheckClockInStatusAPIView,
    RequestAttendanceAPIView,
    ApplyLeaveAPIView,
    GetAttendanceAPIView,
    ApproveAttendanceAPIView,
    ImportHolidayAPIView,
    HolidayListAPIView,
    CreateHolidayAPIView,
    UpdateHolidayAPIView,
    DeleteHolidayAPIView,
    RetrieveHolidayAPIView,
)

urlpatterns = [
    path('clock-in-out/', ClockInOutAPIView.as_view(), name='clock-in-out'),
    path('check-clockin/', CheckClockInStatusAPIView.as_view(), name='Check-clockIn'),
    path('Request-attendance/', RequestAttendanceAPIView.as_view(), name="Request Attendance"),
    path("apply-leave/", ApplyLeaveAPIView.as_view(), name="apply-leave"),
    path("attendance-view/", GetAttendanceAPIView.as_view(), name="Attendance-view"),
    path("approve-attendance/", ApproveAttendanceAPIView.as_view(), name="Attendance-approve"),
    path("holidays/import/", ImportHolidayAPIView.as_view(), name="import-holiday"),
    path("holidays/", HolidayListAPIView.as_view(), name="holiday-list"),
    path("holidays/new/", CreateHolidayAPIView.as_view(), name="create-holiday"),
    path("holidays/<int:id>/", RetrieveHolidayAPIView.as_view(), name="retrieve-holiday"),
    path("holidays/update/<int:id>/", UpdateHolidayAPIView.as_view(), name="update-holiday"),
    path("holidays/delete/<int:id>/", DeleteHolidayAPIView.as_view(), name="delete-holiday"),
]  