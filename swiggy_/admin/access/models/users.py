from django.db import models
from .base_model import BaseModel
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator, RegexValidator

class Users(BaseModel):
    ROLE_CHOICES = (
        ('SUPERADMIN', 'Super Admin'),
        ('ADMIN', 'Admin'),
        ('USER', 'User'),
    )

    ADMIN_TYPE_CHOICES = (
        ('SUPERADMIN', 'Super Admin'),
        ('RESTAURANT_ADMIN', 'Restaurant Admin'),
        ('NONE', 'None'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, db_index=True)
    admin_type = models.CharField(max_length=20, choices=ADMIN_TYPE_CHOICES, default='NONE')
    username = models.CharField(max_length=100) # Renamed from name
    
    email = models.EmailField(
        unique=True, 
        null=True, 
        blank=True,
        validators=[EmailValidator(message="Enter a valid email address.")]
    )
    
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,12}$', 
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone = models.CharField(
        validators=[phone_regex], 
        max_length=17, 
        unique=True, 
        null=True, 
        blank=True
    )
    
    password_hash = models.TextField(null=True, blank=True)
    otp = models.CharField(max_length=10, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    is_logged_in = models.BooleanField(default=False)
    profile_image_url = models.URLField(null=True, blank=True,max_length=500)
    last_login = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.role == 'SUPERADMIN':
            existing = Users.objects.filter(role='SUPERADMIN')
            if self.pk:
                existing = existing.exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError("There can be only one Super Admin.")
        super().save(*args, **kwargs)

    @property
    def is_authenticated(self):
        return True

    def __str__(self):
        return self.username
