from django.urls import path
from company_profile.views import (
    # Company APIs
    CompanyCreateAPI,
    CompanyListAPI,
    CompanyRetrieveAPI,
    CompanyUpdateAPI,
    CompanyDeleteAPI,
    
    # Bank Details APIs
    BankDetailsCreateAPI,
    BankDetailsListAPI,
    BankDetailsRetrieveAPI,
    BankDetailsUpdateAPI,
    BankDetailsDeleteAPI
)

urlpatterns = [
    # Company URLs
    path('companies/create/', CompanyCreateAPI.as_view(), name='company-create'),
    path('companies/list/', CompanyListAPI.as_view(), name='company-list'),
    path('companies/<int:pk>/', CompanyRetrieveAPI.as_view(), name='company-retrieve'),
    path('companies/<int:pk>/update/', CompanyUpdateAPI.as_view(), name='company-update'),
    path('companies/<int:pk>/delete/', CompanyDeleteAPI.as_view(), name='company-delete'),
    
    # Bank Details URLs
    path('companies/<int:company_id>/bank-details/create/', BankDetailsCreateAPI.as_view(), name='bank-details-create'),
    path('companies/<int:company_id>/bank-details/list/', BankDetailsListAPI.as_view(), name='bank-details-list'),
    path('companies/<int:company_id>/bank-details/<int:pk>/', BankDetailsRetrieveAPI.as_view(), name='bank-details-retrieve'),
    path('companies/<int:company_id>/bank-details/<int:pk>/update/', BankDetailsUpdateAPI.as_view(), name='bank-details-update'),
    path('companies/<int:company_id>/bank-details/<int:pk>/delete/', BankDetailsDeleteAPI.as_view(), name='bank-details-delete'),
]