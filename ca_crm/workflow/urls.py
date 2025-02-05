from django.urls import path
from .views import (
    DepartmentCreateAPIView,
    DepartmentGetAPIView,
    DepartmentUpdateAPIView,
    DepartmentDeactivateAPIView,
    WorkCategoryCreateAPIView,
    WorkCategoryGetAPIView,
    WorkCategoryUpdateAPIView,
    WorkCategoryDeactivateAPIView,
    WorkCategoryFilesRequiredCreateAPIView,
    WorkCategoryFilesRequiredGetAPIView,
    WorkCategoryFilesRequiredUpdateAPIView,
    WorkCategoryFilesRequiredDeactivateAPIView,
    WorkCategoryActivityListCreateAPIView,
    WorkCategoryActivityListGetAPIView,
    WorkCategoryActivityListUpdateAPIView,
    WorkCategoryActivityListDeactivateAPIView,
    WorkCategoryUploadDocumentRequiredCreateAPIView,
    WorkCategoryUploadDocumentRequiredGetAPIView,
    WorkCategoryUploadDocumentRequiredUpdateAPIView,
    WorkCategoryUploadDocumentRequiredDeactivateAPIView,
    ClientWorkCategoryAssignmentCreateView,
    ClientWorkCategoryAssignmentRetrieveView,
    ClientWorkCategoryAssignmentUpdateView,
    ClientWorkCategoryAssignmentDeleteView,
    ClientWorkCategoryAssignmentListView,

)

urlpatterns = [
    path('department/create/', DepartmentCreateAPIView.as_view(), name='department_create'),
    path('department/get/', DepartmentGetAPIView.as_view(), name='department_get'),
    path('department/update/<int:id>/', DepartmentUpdateAPIView.as_view(), name='department_update'),
    path('department/deactivate/<int:id>/', DepartmentDeactivateAPIView.as_view(), name='department_deactivate'),
    
    path('work-category/create/', WorkCategoryCreateAPIView.as_view(), name='work_category_create'),
    path('work-category/get/', WorkCategoryGetAPIView.as_view(), name='work_category_get'),
    path('work-category/update/<int:id>/', WorkCategoryUpdateAPIView.as_view(), name='work_category_update'),
    path('work-category/deactivate/<int:id>/', WorkCategoryDeactivateAPIView.as_view(), name='work_category_deactivate'),
    
    path('work-category-files-required/create/', WorkCategoryFilesRequiredCreateAPIView.as_view(), name='work_category_files_required_create'),
    path('work-category-files-required/get/', WorkCategoryFilesRequiredGetAPIView.as_view(), name='work_category_files_required_get'),
    path('work-category-files-required/update/<int:id>/', WorkCategoryFilesRequiredUpdateAPIView.as_view(), name='work_category_files_required_update'),
    path('work-category-files-required/deactivate/<int:id>/', WorkCategoryFilesRequiredDeactivateAPIView.as_view(), name='work_category_files_required_deactivate'),
    
    path('work-category-activity-list/create/', WorkCategoryActivityListCreateAPIView.as_view(), name='work_category_activity_list_create'),
    path('work-category-activity-list/get/', WorkCategoryActivityListGetAPIView.as_view(), name='work_category_activity_list_get'),
    path('work-category-activity-list/update/<int:id>/', WorkCategoryActivityListUpdateAPIView.as_view(), name='work_category_activity_list_update'),
    path('work-category-activity-list/deactivate/<int:id>/', WorkCategoryActivityListDeactivateAPIView.as_view(), name='work_category_activity_list_deactivate'),
    
    path('work-category-upload-document-required/create/', WorkCategoryUploadDocumentRequiredCreateAPIView.as_view(), name='work_category_upload_document_required_create'),
    path('work-category-upload-document-required/get/', WorkCategoryUploadDocumentRequiredGetAPIView.as_view(),
            name='work_category_upload_document_required_get'),
    path('work-category-upload-document-required/update/<int:id>/', WorkCategoryUploadDocumentRequiredUpdateAPIView.as_view(),
            name='work_category_upload_document_required_update'),
    path('work-category-upload-document-required/deactivate/<int:id>/', WorkCategoryUploadDocumentRequiredDeactivateAPIView.as_view(),
         name='work_category_upload_document_required_deactivate'),

    path('client-work-category-assignment/create/', ClientWorkCategoryAssignmentCreateView.as_view(), name='client_work_category_assignment_create'),
    path('client-work-category-assignment/get/<int:assignment_id>/', ClientWorkCategoryAssignmentRetrieveView.as_view(), name='client_work_category_assignment_get'),
    path('client-work-category-assignment/get/', ClientWorkCategoryAssignmentListView.as_view(), name='client_work_category_assignment_get'),
    path('client-work-category-assignment/update/<int:assignment_id>/', ClientWorkCategoryAssignmentUpdateView.as_view(), name='client_work_category_assignment_update'),
    path('client-work-category-assignment/delete/<int:assignment_id>/', ClientWorkCategoryAssignmentDeleteView.as_view(), name='client_work_category_assignment_delete'),
    
]