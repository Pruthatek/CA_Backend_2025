from django.urls import path
from .views import (
    ExpenseCreateView,
    ExpenseListView,
    ExpenseDetailView,
    ExpenseUpdateView,
    ExpenseDeleteView
)

urlpatterns = [
    path('expense/create/', ExpenseCreateView.as_view(), name='expense-create'),
    path('expense/', ExpenseListView.as_view(), name='expense-list'),
    path('expense/retrieve/<int:id>/', ExpenseDetailView.as_view(), name='expense-retrieve'),
    path('expense/update/<int:id>/', ExpenseUpdateView.as_view(), name='expense-update'),
    path('expense/delete/<int:id>/', ExpenseDeleteView.as_view(), name='expense-delete'),
]  