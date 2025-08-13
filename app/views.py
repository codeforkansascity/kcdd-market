from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
import json

# Import our models (will be available after migrations)
# from .models import User, Organization, DonorProfile, Request, CauseArea, IdentityCategory


def home(request):
    """Public homepage with request board"""
    context = {
        'title': 'KCDD Matchmaking Portal',
        'requests': [],  # Will populate after migrations
    }
    return render(request, 'home.html', context)


def request_board(request):
    """Public request board with search/filter"""
    # Get filter parameters
    search_query = request.GET.get('q', '')
    cause_filter = request.GET.get('cause', '')
    status_filter = request.GET.get('status', 'open')
    sort_by = request.GET.get('sort', 'newest')
    
    # Base queryset (will implement after migrations)
    requests_queryset = []  # Request.objects.filter(status='open')
    
    context = {
        'requests': requests_queryset,
        'search_query': search_query,
        'cause_filter': cause_filter,
        'status_filter': status_filter,
        'sort_by': sort_by,
        'cause_areas': [],  # CauseArea.objects.filter(is_active=True)
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
    # Will implement after migrations
    context = {
        'user': request.user,
        'organization': None,  # request.user.organization
        'requests': [],  # request.user.organization.requests.all()
    }
    return render(request, 'cbo_profile.html', context)


@login_required
def donor_profile(request):
    """Donor profile and claimed requests"""
    # Will implement after migrations
    context = {
        'user': request.user,
        'donor_profile': None,  # request.user.donor_profile
        'claimed_requests': [],  # request.user.claimed_requests.filter(status='claimed')
        'fulfilled_requests': [],  # request.user.claimed_requests.filter(status='fulfilled')
    }
    return render(request, 'donor_profile.html', context)


@login_required
def admin_dashboard(request):
    """Admin dashboard for oversight"""
    if not request.user.is_admin_user:
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    # Will implement after migrations
    context = {
        'total_requests': 0,
        'open_requests': 0,
        'claimed_requests': 0,
        'fulfilled_requests': 0,
        'pending_cbos': 0,
        'requests': [],
        'organizations': [],
        'donors': [],
    }
    return render(request, 'admin_dashboard.html', context)


def register(request):
    """User registration"""
    if request.method == 'POST':
        # Will implement form handling after migrations
        pass
    
    context = {
        'user_types': [
            ('donor', 'Donor'),
            ('cbo', 'Community-Based Organization'),
        ]
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
