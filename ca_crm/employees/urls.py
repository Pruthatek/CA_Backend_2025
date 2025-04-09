from django.urls import path
from .views import (
    ClockInOutAPIView,
    CheckClockInStatusAPIView,
    RequestAttendanceAPIView,
    GetAttendanceAPIView,
    ApproveAttendanceAPIView,
    ImportHolidayAPIView,
    HolidayListAPIView,
    CreateHolidayAPIView,
    UpdateHolidayAPIView,
    DeleteHolidayAPIView,

    LeaveTypeListAPIView, LeaveTypeCreateAPIView, LeaveTypeRetrieveAPIView,
    LeaveTypeUpdateAPIView, LeaveTypeDeleteAPIView,
    UserLeaveMappingListAPIView, UserLeaveMappingCreateAPIView,
    UserLeaveMappingRetrieveAPIView, UserLeaveMappingUpdateAPIView,
    UserLeaveMappingDeleteAPIView,

    ApplyLeaveAPIView,
    LeaveApprovalAPIView,


    RetrieveHolidayAPIView,
    BulkTimeTrackingCreateView,
    BulkTimeTrackingUpdateView,
    TimeTrackingDeleteAPIView,
    TimeTrackingListView,
    TimeTrackingRetrieveAPIView,
    TimeTrackingApproveView,
)

urlpatterns = [
    path('clock-in-out/', ClockInOutAPIView.as_view(), name='clock-in-out'),
    path('check-clockin/', CheckClockInStatusAPIView.as_view(), name='Check-clockIn'),
    path('Request-attendance/', RequestAttendanceAPIView.as_view(), name="Request Attendance"),
    path("apply-leave/", ApplyLeaveAPIView.as_view(), name="apply-leave"),
    path("approve-leave/", LeaveApprovalAPIView.as_view(), name="approve-leave"),
    path("attendance-view/", GetAttendanceAPIView.as_view(), name="Attendance-view"),
    path("approve-attendance/", ApproveAttendanceAPIView.as_view(), name="Attendance-approve"),
    
    path("holidays/import/", ImportHolidayAPIView.as_view(), name="import-holiday"),
    path("holidays/", HolidayListAPIView.as_view(), name="holiday-list"),
    path("holidays/new/", CreateHolidayAPIView.as_view(), name="create-holiday"),
    path("holidays/<int:id>/", RetrieveHolidayAPIView.as_view(), name="retrieve-holiday"),
    path("holidays/update/<int:id>/", UpdateHolidayAPIView.as_view(), name="update-holiday"),
    path("holidays/delete/<int:id>/", DeleteHolidayAPIView.as_view(), name="delete-holiday"),

    path('leave-types/', LeaveTypeListAPIView.as_view(), name='leave-type-list'),
    path('leave-types/create/', LeaveTypeCreateAPIView.as_view(), name='leave-type-create'),
    path('leave-types/<int:leave_type_id>/', LeaveTypeRetrieveAPIView.as_view(), name='leave-type-retrieve'),
    path('leave-types/<int:leave_type_id>/update/', LeaveTypeUpdateAPIView.as_view(), name='leave-type-update'),
    path('leave-types/<int:leave_type_id>/delete/', LeaveTypeDeleteAPIView.as_view(), name='leave-type-delete'),
    
    # UserLeaveMapping URLs
    path('user-leave-mappings/', UserLeaveMappingListAPIView.as_view(), name='user-leave-mapping-list'),
    path('user-leave-mappings/create/', UserLeaveMappingCreateAPIView.as_view(), name='user-leave-mapping-create'),
    path('user-leave-mappings/<int:mapping_id>/', UserLeaveMappingRetrieveAPIView.as_view(), name='user-leave-mapping-retrieve'),
    path('user-leave-mappings/<int:mapping_id>/update/', UserLeaveMappingUpdateAPIView.as_view(), name='user-leave-mapping-update'),
    path('user-leave-mappings/<int:mapping_id>/delete/', UserLeaveMappingDeleteAPIView.as_view(), name='user-leave-mapping-delete'),

    path("day-sheet/", TimeTrackingListView.as_view(), name="day-sheet-list"),
    path("day-sheet/new/", BulkTimeTrackingCreateView.as_view(), name="create-day-sheet"),
    path("day-sheet/retrieve/<int:id>/", TimeTrackingRetrieveAPIView.as_view(), name="retrieve-day-sheet"),
    path("day-sheet/update/", BulkTimeTrackingUpdateView.as_view(), name="update-day-sheet"),
    path("day-sheet/delete/<int:id>/", TimeTrackingDeleteAPIView.as_view(), name="delete-day-sheet"),
    path("day-sheet/approve/", TimeTrackingApproveView.as_view(), name="approve-day-sheet"),

]  