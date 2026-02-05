from django.db import models
from admin.models import BaseModel
from django.core.exceptions import ValidationError

class Users(BaseModel):
    ROLE_CHOICES = (
        ('SUPERADMIN', 'Super Admin'),
        ('ADMIN', 'Admin'),
        ('USER', 'User'),
    )
    ADMIN_TYPE_CHOICES = (
        ('RESTAURANT', 'Restaurant Owner'),
        ('DELIVERY', 'Delivery Partner'),
        ('MANAGER', 'Manager'),
        ('NONE', 'None'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='USER')
    admin_type = models.CharField(max_length=20, choices=ADMIN_TYPE_CHOICES, default='NONE', null=True, blank=True)
    name = models.CharField(max_length=100)
    
    def save(self, *args, **kwargs):
        if self.role == 'SUPERADMIN':
            existing = Users.objects.filter(role='SUPERADMIN')
            if self.pk:
                existing = existing.exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError("There can be only one Super Admin.")
        super().save(*args, **kwargs)
    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(max_length=15, unique=True, null=True, blank=True)
    password_hash = models.TextField(null=True, blank=True)
    profile_image_url = models.URLField(null=True, blank=True)
    last_login = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_by = models.CharField(max_length=100, null=True, blank=True)
    updated_by = models.CharField(max_length=100, null=True, blank=True)
    deleted_by = models.CharField(max_length=100, null=True, blank=True)
    def __str__(self):
        return self.name
