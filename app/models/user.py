from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator
import uuid


class User(AbstractUser):
    """Extended user model with profile types"""
    USER_TYPES = [
        ('admin', 'Admin'),
        ('cbo', 'Community-Based Organization'),
        ('donor', 'Donor'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='donor')
    phone = models.CharField(max_length=20, blank=True)
    is_vetted = models.BooleanField(default=False)
    vetting_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"

    @property
    def is_cbo(self):
        return self.user_type == 'cbo'
    
    @property
    def is_donor(self):
        return self.user_type == 'donor'
    
    @property
    def is_admin_user(self):
        return self.user_type == 'admin' or self.is_superuser


class CauseArea(models.Model):
    """Standardized cause areas for organizations and donors"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class IdentityCategory(models.Model):
    """Identity categories for request recipients"""
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = "Identity categories"

    def __str__(self):
        return self.name
