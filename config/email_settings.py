"""
Email configuration for KCDD Matchmaking Portal

To enable AWS SES in production:

1. Install boto3:
   pip install boto3

2. Add to settings.py:
   from .email_settings import *

3. Set environment variables:
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   AWS_SES_REGION_NAME=us-east-1  # or your preferred region
   USE_AWS_SES=True

4. Verify your domain and email addresses in AWS SES console
"""

import os

# Email backend configuration
USE_AWS_SES = os.getenv('USE_AWS_SES', 'False').lower() == 'true'

if USE_AWS_SES:
    # AWS SES Configuration
    EMAIL_BACKEND = 'django_ses.SESBackend'
    
    # AWS Configuration
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_SES_REGION_NAME = os.getenv('AWS_SES_REGION_NAME', 'us-east-1')
    AWS_SES_REGION_ENDPOINT = f'email.{AWS_SES_REGION_NAME}.amazonaws.com'
    
    # Optional: Configuration set for tracking
    # AWS_SES_CONFIGURATION_SET = 'kcdd-emails'
    
    # Email settings
    DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@kcdd.org')
    SERVER_EMAIL = DEFAULT_FROM_EMAIL
    
    # Admin notification emails
    ADMIN_EMAILS = os.getenv('ADMIN_EMAILS', 'admin@kcdd.org').split(',')
    
else:
    # Development configuration - emails logged to console
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    DEFAULT_FROM_EMAIL = 'noreply@localhost'
    ADMIN_EMAILS = ['admin@localhost']

# Site URL for email links
SITE_URL = os.getenv('SITE_URL', 'http://localhost:8000')

# Email templates configuration
EMAIL_USE_TLS = True
EMAIL_PORT = 587

# For development file backend (alternative to console)
# EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
# EMAIL_FILE_PATH = 'emails/'
