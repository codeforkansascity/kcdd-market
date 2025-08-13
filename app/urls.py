"""
URL patterns for the main app
"""
from django.urls import path, include
from django.views.generic import TemplateView

app_name = 'app'

urlpatterns = [
    # Home page
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    
    # Dashboard
    path('dashboard/', TemplateView.as_view(template_name='dashboard.html'), name='dashboard'),
    
    # Include other URL modules when they're implemented
    # path('organizations/', include('app.urls.organizations')),
    # path('requests/', include('app.urls.requests')),
    # path('donors/', include('app.urls.donors')),
]
