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
    OutwardCreateView,
    OutwardListView,
    OutwardRetrieveView,
    OutwardUpdateView,
    OutwardDeleteView,
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

    path('outward/create/', OutwardCreateView.as_view(), name='outward-create'),
    path('outward/', OutwardListView.as_view(), name='outward-retrieve'),
    path('outward/retrieve/<int:pk>/', OutwardRetrieveView.as_view(), name='outward-retrieve'),
    path('outward/update/<int:pk>/', OutwardUpdateView.as_view(), name='outward-update'),
    path('outward/delete/<int:pk>/', OutwardDeleteView.as_view(), name='outward-delete'),
]  