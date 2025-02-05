"""
URL configuration for ca_crm project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from .views import (
    CreateEmployeeView,
    RetrieveEmployeeView,
    LoginView,
    AssignRoleView,
    CheckPermissionView,
    RoleCreateAPIView,
    RoleListAPIView,
    RoleUpdateAPIView,
    RoleDeleteAPIView,
    PermissionCreateAPIView,
    PermissionListAPIView,
    PermissionUpdateAPIView,
    PermissionDeleteAPIView,
    RolePermissionAddAPIView,
    RolePermissionListAPIView,
    RolePermissionRemoveAPIView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('create-user/', CreateEmployeeView.as_view(), name='create-employee'),
    path('retrieve-user/<int:user_id>/', RetrieveEmployeeView.as_view(), name='retrieve-employee'),
    path('login/', LoginView.as_view(), name='login'),
    path('assign-role/', AssignRoleView.as_view(), name='assign-role'),
    path('check-permission/', CheckPermissionView.as_view(), name='check-permission'),
    path('roles/create/', RoleCreateAPIView.as_view(), name='create-role'),
    path('roles/list/', RoleListAPIView.as_view(), name='list-roles'),
    path('roles/update/<int:role_id>/', RoleUpdateAPIView.as_view(), name='update-role'),
    path('roles/delete/<int:role_id>/', RoleDeleteAPIView.as_view(), name='delete-role'),
    path('permissions/create/', PermissionCreateAPIView.as_view(), name='create-permission'),
    path('permissions/list/', PermissionListAPIView.as_view(), name='list-permissions'),
    path('permissions/update/<int:permission_id>/', PermissionUpdateAPIView.as_view(), name='update-permission'),
    path('permissions/delete/<int:permission_id>/', PermissionDeleteAPIView.as_view(), name='delete-permission'),
    path('role-permission/add/', RolePermissionAddAPIView.as_view(), name='add-role-permissions'),
    path('role-permission/list/<int:role_id>/', RolePermissionListAPIView.as_view(), name='list-role-permissions'),
    path('role-permission/remove/', RolePermissionRemoveAPIView.as_view(), name='remove-role-permissions'),  
]

