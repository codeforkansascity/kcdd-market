from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Sum, Count
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
    """User profile redirect based on user type"""
    user = request.user
    
    # Superusers should go to admin dashboard regardless of user_type
    if user.is_superuser or user.user_type == 'admin':
        return redirect('app:admin_dashboard')
    elif user.user_type == 'cbo':
        return redirect('app:cbo_dashboard')
    elif user.user_type == 'donor':
        return redirect('app:donor_dashboard')
    else:
        return redirect('app:home')


def cbo_public_profile(request, username):
    """Public CBO profile page"""
    try:
        cbo_user = User.objects.get(username=username, user_type='cbo')
        organization = cbo_user.organization
    except (User.DoesNotExist, Organization.DoesNotExist):
        messages.error(request, 'Organization not found.')
        return redirect('app:home')
    
    # Get CBO's public requests
    public_requests = Request.objects.filter(
        organization=organization, 
        status__in=['open', 'claimed']
    ).order_by('-created_at')
    
    context = {
        'organization': organization,
        'requests': public_requests,
        'is_public': True,
    }
    return render(request, 'cbo_public_profile.html', context)


@login_required
def cbo_dashboard(request):
    """CBO dashboard for managing profile and requests"""
    if request.user.user_type != 'cbo':
        messages.error(request, 'Access denied.')
        return redirect('app:home')
    
    try:
        organization = request.user.organization
    except Organization.DoesNotExist:
        # Create organization profile if it doesn't exist
        organization = Organization.objects.create(user=request.user)
    
    if request.method == 'POST':
        form = OrganizationProfileForm(request.POST, request.FILES, instance=organization)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('app:cbo_dashboard')
    else:
        form = OrganizationProfileForm(instance=organization)
    
    # Get CBO's requests
    cbo_requests = Request.objects.filter(organization=organization).order_by('-created_at')
    
    context = {
        'form': form,
        'organization': organization,
        'requests': cbo_requests,
        'is_dashboard': True,
    }
    return render(request, 'cbo_dashboard.html', context)


def donor_public_profile(request, username):
    """Public donor profile page"""
    try:
        donor_user = User.objects.get(username=username, user_type='donor')
        donor_profile = donor_user.donor_profile
    except (User.DoesNotExist, DonorProfile.DoesNotExist):
        messages.error(request, 'Donor not found.')
        return redirect('app:home')
    
    # Get donor's fulfilled requests (public)
    fulfilled_requests = Request.objects.filter(
        donor=donor_user, 
        status='fulfilled'
    ).order_by('-fulfilled_at')
    
    # Calculate total amount given
    total_given = sum(req.amount for req in fulfilled_requests) if fulfilled_requests else 0
    
    context = {
        'donor_profile': donor_profile,
        'fulfilled_requests': fulfilled_requests,
        'total_given': total_given,
        'is_public': True,
    }
    return render(request, 'donor_public_profile.html', context)


@login_required
def donor_dashboard(request):
    """Donor dashboard for managing profile and donations"""
    if request.user.user_type != 'donor':
        messages.error(request, 'Access denied.')
        return redirect('app:home')
    
    # Get or create donor profile
    try:
        donor_profile = request.user.donor_profile
    except DonorProfile.DoesNotExist:
        # Create donor profile if it doesn't exist
        donor_profile = DonorProfile.objects.create(user=request.user)
    
    if request.method == 'POST':
        form = DonorProfileForm(request.POST, request.FILES, instance=donor_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('app:donor_dashboard')
    else:
        form = DonorProfileForm(instance=donor_profile)
    
    # Get user's claimed and fulfilled requests
    claimed_requests = Request.objects.filter(donor=request.user, status='claimed').order_by('-claimed_at')
    fulfilled_requests = Request.objects.filter(donor=request.user, status='fulfilled').order_by('-fulfilled_at')
    
    # Calculate total amount given
    total_given = sum(req.amount for req in fulfilled_requests) if fulfilled_requests else 0
    
    context = {
        'form': form,
        'donor_profile': donor_profile,
        'claimed_requests': claimed_requests,
        'fulfilled_requests': fulfilled_requests,
        'total_given': total_given,
        'is_dashboard': True,
    }
    return render(request, 'donor_dashboard.html', context)


@login_required
def admin_dashboard(request):
    """Admin dashboard for oversight"""
    if not request.user.is_admin_user:
        messages.error(request, 'Access denied.')
        return redirect('app:home')
    
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
    import json
    from django.shortcuts import get_object_or_404
    from django.utils import timezone
    from .models import Request, RequestHistory
    
    if request.user.user_type != 'donor':
        return JsonResponse({'error': 'Only donors can claim requests'}, status=403)
    
    if not request.user.is_vetted:
        return JsonResponse({'error': 'Only vetted donors can claim requests'}, status=403)
    
    try:
        request_obj = get_object_or_404(Request, id=request_id)
        
        # Check if request is available
        if request_obj.status != 'open':
            return JsonResponse({'error': 'This request is no longer available'}, status=400)
        
        # Parse request body for donor note
        try:
            data = json.loads(request.body)
            donor_note = data.get('donor_note', '').strip()
        except (json.JSONDecodeError, AttributeError):
            donor_note = ''
        
        # Update request
        request_obj.status = 'claimed'
        request_obj.donor = request.user
        request_obj.donor_note = donor_note
        request_obj.claimed_at = timezone.now()
        request_obj.save()
        
        # Create history record
        RequestHistory.objects.create(
            request=request_obj,
            user=request.user,
            action='claimed',
            description=f"Request claimed by {request.user.get_full_name() or request.user.username}"
        )
        
        # Send notification email
        try:
            send_request_claimed_email(request_obj, request.user)
        except Exception as e:
            # Log the error but don't fail the claim
            print(f"Failed to send claim notification email: {e}")
        
        return JsonResponse({
            'success': True, 
            'message': 'Request claimed successfully',
            'claimed_at': request_obj.claimed_at.isoformat()
        })
        
    except Exception as e:
        return JsonResponse({'error': f'Failed to claim request: {str(e)}'}, status=500)


@require_POST
@login_required
def fulfill_request(request, request_id):
    """Mark request as fulfilled"""
    from django.shortcuts import get_object_or_404
    from django.utils import timezone
    from .models import Request, RequestHistory, FulfillmentRecord
    
    try:
        request_obj = get_object_or_404(Request, id=request_id)
        
        # Check permissions
        if request_obj.donor != request.user and not request.user.is_admin_user:
            return JsonResponse({'error': 'Only the claiming donor can mark as fulfilled'}, status=403)
        
        # Check if request is in claimed status
        if request_obj.status != 'claimed':
            return JsonResponse({'error': 'Request must be claimed before it can be fulfilled'}, status=400)
        
        # Update request
        request_obj.status = 'fulfilled'
        request_obj.fulfilled_at = timezone.now()
        request_obj.save()
        
        # Create fulfillment record
        FulfillmentRecord.objects.create(
            request=request_obj,
            fulfillment_type='monetary',  # Default, can be updated later
            donor_satisfied=True,
            cbo_satisfied=True
        )
        
        # Create history record
        RequestHistory.objects.create(
            request=request_obj,
            user=request.user,
            action='fulfilled',
            description=f"Request fulfilled by {request.user.get_full_name() or request.user.username}"
        )
        
        # TODO: Send fulfillment notification emails
        
        return JsonResponse({
            'success': True, 
            'message': 'Request marked as fulfilled successfully',
            'fulfilled_at': request_obj.fulfilled_at.isoformat()
        })
        
    except Exception as e:
        return JsonResponse({'error': f'Failed to fulfill request: {str(e)}'}, status=500)


@require_POST
@login_required
def unclaim_request(request, request_id):
    """Release a claimed request (for donors who claimed it)"""
    from django.shortcuts import get_object_or_404
    from .models import Request, RequestHistory
    
    try:
        request_obj = get_object_or_404(Request, id=request_id)
        
        # Check permissions
        if request_obj.donor != request.user and not request.user.is_admin_user:
            return JsonResponse({'error': 'Only the claiming donor can release this claim'}, status=403)
        
        # Check if request is in claimed status
        if request_obj.status != 'claimed':
            return JsonResponse({'error': 'Request is not currently claimed'}, status=400)
        
        # Store donor info for history
        donor_name = request_obj.donor.get_full_name() or request_obj.donor.username
        
        # Reset request to open status
        request_obj.status = 'open'
        request_obj.donor = None
        request_obj.donor_note = ''
        request_obj.claimed_at = None
        request_obj.save()
        
        # Create history record
        RequestHistory.objects.create(
            request=request_obj,
            user=request.user,
            action='updated',
            description=f"Claim released by {donor_name} - request is now available again"
        )
        
        return JsonResponse({
            'success': True, 
            'message': 'Claim released successfully'
        })
        
    except Exception as e:
        return JsonResponse({'error': f'Failed to release claim: {str(e)}'}, status=500)


def donor_leaderboard(request):
    """Display top donors leaderboard"""
    
    # Get top donors by number of fulfilled requests
    top_donors_by_count = User.objects.filter(
        user_type='donor',
        is_vetted=True,
        claimed_requests__status='fulfilled',
        donor_profile__isnull=False  # Ensure they have a profile
    ).annotate(
        fulfilled_count=Count('claimed_requests', filter=models.Q(claimed_requests__status='fulfilled')),
        total_donated=Sum('claimed_requests__amount', filter=models.Q(claimed_requests__status='fulfilled'))
    ).order_by('-fulfilled_count', '-total_donated')[:10]
    
    # Get top donors by total amount donated
    top_donors_by_amount = User.objects.filter(
        user_type='donor',
        is_vetted=True,
        claimed_requests__status='fulfilled',
        donor_profile__isnull=False  # Ensure they have a profile
    ).annotate(
        fulfilled_count=Count('claimed_requests', filter=models.Q(claimed_requests__status='fulfilled')),
        total_donated=Sum('claimed_requests__amount', filter=models.Q(claimed_requests__status='fulfilled'))
    ).order_by('-total_donated', '-fulfilled_count')[:10]
    
    # Get overall stats
    total_donors = User.objects.filter(user_type='donor', is_vetted=True).count()
    total_fulfilled = User.objects.filter(
        user_type='donor',
        claimed_requests__status='fulfilled'
    ).aggregate(
        count=Count('claimed_requests', filter=models.Q(claimed_requests__status='fulfilled'))
    )['count'] or 0
    
    total_amount = User.objects.filter(
        user_type='donor',
        claimed_requests__status='fulfilled'
    ).aggregate(
        amount=Sum('claimed_requests__amount', filter=models.Q(claimed_requests__status='fulfilled'))
    )['amount'] or 0
    
    context = {
        'top_donors_by_count': top_donors_by_count,
        'top_donors_by_amount': top_donors_by_amount,
        'total_donors': total_donors,
        'total_fulfilled': total_fulfilled,
        'total_amount': total_amount,
    }
    
    return render(request, 'donor_leaderboard.html', context)


def request_detail(request, request_id):
    """Request detail view"""
    from django.shortcuts import get_object_or_404
    from .models import Request
    
    request_obj = get_object_or_404(Request, id=request_id)
    
    # Get related requests (same cause area, different organization)
    related_requests = Request.objects.filter(
        cause_area=request_obj.cause_area,
        status='open'
    ).exclude(id=request_obj.id)[:3]
    
    context = {
        'request_obj': request_obj,
        'related_requests': related_requests,
    }
    return render(request, 'request_detail.html', context)


@login_required
def create_request(request):
    """Create a new request (CBOs only)"""
    if request.user.user_type != 'cbo':
        messages.error(request, 'Only Community-Based Organizations can create requests.')
        return redirect('app:home')
    
    # Ensure user has an organization profile
    try:
        organization = request.user.organization
    except Organization.DoesNotExist:
        messages.error(request, 'Please complete your organization profile first.')
        return redirect('app:cbo_dashboard')
    
    if not request.user.is_vetted:
        messages.error(request, 'Your organization must be approved before creating requests.')
        return redirect('app:cbo_dashboard')
    
    if request.method == 'POST':
        form = RequestForm(request.POST, request.FILES)
        if form.is_valid():
            new_request = form.save(commit=False)
            new_request.organization = organization
            new_request.save()
            form.save_m2m()  # Save many-to-many relationships
            messages.success(request, 'Request created successfully!')
            return redirect('app:cbo_dashboard')
    else:
        form = RequestForm()
    
    context = {
        'form': form,
        'organization': organization,
    }
    return render(request, 'create_request.html', context)


@login_required
def edit_request(request, request_id):
    """Edit a request (CBOs only, open requests only)"""
    from django.shortcuts import get_object_or_404
    from .models import Request
    
    if request.user.user_type != 'cbo':
        messages.error(request, 'Only Community-Based Organizations can edit requests.')
        return redirect('app:home')
    
    # Get the request and verify ownership
    request_obj = get_object_or_404(Request, id=request_id, organization__user=request.user)
    
    # Only allow editing of open requests
    if request_obj.status != 'open':
        messages.error(request, 'You can only edit open requests that have not been claimed.')
        return redirect('app:cbo_dashboard')
    
    if request.method == 'POST':
        form = RequestForm(request.POST, instance=request_obj)
        if form.is_valid():
            updated_request = form.save()
            
            # Create history record
            RequestHistory.objects.create(
                request=updated_request,
                user=request.user,
                action='updated',
                description=f"Request updated by {request.user.get_full_name() or request.user.username}"
            )
            
            messages.success(request, 'Request updated successfully!')
            return redirect('app:cbo_dashboard')
    else:
        form = RequestForm(instance=request_obj)
    
    context = {
        'form': form,
        'request_obj': request_obj,
        'is_edit': True,
    }
    return render(request, 'edit_request.html', context)


@login_required  
def delete_request(request, request_id):
    """Delete a request (CBOs only, open requests only)"""
    from django.shortcuts import get_object_or_404
    from django.views.decorators.http import require_http_methods
    from .models import Request
    
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    if request.user.user_type != 'cbo':
        return JsonResponse({'error': 'Only Community-Based Organizations can delete requests'}, status=403)
    
    try:
        request_obj = get_object_or_404(Request, id=request_id, organization__user=request.user)
        
        # Only allow deletion of open requests
        if request_obj.status != 'open':
            return JsonResponse({'error': 'You can only delete open requests that have not been claimed'}, status=400)
        
        # Create history record before deletion
        RequestHistory.objects.create(
            request=request_obj,
            user=request.user,
            action='updated',
            description=f"Request deleted by {request.user.get_full_name() or request.user.username}"
        )
        
        request_obj.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Request deleted successfully'
        })
        
    except Exception as e:
        return JsonResponse({'error': f'Failed to delete request: {str(e)}'}, status=500)


@login_required
def manage_requests(request):
    """Admin view for managing all requests"""
    if not request.user.is_admin_user:
        messages.error(request, 'Access denied.')
        return redirect('app:home')
    
    # Handle request status updates
    if request.method == 'POST':
        action = request.POST.get('action')
        request_id = request.POST.get('request_id')
        
        if action and request_id:
            try:
                req_obj = Request.objects.get(id=request_id)
                if action == 'approve':
                    req_obj.status = 'open'
                    req_obj.save()
                    messages.success(request, f'Request "{req_obj.title}" approved')
                elif action == 'reject':
                    req_obj.status = 'rejected'
                    req_obj.save()
                    messages.warning(request, f'Request "{req_obj.title}" rejected')
                elif action == 'delete':
                    title = req_obj.title
                    req_obj.delete()
                    messages.warning(request, f'Request "{title}" deleted')
            except Request.DoesNotExist:
                messages.error(request, 'Request not found')
        
        return redirect('app:manage_requests')
    
    # Get all requests with filtering
    status_filter = request.GET.get('status', 'all')
    search_query = request.GET.get('search', '')
    
    requests_queryset = Request.objects.select_related('organization', 'donor').order_by('-created_at')
    
    if status_filter != 'all':
        requests_queryset = requests_queryset.filter(status=status_filter)
    
    if search_query:
        requests_queryset = requests_queryset.filter(
            Q(title__icontains=search_query) |
            Q(organization__name__icontains=search_query)
        )
    
    context = {
        'requests': requests_queryset,
        'status_filter': status_filter,
        'search_query': search_query,
        'status_choices': Request.STATUS_CHOICES,
    }
    return render(request, 'manage_requests.html', context)


@login_required
def admin_create_request(request):
    """Admin view for creating requests on behalf of organizations"""
    if not request.user.is_admin_user:
        messages.error(request, 'Access denied.')
        return redirect('app:home')
    
    if request.method == 'POST':
        form = RequestForm(request.POST, request.FILES)
        organization_id = request.POST.get('organization')
        
        if form.is_valid() and organization_id:
            try:
                organization = Organization.objects.get(id=organization_id)
                new_request = form.save(commit=False)
                new_request.organization = organization
                new_request.save()
                form.save_m2m()  # Save many-to-many relationships
                messages.success(request, f'Request created for {organization.name}!')
                return redirect('app:manage_requests')
            except Organization.DoesNotExist:
                messages.error(request, 'Selected organization not found.')
        else:
            if not organization_id:
                messages.error(request, 'Please select an organization.')
            if not form.is_valid():
                messages.error(request, f'Form validation failed: {form.errors}')
    else:
        form = RequestForm()
    
    # Get all approved organizations
    organizations = Organization.objects.filter(user__is_vetted=True).select_related('user')
    
    context = {
        'form': form,
        'organizations': organizations,
        'is_admin_create': True,
    }
    return render(request, 'admin_create_request.html', context)


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


def custom_logout(request):
    """Custom logout view that ensures proper redirection to home page"""
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('app:home')
