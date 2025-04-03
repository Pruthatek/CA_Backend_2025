from django.urls import path
from reminders.views import (
    CustomerReminderListView,
    ReminderListView,
    ReminderRetrieveView,
    ReminderCreateView
)

urlpatterns = [
    path('reminder/create/', ReminderCreateView.as_view(), name='reminder-create'),
    path('reminder/', ReminderListView.as_view(), name='reminder-get'),
    path('reminder/fetch/<int:id>/', ReminderRetrieveView.as_view(), name='reminder-retrieve'),
    ]