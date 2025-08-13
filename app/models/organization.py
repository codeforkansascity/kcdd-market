from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator
import uuid


class Organization(models.Model):
    """CBO organization profiles"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='organization')
    
    # Basic Information
    name = models.CharField(max_length=200)
    website = models.URLField(blank=True)
    mission = models.TextField(help_text="Organization mission/description")
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    
    # Address Information
    address = models.TextField(blank=True)
    zipcode = models.CharField(
        max_length=10, 
        validators=[RegexValidator(r'^\d{5}(-\d{4})?$', 'Enter a valid ZIP code')]
    )
    
    # Legal/Organizational Details
    ein = models.CharField(
        max_length=12, 
        blank=True,
        validators=[RegexValidator(r'^\d{2}-\d{7}$', 'Enter EIN in format: 12-3456789')],
        help_text="Tax ID in format: 12-3456789"
    )
    
    # Logo/Branding
    logo = models.ImageField(upload_to='org_logos/', blank=True, null=True)
    logo_emoji = models.CharField(max_length=10, blank=True, help_text="Emoji as fallback logo")
    
    # Cause Areas (Many-to-Many)
    cause_areas = models.ManyToManyField('app.CauseArea', blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def is_vetted(self):
        return self.user.is_vetted

    @property
    def display_logo(self):
        """Return emoji for text display (used in cards/lists)"""
        return self.logo_emoji or "🏢"
    
    @property
    def logo_display(self):
        """Return emoji fallback for display consistency"""
        return self.logo_emoji or "🏢"


class DonorProfile(models.Model):
    """Donor profiles"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='donor_profile')
    
    # Contact Information
    name = models.CharField(max_length=200, help_text="Individual or organization name")
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    
    # Giving Preferences
    max_per_request = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        help_text="Maximum amount willing to give per request"
    )
    
    # Geographic Preference
    service_area_zipcode = models.CharField(
        max_length=10, 
        blank=True,
        validators=[RegexValidator(r'^\d{5}(-\d{4})?$', 'Enter a valid ZIP code')],
        help_text="Preferred geographic area to serve"
    )
    
    # Cause Areas (Many-to-Many)
    cause_areas = models.ManyToManyField('app.CauseArea', blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def is_vetted(self):
        return self.user.is_vetted
