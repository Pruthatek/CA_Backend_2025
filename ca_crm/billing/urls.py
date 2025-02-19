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
    CreditNoteCreateView,
    CreditNoteListView,
    CreditNoteUpdateView,
    CreditNoteRetrieveView,
    CreditNoteDeleteView,
    DebitNoteCreateView,
    DebitNoteListView,
    DebitNoteUpdateView,
    DebitNoteRetrieveView,
    DebitNoteDeleteView
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

    path('credit-note/create/', CreditNoteCreateView.as_view(), name='credit-note-create'),
    path('credit-note/', CreditNoteListView.as_view(), name='credit-note-list'),
    path('credit-note/retrieve/<int:id>/', CreditNoteRetrieveView.as_view(), name='credit-note-retrieve'),
    path('credit-note/update/<int:id>/', CreditNoteUpdateView.as_view(), name='credit-note-update'),
    path('credit-note/delete/<int:id>/', CreditNoteDeleteView.as_view(), name='credit-note-delete'),

    path('debit-note/create/', DebitNoteCreateView.as_view(), name='debit-note-create'),
    path('debit-note/', DebitNoteListView.as_view(), name='debit-note-list'),
    path('debit-note/retrieve/<int:id>/', DebitNoteRetrieveView.as_view(), name='debit-note-retrieve'),
    path('debit-note/update/<int:id>/', DebitNoteUpdateView.as_view(), name='debit-note-update'),
    path('debit-note/delete/<int:id>/', DebitNoteDeleteView.as_view(), name='debit-note-delete'),

]  