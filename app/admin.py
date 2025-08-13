from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, CauseArea, IdentityCategory, Organization, 
    DonorProfile, Request, RequestHistory, FulfillmentRecord
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom user admin"""
    list_display = ('username', 'email', 'user_type', 'is_vetted', 'is_active', 'date_joined')
    list_filter = ('user_type', 'is_vetted', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Profile Information', {
            'fields': ('user_type', 'phone', 'is_vetted', 'vetting_note')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Profile Information', {
            'fields': ('user_type', 'phone', 'email')
        }),
    )


@admin.register(CauseArea)
class CauseAreaAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')


@admin.register(IdentityCategory)
class IdentityCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'zipcode', 'is_vetted', 'created_at')
    list_filter = ('cause_areas', 'user__is_vetted', 'created_at')
    search_fields = ('name', 'email', 'zipcode', 'ein')
    filter_horizontal = ('cause_areas',)
    
    def is_vetted(self, obj):
        return obj.is_vetted
    is_vetted.boolean = True
    is_vetted.short_description = 'Vetted'


@admin.register(DonorProfile)
class DonorProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'max_per_request', 'service_area_zipcode', 'is_vetted', 'created_at')
    list_filter = ('cause_areas', 'user__is_vetted', 'created_at')
    search_fields = ('name', 'email', 'service_area_zipcode')
    filter_horizontal = ('cause_areas',)
    
    def is_vetted(self, obj):
        return obj.is_vetted
    is_vetted.boolean = True
    is_vetted.short_description = 'Vetted'


@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'organization', 'amount', 'urgency', 'status', 'donor', 'created_at')
    list_filter = ('status', 'urgency', 'cause_area', 'created_at')
    search_fields = ('description', 'organization__name', 'zipcode')
    filter_horizontal = ('identity_categories',)
    readonly_fields = ('created_at', 'updated_at', 'claimed_at', 'fulfilled_at')


@admin.register(RequestHistory)
class RequestHistoryAdmin(admin.ModelAdmin):
    list_display = ('request', 'action', 'user', 'timestamp')
    list_filter = ('action', 'timestamp')
    search_fields = ('request__description', 'description')
    readonly_fields = ('timestamp',)


@admin.register(FulfillmentRecord)
class FulfillmentRecordAdmin(admin.ModelAdmin):
    list_display = ('request', 'fulfillment_type', 'donor_satisfied', 'cbo_satisfied', 'created_at')
    list_filter = ('fulfillment_type', 'device_condition', 'donor_satisfied', 'cbo_satisfied')
    readonly_fields = ('created_at', 'updated_at')
