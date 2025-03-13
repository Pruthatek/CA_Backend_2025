from django.urls import path
from .views import (CustomerCreateAPIView,
                    CustomerListAPIView,
                    CustomerRetrieveAPIView,
                    CustomerUpdateAPIView, 
                    CustomerDeleteAPIView,
                    CustomerBulkCreateExcelAPIView,
                    CustomerBranchCreateView,
                    CustomerBranchListView,
                    CustomerBranchDetailView,
                    CustomerBranchUpdateView,
                    CustomerBranchDeleteView,
                    CustomerGroupCreateView,
                    CustomerGroupListView,
                    CustomerGroupDetailView,
                    CustomerGroupUpdateView,
                    CustomerGroupDeleteView)

urlpatterns = [
    path('create/', CustomerCreateAPIView.as_view(), name='customer-list'),
    path('get-customers/', CustomerListAPIView.as_view(), name='customer-detail'),
    path('get-customer/<int:pk>/', CustomerRetrieveAPIView.as_view(), name='customer-retrieve'),
    path('customers/update/<int:pk>/', CustomerUpdateAPIView.as_view(), name='customer-update'),
    path('customers/delete/<int:pk>/', CustomerDeleteAPIView.as_view(), name='customer-delete'),
    path('customers/bulk-create/', CustomerBulkCreateExcelAPIView.as_view(), name='customer-bulk-create'),

    path('customer-groups/create/', CustomerGroupCreateView.as_view(), name='customer-group-create'),
    path('customer-groups/get/', CustomerGroupListView.as_view(), name='customer-group-detail'),
    path('customer-groups/get/<int:group_id>/', CustomerGroupDetailView.as_view(), name='customer-group-retrieve'),
    path('customer-groups/update/<int:group_id>/', CustomerGroupUpdateView.as_view(), name='customer-group-update'),
    path('customer-groups/delete/<int:group_id>/', CustomerGroupDeleteView.as_view(), name='customer-group-delete'),

    path('customer-branch/create/', CustomerBranchCreateView.as_view(), name='customer-branch-list'),
    path('customer-branch/get/', CustomerBranchListView.as_view(), name='customer-branch-detail'),
    path('customer-branch/get/<int:branch_id>/', CustomerGroupDetailView.as_view(), name='customer-branch-retrieve'),
    path('customer-branch/update/<int:branch_id>/', CustomerBranchUpdateView.as_view(), name='customer-branch-update'),
    path('customer-branch/delete/<int:branch_id>/', CustomerBranchDeleteView.as_view(), name='customer-branch-delete'),
]