from django.urls import path
from .views import (
    CreateDSCView,
    UpdateDSCView,
    DeleteDSCView,
    RetrieveDSCView,
    ListDSCView,
    BulkCreateDSCView
)

urlpatterns = [
    path('dcs/create/', CreateDSCView.as_view(), name='dcs-create'),
    path('dcs/', ListDSCView.as_view(), name='dcs-list'),
    path('dcs/retrieve/<int:id>/', RetrieveDSCView.as_view(), name='dcs-retrieve'),
    path('dcs/update/<int:id>/', UpdateDSCView.as_view(), name='dcs-update'),
    path('dcs/delete/<int:id>/', DeleteDSCView.as_view(), name='dcs-delete'),
    path('dcs/upload/', BulkCreateDSCView.as_view(), name='dcs-bulk-create'),
]  