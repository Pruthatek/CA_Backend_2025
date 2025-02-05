from django.db import models
from django.contrib.auth.hashers import make_password, check_password

class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Permission(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='permissions')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name='roles')
    is_active = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('role', 'permission')


class CustomUser(models.Model):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    first_name = models.CharField(max_length=50, null=True, blank=True)
    last_name = models.CharField(max_length=50, null=True, blank=True)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, related_name='users')
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    employee_code = models.CharField(max_length=20, null=True, blank=True)
    gender = models.CharField(max_length=20, null=True, blank=True)
    photo_url = models.CharField(max_length=255, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)


    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        self.save()

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def __str__(self):
        return self.username

    @property
    def is_authenticated(self):
        """Override this method to work with Django authentication system."""
        return True
    
    @property
    def has_access(self):
        """
        Check if the user has a specific permission.
        """
        def check(permission_name):
            if not self.role or not self.role.is_active:
                return False
            return self.role.permissions.filter(
                permission__name=permission_name, is_active=True
            ).exists()
        
        return check
    
class EmployeeProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True)
    date_of_joining = models.DateField(null=True, blank=True)
    date_of_leaving = models.DateField(null=True, blank=True)
    referred_by = models.CharField(max_length=150, null=True, blank=True)
    designation = models.CharField(max_length=50, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    login_enabled = models.BooleanField(default=True)


    def __str__(self):
        return self.user.username
    

class ReportingUser(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True)
    reporting_to = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='reportees')
    working_under = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='subordinates')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.user.username