from django.urls import path
from .views import (
    CreateDSCView,
    UpdateDSCView,
    DeleteDSCView,
    RetrieveDSCView,
    ListDSCView,
    BulkCreateDSCView,
    CreateDSCUseView
)

urlpatterns = [
    path('dsc/create/', CreateDSCView.as_view(), name='dsc-create'),
    path('dsc/', ListDSCView.as_view(), name='dsc-list'),
    path('dsc/retrieve/<int:id>/', RetrieveDSCView.as_view(), name='dsc-retrieve'),
    path('dsc/update/<int:id>/', UpdateDSCView.as_view(), name='dsc-update'),
    path('dsc/delete/<int:id>/', DeleteDSCView.as_view(), name='dsc-delete'),
    path('dsc/upload/', BulkCreateDSCView.as_view(), name='dsc-bulk-create'),
    path('dsc/use/', CreateDSCUseView.as_view(), name='dsc-use-create'),
]  