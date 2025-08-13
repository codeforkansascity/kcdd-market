from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
import uuid


class Request(models.Model):
    """Technology equipment requests from CBOs"""
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('claimed', 'Claimed'),
        ('fulfilled', 'Fulfilled'),
    ]
    
    URGENCY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relationships
    organization = models.ForeignKey('app.Organization', on_delete=models.CASCADE, related_name='requests')
    cause_area = models.ForeignKey('app.CauseArea', on_delete=models.PROTECT)
    donor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='claimed_requests')
    
    # Request Details
    description = models.TextField(help_text="What is needed and why?")
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text="Dollar amount requested"
    )
    urgency = models.CharField(max_length=10, choices=URGENCY_CHOICES, default='medium')
    
    # Geographic Information
    zipcode = models.CharField(max_length=10, help_text="ZIP code where assistance is needed")
    
    # Identity Categories (Many-to-Many)
    identity_categories = models.ManyToManyField('app.IdentityCategory', blank=True, help_text="Recipient identity tags")
    
    # Status and Workflow
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')
    donor_note = models.TextField(blank=True, help_text="Note from donor about fulfillment plan")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    claimed_at = models.DateTimeField(null=True, blank=True)
    fulfilled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.organization.name}: {self.description[:50]}..."

    def save(self, *args, **kwargs):
        # Auto-set timestamps based on status changes
        if self.status == 'claimed' and not self.claimed_at:
            self.claimed_at = timezone.now()
        elif self.status == 'fulfilled' and not self.fulfilled_at:
            self.fulfilled_at = timezone.now()
        super().save(*args, **kwargs)

    @property
    def is_open(self):
        return self.status == 'open'
    
    @property
    def is_claimed(self):
        return self.status == 'claimed'
    
    @property
    def is_fulfilled(self):
        return self.status == 'fulfilled'

    @property
    def urgency_badge_class(self):
        """CSS classes for urgency badges"""
        badges = {
            'low': 'bg-gray-100 text-gray-700',
            'medium': 'bg-yellow-100 text-yellow-800',
            'high': 'bg-red-100 text-red-700',
        }
        return badges.get(self.urgency, 'bg-gray-100 text-gray-700')


class RequestHistory(models.Model):
    """Track request status changes and actions"""
    
    ACTION_CHOICES = [
        ('created', 'Request Created'),
        ('claimed', 'Request Claimed'),
        ('fulfilled', 'Request Fulfilled'),
        ('updated', 'Request Updated'),
        ('note_added', 'Note Added'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name='history')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField(help_text="Description of the action taken")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = "Request histories"

    def __str__(self):
        return f"{self.request.id} - {self.get_action_display()}"


class FulfillmentRecord(models.Model):
    """Track fulfillment details"""
    
    FULFILLMENT_TYPES = [
        ('monetary', 'Monetary'),
        ('device', 'Device'),
    ]
    
    DEVICE_CONDITIONS = [
        ('new', 'New'),
        ('refurbished', 'Refurbished'),
        ('used_good', 'Used - Good'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request = models.OneToOneField(Request, on_delete=models.CASCADE, related_name='fulfillment')
    
    # Fulfillment Details
    fulfillment_type = models.CharField(max_length=10, choices=FULFILLMENT_TYPES)
    device_condition = models.CharField(max_length=15, choices=DEVICE_CONDITIONS, blank=True)
    
    # Satisfaction and Feedback
    donor_satisfied = models.BooleanField(default=True, help_text="Was donor satisfied with the process?")
    cbo_satisfied = models.BooleanField(default=True, help_text="Was CBO satisfied with the process?")
    
    # Notes
    donor_notes = models.TextField(blank=True, help_text="Donor feedback and notes")
    cbo_notes = models.TextField(blank=True, help_text="CBO feedback and notes")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Fulfillment for {self.request}"
