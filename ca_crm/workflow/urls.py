from django.urls import path
from .views import (
    DepartmentCreateAPIView,
    DepartmentGetAPIView,
    DepartmentUpdateAPIView,
    DepartmentDeactivateAPIView,
    
    GetDepartmentWorkCategoriesAPIView,
    
    WorkCategoryCreateAPIView,
    WorkCategoryGetAPIView,
    WorkCategoryUpdateAPIView,
    WorkCategoryDeactivateAPIView,
    
    WorkCategoryRetrieveAPIView,
    
    WorkCategoryFilesRequiredCreateAPIView,
    WorkCategoryFilesRequiredGetAPIView,
    WorkCategoryFilesRequiredUpdateAPIView,
    WorkCategoryFilesRequiredDeactivateAPIView,
    
    WorkCategoryActivityListCreateAPIView,
    WorkCategoryActivityListGetAPIView,
    WorkCategoryActivityListUpdateAPIView,
    WorkCategoryActivityListDeactivateAPIView,

    WorkCategoryActivityStagesCreateAPIView,
    WorkCategoryActivityStagesGetAPIView,
    WorkCategoryActivityStagesUpdateAPIView,
    WorkCategoryActivityStagesDeactivateAPIView,
    
    WorkCategoryUploadDocumentRequiredCreateAPIView,
    WorkCategoryUploadDocumentRequiredGetAPIView,
    WorkCategoryUploadDocumentRequiredUpdateAPIView,
    WorkCategoryUploadDocumentRequiredDeactivateAPIView,
    
    ClientWorkCategoryAssignmentCreateView,
    ClientWorkCategoryAssignmentRetrieveView,
    ClientWorkCategoryAssignmentUpdateView,
    ClientWorkCategoryAssignmentDeleteView,
    ClientWorkCategoryAssignmentListView,
    ClientWorkCategoryAssignmentFilteredListView,

    SubmitClientWorkRequiredFiles,
    SubmitClientWorkActivityList,
    SubmitClientWorkActivityStage,
    SubmitClientWorkOutputFiles,
    SubmitClientWorkAdditionalActivity,
    SubmitClientWorkAdditionalFiles,
    SubmitReviewByView,

    WorkCategoryUploadDocumentRequiredBulkCreateAPIView,
    WorkCategoryActivityListBulkCreateAPIView,
    WorkCategoryOutputFileBulkCreateAPIView,

    ConsolidatedTaskDetailsWithExpensesAndBillingView,
)

urlpatterns = [
    path('department/create/', DepartmentCreateAPIView.as_view(), name='department_create'),
    path('department/get/', DepartmentGetAPIView.as_view(), name='department_get'),
    path('department/update/<int:id>/', DepartmentUpdateAPIView.as_view(), name='department_update'),
    path('department/deactivate/<int:id>/', DepartmentDeactivateAPIView.as_view(), name='department_deactivate'),
    path('department/get-work-categories/<int:id>/', GetDepartmentWorkCategoriesAPIView.as_view(), name='department_get_work_categories'),
    
    path('work-category/create/', WorkCategoryCreateAPIView.as_view(), name='work_category_create'),
    path('work-category/get/', WorkCategoryGetAPIView.as_view(), name='work_category_get'),
    path('work-category/update/<int:id>/', WorkCategoryUpdateAPIView.as_view(), name='work_category_update'),
    path('work-category/deactivate/<int:id>/', WorkCategoryDeactivateAPIView.as_view(), name='work_category_deactivate'),
    path('work-category/get/<int:id>/', WorkCategoryRetrieveAPIView.as_view(), name='work_category_retrieve'),

    path('work-category-files-required/create/', WorkCategoryFilesRequiredCreateAPIView.as_view(), name='work_category_files_required_create'),
    path('work-category-files-required/get/', WorkCategoryFilesRequiredGetAPIView.as_view(), name='work_category_files_required_get'),
    path('work-category-files-required/update/<int:id>/', WorkCategoryFilesRequiredUpdateAPIView.as_view(), name='work_category_files_required_update'),
    path('work-category-files-required/deactivate/<int:id>/', WorkCategoryFilesRequiredDeactivateAPIView.as_view(), name='work_category_files_required_deactivate'),
    
    path('work-category-activity-list/create/', WorkCategoryActivityListCreateAPIView.as_view(), name='work_category_activity_list_create'),
    path('work-category-activity-list/get/', WorkCategoryActivityListGetAPIView.as_view(), name='work_category_activity_list_get'),
    path('work-category-activity-list/update/<int:id>/', WorkCategoryActivityListUpdateAPIView.as_view(), name='work_category_activity_list_update'),
    path('work-category-activity-list/deactivate/<int:id>/', WorkCategoryActivityListDeactivateAPIView.as_view(), name='work_category_activity_list_deactivate'),
    
    path('work-category-activity-stage/create/', WorkCategoryActivityStagesCreateAPIView.as_view(), name='work_category_activity_stage_create'),
    path('work-category-activity-stage/get/', WorkCategoryActivityStagesGetAPIView.as_view(), name='work_category_activity_stage_get'),
    path('work-category-activity-stage/update/<int:id>/', WorkCategoryActivityStagesUpdateAPIView.as_view(), name='work_category_activity_stage_update'),
    path('work-category-activity-stage/deactivate/<int:id>/', WorkCategoryActivityStagesDeactivateAPIView.as_view(), name='work_category_activity_stage_deactivate'),

    path('work-category-output-document/create/', WorkCategoryUploadDocumentRequiredCreateAPIView.as_view(), name='work_category_upload_document_required_create'),
    path('work-category-output-document/get/', WorkCategoryUploadDocumentRequiredGetAPIView.as_view(),
            name='work_category_upload_document_required_get'),
    path('work-category-output-document/update/<int:id>/', WorkCategoryUploadDocumentRequiredUpdateAPIView.as_view(),
            name='work_category_upload_document_required_update'),
    path('work-category-output-document/deactivate/<int:id>/', WorkCategoryUploadDocumentRequiredDeactivateAPIView.as_view(),
         name='work_category_upload_document_required_deactivate'),

    path('client-work-category-assignment/create/', ClientWorkCategoryAssignmentCreateView.as_view(), name='client_work_category_assignment_create'),
    path('client-work-category-assignment/get/<int:assignment_id>/', ClientWorkCategoryAssignmentRetrieveView.as_view(), name='client_work_category_assignment_get'),
    path('client-work-category-assignment/get/', ClientWorkCategoryAssignmentListView.as_view(), name='client_work_category_assignment_get'),
    path('client-work-category-assignment/filter/', ClientWorkCategoryAssignmentFilteredListView.as_view(), name='client_work_category_assignment_get_filter'),
    path('client-work-category-assignment/update/<int:assignment_id>/', ClientWorkCategoryAssignmentUpdateView.as_view(), name='client_work_category_assignment_update'),
    path('client-work-category-assignment/delete/<int:assignment_id>/', ClientWorkCategoryAssignmentDeleteView.as_view(), name='client_work_category_assignment_delete'),
    
    path('submit-client-work/required-files/<int:assignment_id>/', SubmitClientWorkRequiredFiles.as_view(), name="submit-client-work-required-files"),
    path('submit-client-work/activity-list/<int:assignment_id>/', SubmitClientWorkActivityList.as_view(), name="submit-client-work-activity-list"),
    path('submit-client-work/activity-stage/<int:assignment_id>/', SubmitClientWorkActivityStage.as_view(), name="submit-client-work-activity-stage"),
    path('submit-client-work/output-files/<int:assignment_id>/', SubmitClientWorkOutputFiles.as_view(), name="submit-client-work-required-files"),
    path('submit-client-work/additional-files/<int:assignment_id>/', SubmitClientWorkAdditionalFiles.as_view(), name="submit-client-work-additional-files"),
    path('submit-client-work/additional-activity/<int:assignment_id>/', SubmitClientWorkAdditionalActivity.as_view(), name="submit-client-work-additional-activities"),

    path('submit-client-work/review-submission/<int:assignment_id>/', SubmitReviewByView.as_view(), name="submit-client-work-review-submission"),

    path('bulk-upload/required-files/', WorkCategoryUploadDocumentRequiredBulkCreateAPIView.as_view(), name="files-required-bulk-create"),
    path('bulk-upload/activity-list/', WorkCategoryActivityListBulkCreateAPIView.as_view(), name="activity-list-bulk-create"),
    path('bulk-upload/output-files/', WorkCategoryOutputFileBulkCreateAPIView.as_view(), name="output-files-bulk-create"),

    path('reports/consolidate-task/', ConsolidatedTaskDetailsWithExpensesAndBillingView.as_view(), name="consolidate-task-details"),

]