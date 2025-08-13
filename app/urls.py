"""
URL patterns for the main app
"""
from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

app_name = 'app'

urlpatterns = [
    # Home and public pages
    path('', views.home, name='home'),
    path('requests/', views.request_board, name='request_board'),
    path('requests/<uuid:request_id>/', views.request_detail, name='request_detail'),
    
    # User authentication
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='app:home'), name='logout'),
    
    # User profiles and dashboards
    path('profile/', views.profile, name='profile'),
    path('cbo/<str:username>/', views.cbo_public_profile, name='cbo_public_profile'),
    path('cbo-dashboard/', views.cbo_dashboard, name='cbo_dashboard'),
    path('donor/<str:username>/', views.donor_public_profile, name='donor_public_profile'),
    path('donor-dashboard/', views.donor_dashboard, name='donor_dashboard'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # Request management
    path('create-request/', views.create_request, name='create_request'),
    path('manage-requests/', views.manage_requests, name='manage_requests'),
    path('admin-create-request/', views.admin_create_request, name='admin_create_request'),
    
    # AJAX endpoints
    path('api/claim/<uuid:request_id>/', views.claim_request, name='claim_request'),
    path('api/fulfill/<uuid:request_id>/', views.fulfill_request, name='fulfill_request'),
    
    # Future URL modules (when implemented)
    # path('organizations/', include('app.urls.organizations')),
    # path('donors/', include('app.urls.donors')),
]
