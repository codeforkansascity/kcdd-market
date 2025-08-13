from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import User, Organization, DonorProfile, Request, CauseArea, IdentityCategory


class UserRegistrationForm(UserCreationForm):
    """Extended user registration form"""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    user_type = forms.ChoiceField(
        choices=[('cbo', 'Community-Based Organization'), ('donor', 'Donor')],
        required=True,
        widget=forms.RadioSelect,
        initial='cbo'
    )
    phone = forms.CharField(max_length=20, required=False)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'user_type', 'phone', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add CSS classes for styling
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-input mt-1 block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
        
        # Special styling for radio buttons
        self.fields['user_type'].widget.attrs['class'] = 'form-radio'

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.user_type = self.cleaned_data['user_type']
        user.phone = self.cleaned_data['phone']
        
        # CBOs need approval, donors are auto-approved
        if user.user_type == 'donor':
            user.is_vetted = True
            user.vetting_note = 'Auto-approved donor'
        else:
            user.is_vetted = False
            user.vetting_note = 'Under review by KCDD'
        
        if commit:
            user.save()
        return user


class OrganizationProfileForm(forms.ModelForm):
    """CBO organization profile form"""
    
    class Meta:
        model = Organization
        fields = [
            'name', 'website', 'mission', 'email', 'phone',
            'address', 'zipcode', 'ein', 'cause_areas', 'logo', 'logo_emoji'
        ]
        widgets = {
            'mission': forms.Textarea(attrs={'rows': 4}),
            'address': forms.Textarea(attrs={'rows': 3}),
            'cause_areas': forms.CheckboxSelectMultiple,
        }
        help_texts = {
            'logo': 'Upload your organization logo (PNG, JPG, GIF supported). Recommended size: 200x200px or larger.',
            'logo_emoji': 'Choose an emoji to represent your organization when no logo is uploaded (e.g., 🏫, 🏥, 🎯, 💚)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add CSS classes
        for field_name, field in self.fields.items():
            if field_name == 'cause_areas':
                field.widget.attrs['class'] = 'form-checkbox'
            elif field_name == 'logo':
                field.widget.attrs['class'] = 'form-input mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100'
                field.widget.attrs['accept'] = 'image/png,image/jpeg,image/gif'
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs['class'] = 'form-textarea mt-1 block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            else:
                field.widget.attrs['class'] = 'form-input mt-1 block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
    
    def clean_logo(self):
        logo = self.cleaned_data.get('logo')
        if logo:
            # Check file size (limit to 5MB)
            if logo.size > 5 * 1024 * 1024:
                raise forms.ValidationError("Logo file size cannot exceed 5MB.")
            
            # Check file type
            allowed_types = ['image/png', 'image/jpeg', 'image/gif']
            if logo.content_type not in allowed_types:
                raise forms.ValidationError("Logo must be a PNG, JPEG, or GIF image.")
        
        return logo


class DonorProfileForm(forms.ModelForm):
    """Donor profile form"""
    
    class Meta:
        model = DonorProfile
        fields = [
            'display_name', 'bio', 'profile_picture', 'name', 'email', 'phone', 
            'max_per_request', 'service_area_zipcode', 'cause_areas'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
            'cause_areas': forms.CheckboxSelectMultiple,
        }
        help_texts = {
            'profile_picture': 'Upload a profile picture (PNG, JPG, GIF supported). Recommended size: 200x200px or larger.',
            'display_name': 'The name that will be shown publicly when you claim requests.',
            'bio': 'Tell others about yourself, your interests, or why you donate (optional).',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add CSS classes
        for field_name, field in self.fields.items():
            if field_name == 'cause_areas':
                field.widget.attrs['class'] = 'form-checkbox'
            elif field_name == 'profile_picture':
                field.widget.attrs['class'] = 'form-input mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100'
                field.widget.attrs['accept'] = 'image/png,image/jpeg,image/gif'
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs['class'] = 'form-textarea mt-1 block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            else:
                field.widget.attrs['class'] = 'form-input mt-1 block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
    
    def clean_profile_picture(self):
        profile_picture = self.cleaned_data.get('profile_picture')
        if profile_picture:
            # Only validate uploaded files, not existing files
            if hasattr(profile_picture, 'content_type'):
                # Check file size (limit to 5MB)
                if profile_picture.size > 5 * 1024 * 1024:
                    raise forms.ValidationError("Profile picture file size cannot exceed 5MB.")
                
                # Check file type
                allowed_types = ['image/png', 'image/jpeg', 'image/gif']
                if profile_picture.content_type not in allowed_types:
                    raise forms.ValidationError("Profile picture must be a PNG, JPEG, or GIF image.")
        
        return profile_picture


class RequestForm(forms.ModelForm):
    """Request creation/editing form"""
    
    class Meta:
        model = Request
        fields = [
            'description', 'amount', 'urgency', 'cause_area',
            'zipcode', 'identity_categories'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'identity_categories': forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add CSS classes
        for field_name, field in self.fields.items():
            if field_name == 'identity_categories':
                field.widget.attrs['class'] = 'form-checkbox'
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs['class'] = 'form-textarea mt-1 block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            else:
                field.widget.attrs['class'] = 'form-input mt-1 block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'


class ClaimRequestForm(forms.Form):
    """Form for claiming a request"""
    donor_note = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4}),
        required=False,
        help_text="Share your fulfillment plan, timing, questions, etc. (optional)",
        label="Message to the CBO"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['donor_note'].widget.attrs['class'] = 'form-textarea mt-1 block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'


class FulfillmentForm(forms.Form):
    """Form for marking request as fulfilled"""
    fulfillment_type = forms.ChoiceField(
        choices=[('monetary', 'Monetary'), ('device', 'Device')],
        widget=forms.RadioSelect,
        required=True
    )
    device_condition = forms.ChoiceField(
        choices=[('new', 'New'), ('refurbished', 'Refurbished'), ('used_good', 'Used - Good')],
        required=False,
        help_text="Required if fulfillment type is Device"
    )
    satisfied = forms.ChoiceField(
        choices=[('yes', 'Yes'), ('no', 'No')],
        widget=forms.RadioSelect,
        required=True,
        label="Were you satisfied with the process?"
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        label="Notes / feedback"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add CSS classes
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.RadioSelect):
                field.widget.attrs['class'] = 'form-radio'
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs['class'] = 'form-textarea mt-1 block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            else:
                field.widget.attrs['class'] = 'form-input mt-1 block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'

    def clean(self):
        cleaned_data = super().clean()
        fulfillment_type = cleaned_data.get('fulfillment_type')
        device_condition = cleaned_data.get('device_condition')

        if fulfillment_type == 'device' and not device_condition:
            raise ValidationError('Device condition is required when fulfillment type is Device.')

        return cleaned_data


class RequestSearchForm(forms.Form):
    """Form for searching and filtering requests"""
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search organization, description, or ZIP...',
            'class': 'form-input mt-1 block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
        }),
        label='Search'
    )
    cause = forms.ModelChoiceField(
        queryset=CauseArea.objects.filter(is_active=True),
        required=False,
        empty_label="All Causes",
        widget=forms.Select(attrs={
            'class': 'form-select mt-1 block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
        })
    )
    status = forms.ChoiceField(
        choices=[('', 'All'), ('open', 'Open'), ('claimed', 'Claimed'), ('fulfilled', 'Fulfilled')],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select mt-1 block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
        })
    )
    sort = forms.ChoiceField(
        choices=[
            ('newest', 'Newest'),
            ('oldest', 'Oldest'),
            ('amount_asc', 'Amount ↑'),
            ('amount_desc', 'Amount ↓'),
            ('urgency', 'Urgency'),
        ],
        required=False,
        initial='newest',
        widget=forms.Select(attrs={
            'class': 'form-select mt-1 block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
        })
    )
