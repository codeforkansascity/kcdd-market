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
    
    # User profiles
    path('profile/', views.profile, name='profile'),
    path('cbo/', views.cbo_profile, name='cbo_profile'),
    path('donor/', views.donor_profile, name='donor_profile'),
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    
    # AJAX endpoints
    path('api/claim/<uuid:request_id>/', views.claim_request, name='claim_request'),
    path('api/fulfill/<uuid:request_id>/', views.fulfill_request, name='fulfill_request'),
    
    # Future URL modules (when implemented)
    # path('organizations/', include('app.urls.organizations')),
    # path('donors/', include('app.urls.donors')),
]
