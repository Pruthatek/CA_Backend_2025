from django.urls import path
from .views import (CustomerCreateAPIView,
                    CustomerListAPIView,
                    CustomerRetrieveAPIView, 
                    CustomerDeleteAPIView)

urlpatterns = [
    path('create/', CustomerCreateAPIView.as_view(), name='customer-list'),
    path('get-customers/', CustomerListAPIView.as_view(), name='customer-detail'),
    path('get-customer/<int:pk>/', CustomerRetrieveAPIView.as_view(), name='customer-retrieve'),
    # path('customers/update/<int:pk>/', CustomerUpdateView.as_view(), name='customer-update'),
    path('customers/delete/<int:pk>/', CustomerDeleteAPIView.as_view(), name='customer-delete'),
]