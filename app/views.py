from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Sum
from django.db import models
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.utils import timezone
import json

from .models import User, Organization, DonorProfile, Request, CauseArea, IdentityCategory, RequestHistory
from .forms import (
    UserRegistrationForm, OrganizationProfileForm, DonorProfileForm, 
    RequestForm, ClaimRequestForm, FulfillmentForm, RequestSearchForm
)
from .services import send_cbo_approval_email, send_welcome_email, send_request_claimed_email


def home(request):
    """Public homepage with request board"""
    # Get recent open requests for preview
    recent_requests = Request.objects.filter(status='open').order_by('-created_at')[:3]
    
    # Basic stats
    stats = {
        'open_requests': Request.objects.filter(status='open').count(),
        'fulfilled_requests': Request.objects.filter(status='fulfilled').count(),
        'total_cbos': Organization.objects.filter(user__is_vetted=True).count(),
        'total_impact': Request.objects.filter(status='fulfilled').aggregate(
            total=Sum('amount'))['total'] or 0,
    }
    
    context = {
        'title': 'KCDD Matchmaking Portal',
        'requests': recent_requests,
        'stats': stats,
    }
    return render(request, 'home.html', context)


def request_board(request):
    """Public request board with search/filter"""
    form = RequestSearchForm(request.GET)
    
    # Base queryset
    requests_queryset = Request.objects.all()
    
    if form.is_valid():
        # Apply filters
        if form.cleaned_data.get('q'):
            query = form.cleaned_data['q']
            requests_queryset = requests_queryset.filter(
                Q(organization__name__icontains=query) |
                Q(description__icontains=query) |
                Q(zipcode__icontains=query)
            )
        
        if form.cleaned_data.get('cause'):
            requests_queryset = requests_queryset.filter(cause_area=form.cleaned_data['cause'])
        
        if form.cleaned_data.get('status'):
            requests_queryset = requests_queryset.filter(status=form.cleaned_data['status'])
        else:
            # Default to open requests only
            requests_queryset = requests_queryset.filter(status='open')
        
        # Apply sorting
        sort_by = form.cleaned_data.get('sort', 'newest')
        if sort_by == 'oldest':
            requests_queryset = requests_queryset.order_by('created_at')
        elif sort_by == 'amount_asc':
            requests_queryset = requests_queryset.order_by('amount')
        elif sort_by == 'amount_desc':
            requests_queryset = requests_queryset.order_by('-amount')
        elif sort_by == 'urgency':
            # Custom ordering: high, medium, low
            requests_queryset = requests_queryset.extra(
                select={'urgency_order': "CASE WHEN urgency='high' THEN 1 WHEN urgency='medium' THEN 2 ELSE 3 END"}
            ).order_by('urgency_order', '-created_at')
        else:  # newest
            requests_queryset = requests_queryset.order_by('-created_at')
    else:
        # Default view: open requests, newest first
        requests_queryset = requests_queryset.filter(status='open').order_by('-created_at')
    
    # Pagination
    paginator = Paginator(requests_queryset, 12)  # 12 requests per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'form': form,
        'page_obj': page_obj,
        'requests': page_obj.object_list,
    }
    return render(request, 'request_board.html', context)


@login_required
def profile(request):
    """User profile based on user type"""
    user = request.user
    
    if user.user_type == 'cbo':
        return cbo_profile(request)
    elif user.user_type == 'donor':
        return donor_profile(request)
    elif user.user_type == 'admin':
        return admin_dashboard(request)
    else:
        return redirect('home')


@login_required
def cbo_profile(request):
    """CBO profile and request management"""
    if not request.user.is_cbo:
        messages.error(request, 'Access denied.')
        return redirect('app:home')
    
    # Get or create organization profile
    try:
        organization = request.user.organization
    except Organization.DoesNotExist:
        organization = None
    
    # Get user's requests
    requests = Request.objects.filter(organization__user=request.user).order_by('-created_at') if organization else []
    
    context = {
        'user': request.user,
        'organization': organization,
        'requests': requests,
    }
    return render(request, 'cbo_profile.html', context)


@login_required
def donor_profile(request):
    """Donor profile and claimed requests"""
    if not request.user.is_donor:
        messages.error(request, 'Access denied.')
        return redirect('app:home')
    
    # Get or create donor profile
    try:
        donor_profile = request.user.donor_profile
    except DonorProfile.DoesNotExist:
        donor_profile = None
    
    # Get user's claimed and fulfilled requests
    claimed_requests = Request.objects.filter(donor=request.user, status='claimed').order_by('-claimed_at')
    fulfilled_requests = Request.objects.filter(donor=request.user, status='fulfilled').order_by('-fulfilled_at')
    
    context = {
        'user': request.user,
        'donor_profile': donor_profile,
        'claimed_requests': claimed_requests,
        'fulfilled_requests': fulfilled_requests,
    }
    return render(request, 'donor_profile.html', context)


@login_required
def admin_dashboard(request):
    """Admin dashboard for oversight"""
    if not request.user.is_admin_user:
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    # Handle CBO approval/rejection
    if request.method == 'POST':
        action = request.POST.get('action')
        cbo_id = request.POST.get('cbo_id')
        
        if action and cbo_id:
            try:
                cbo_user = User.objects.get(id=cbo_id, user_type='cbo')
                if action == 'approve':
                    cbo_user.is_vetted = True
                    cbo_user.vetting_note = f'Approved by {request.user.username} on {timezone.now().strftime("%Y-%m-%d")}'
                    cbo_user.save()
                    messages.success(request, f'Approved {cbo_user.username}')
                    
                    # Send approval email
                    send_cbo_approval_email(cbo_user)
                elif action == 'reject':
                    cbo_user.is_vetted = False
                    cbo_user.vetting_note = f'Rejected by {request.user.username} on {timezone.now().strftime("%Y-%m-%d")}'
                    cbo_user.save()
                    messages.warning(request, f'Rejected {cbo_user.username}')
            except User.DoesNotExist:
                messages.error(request, 'CBO not found')
        
        return redirect('app:admin_dashboard')
    
    # Analytics and stats
    total_requests = Request.objects.count()
    open_requests = Request.objects.filter(status='open').count()
    claimed_requests = Request.objects.filter(status='claimed').count()
    fulfilled_requests = Request.objects.filter(status='fulfilled').count()
    pending_cbos = User.objects.filter(user_type='cbo', is_vetted=False).count()
    total_impact = Request.objects.filter(status='fulfilled').aggregate(total=Sum('amount'))['total'] or 0
    
    # Recent activity
    recent_requests = Request.objects.order_by('-created_at')[:10]
    pending_cbo_users = User.objects.filter(user_type='cbo', is_vetted=False).order_by('-date_joined')
    all_organizations = Organization.objects.select_related('user').order_by('-created_at')[:10]
    all_donors = DonorProfile.objects.select_related('user').order_by('-created_at')[:10]
    
    context = {
        'total_requests': total_requests,
        'open_requests': open_requests,
        'claimed_requests': claimed_requests,
        'fulfilled_requests': fulfilled_requests,
        'pending_cbos': pending_cbos,
        'total_impact': total_impact,
        'recent_requests': recent_requests,
        'pending_cbo_users': pending_cbo_users,
        'organizations': all_organizations,
        'donors': all_donors,
    }
    return render(request, 'admin_dashboard.html', context)


def register(request):
    """User registration"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Send welcome email
            send_welcome_email(user)
            
            # Auto-login for donors
            if user.user_type == 'donor':
                login(request, user)
                messages.success(request, 'Welcome! Your donor account is ready to use.')
                return redirect('app:profile')
            else:
                # CBOs need to complete their profile
                messages.success(request, 
                    'Account created! Please complete your organization profile. '
                    'KCDD will review and approve your account.')
                return redirect('app:login')
    else:
        form = UserRegistrationForm()
    
    context = {
        'form': form,
    }
    return render(request, 'registration/register.html', context)


@require_POST
@login_required
def claim_request(request, request_id):
    """Claim a request (for donors)"""
    if request.user.user_type != 'donor':
        return JsonResponse({'error': 'Only donors can claim requests'}, status=403)
    
    # Will implement after migrations
    return JsonResponse({'success': True, 'message': 'Request claimed successfully'})


@require_POST
@login_required
def fulfill_request(request, request_id):
    """Mark request as fulfilled"""
    # Will implement after migrations
    return JsonResponse({'success': True, 'message': 'Request marked as fulfilled'})


def request_detail(request, request_id):
    """Request detail view"""
    # Will implement after migrations
    context = {
        'request_obj': None,  # get_object_or_404(Request, id=request_id)
    }
    return render(request, 'request_detail.html', context)


# Email notification functions (mocked for now)
def send_claim_notification(request_obj, donor):
    """Send email when request is claimed"""
    # Mock implementation - will integrate with AWS SES later
    print(f"MOCK EMAIL: Request {request_obj.id} claimed by {donor.email}")
    print(f"TO: {request_obj.organization.email}")
    print(f"SUBJECT: Your request has been claimed!")
    return True


def send_fulfillment_notification(request_obj):
    """Send email when request is fulfilled"""
    # Mock implementation
    print(f"MOCK EMAIL: Request {request_obj.id} fulfilled")
    return True


def send_vetting_notification(user):
    """Send email when user is vetted"""
    # Mock implementation
    print(f"MOCK EMAIL: User {user.email} has been approved")
    return True
