from django.urls import path
from .views import (
    BillingCreateView,
    BillingListView,
    BillingRetrieveView,
    BillingUpdateView,
    BillingDeleteView,
    ReceiptCreateAPIView,
    ReceiptListAPIView,
    ReceiptRetrieveAPIView,
    ReceiptUpdateAPIView,
    ReceiptDeleteAPIView,
)

urlpatterns = [
    path('billing/create/', BillingCreateView.as_view(), name='billing-create'),
    path('billing/', BillingListView.as_view(), name='billing-list'),
    path('billing/retrieve/<int:bill_id>/', BillingRetrieveView.as_view(), name='billing-retrieve'),
    path('billing/update/<int:bill_id>/', BillingUpdateView.as_view(), name='billing-update'),
    path('billing/delete/<int:bill_id>/', BillingDeleteView.as_view(), name='billing-delete'),

    path('receipt/create/', ReceiptCreateAPIView.as_view(), name='receipt-create'),
    path('receipt/', ReceiptListAPIView.as_view(), name='receipt-list'),
    path('receipt/retrieve/<int:id>/', ReceiptRetrieveAPIView.as_view(), name='receipt-retrieve'),
    path('receipt/update/<int:id>/', ReceiptUpdateAPIView.as_view(), name='receipt-update'),
    path('receipt/delete/<int:id>/', ReceiptDeleteAPIView.as_view(), name='receipt-delete'),

]  