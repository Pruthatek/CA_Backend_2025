from django.urls import path
from .views import (
    LocationCreateView,
    LocationRetrieveView,
    LocationUpdateView,
    LocationDeleteView,
    InwardCreateView,
    InwardListView,
    InwardRetrieveView,
    InwardUpdateView,
    InwardDeleteView,
)

urlpatterns = [
    path('location/create/', LocationCreateView.as_view(), name='location-create'),
    path('location/', LocationRetrieveView.as_view(), name='location-retrieve'),
    path('location/update/<int:id>/', LocationUpdateView.as_view(), name='location-update'),
    path('location/delete/<int:id>/', LocationDeleteView.as_view(), name='location-delete'),
    
    path('inward/create/', InwardCreateView.as_view(), name='inward-create'),
    path('inward/', InwardListView.as_view(), name='inward-retrieve'),
    path('inward/retrieve/<int:id>/', InwardRetrieveView.as_view(), name='inward-retrieve'),
    path('inward/update/<int:pk>/', InwardUpdateView.as_view(), name='inward-update'),
    path('inward/delete/<int:pk>/', InwardDeleteView.as_view(), name='inward-delete'),
]  