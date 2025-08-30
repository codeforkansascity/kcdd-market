"""
Email and notification services for the KCDD Matchmaking Portal

This module provides email functionality with easy AWS SES integration.
Currently uses console/file logging for development, with clear path to production.
"""

import logging
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from typing import Optional, List

logger = logging.getLogger(__name__)


class EmailService:
    """
    Email service that supports both development mocking and production AWS SES
    """
    
    def __init__(self):
        self.from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@kcdd.org')
        self.is_production = getattr(settings, 'USE_AWS_SES', False)
    
    def send_email(self, 
                   to_emails: List[str], 
                   subject: str, 
                   template_name: str, 
                   context: dict, 
                   cc_emails: Optional[List[str]] = None,
                   bcc_emails: Optional[List[str]] = None) -> bool:
        """
        Send an email using template rendering
        
        Args:
            to_emails: List of recipient email addresses
            subject: Email subject line
            template_name: Template path (without .html)
            context: Template context dictionary
            cc_emails: Optional CC recipients
            bcc_emails: Optional BCC recipients
            
        Returns:
            bool: True if email sent successfully
        """
        try:
            # Render HTML and text versions
            html_template = f"emails/{template_name}.html"
            text_template = f"emails/{template_name}.txt"
            
            html_content = render_to_string(html_template, context)
            text_content = render_to_string(text_template, context)
            
            # In development, just log the email
            if not self.is_production:
                self._log_email(to_emails, subject, text_content, html_content)
                return True
            
            # In production, send via Django's email backend (configured for AWS SES)
            success = send_mail(
                subject=subject,
                message=text_content,
                html_message=html_content,
                from_email=self.from_email,
                recipient_list=to_emails,
                fail_silently=False
            )
            
            logger.info(f"Email sent successfully to {to_emails}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_emails}: {str(e)}")
            return False
    
    def _log_email(self, to_emails: List[str], subject: str, text_content: str, html_content: str):
        """Log email content for development"""
        print("\n" + "="*80)
        print("📧 MOCK EMAIL SENT")
        print("="*80)
        print(f"TO: {', '.join(to_emails)}")
        print(f"FROM: {self.from_email}")
        print(f"SUBJECT: {subject}")
        print("-"*80)
        print(text_content)
        print("="*80 + "\n")
        
        # Also log to file for debugging
        logger.info(f"MOCK EMAIL - TO: {to_emails}, SUBJECT: {subject}")


# Global email service instance
email_service = EmailService()


# Convenience functions for specific email types
def send_cbo_approval_email(user):
    """Send approval email to CBO"""
    context = {
        'user': user,
        'organization': getattr(user, 'organization', None),
        'portal_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
    }
    
    return email_service.send_email(
        to_emails=[user.email],
        subject="Your KCDD Account Has Been Approved!",
        template_name="cbo_approval",
        context=context
    )


def send_cbo_rejection_email(user, reason=""):
    """Send rejection email to CBO"""
    context = {
        'user': user,
        'reason': reason,
        'portal_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
    }
    
    return email_service.send_email(
        to_emails=[user.email],
        subject="KCDD Account Application Update",
        template_name="cbo_rejection",
        context=context
    )


def send_request_claimed_email(request_obj, donor):
    """Send notification when request is claimed"""
    context = {
        'request': request_obj,
        'organization': request_obj.organization,
        'donor': donor,
        'donor_profile': getattr(donor, 'donor_profile', None),
        'portal_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
    }
    
    # Email to CBO
    cbo_success = email_service.send_email(
        to_emails=[request_obj.organization.email],
        subject=f"Your Request Has Been Claimed - ${request_obj.amount}",
        template_name="request_claimed_cbo",
        context=context
    )
    
    # Email to Donor
    donor_success = email_service.send_email(
        to_emails=[donor.email],
        subject=f"Request Claimed Successfully - {request_obj.organization.name}",
        template_name="request_claimed_donor",
        context=context
    )
    
    return cbo_success and donor_success


def send_request_fulfilled_email(request_obj, fulfillment_record):
    """Send notification when request is fulfilled"""
    context = {
        'request': request_obj,
        'organization': request_obj.organization,
        'donor': request_obj.donor,
        'fulfillment': fulfillment_record,
        'portal_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
    }
    
    # Email to CBO
    cbo_success = email_service.send_email(
        to_emails=[request_obj.organization.email],
        subject=f"Request Fulfilled - ${request_obj.amount}",
        template_name="request_fulfilled_cbo",
        context=context
    )
    
    # Email to Donor
    donor_success = email_service.send_email(
        to_emails=[request_obj.donor.email],
        subject=f"Thank You for Your Contribution - {request_obj.organization.name}",
        template_name="request_fulfilled_donor",
        context=context
    )
    
    return cbo_success and donor_success


def send_welcome_email(user):
    """Send welcome email to new users"""
    context = {
        'user': user,
        'portal_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
    }
    
    if user.user_type == 'donor':
        template_name = "welcome_donor"
        subject = "Welcome to KCDD Matchmaking Portal!"
    else:
        template_name = "welcome_cbo"
        subject = "Welcome to KCDD - Account Under Review"
    
    return email_service.send_email(
        to_emails=[user.email],
        subject=subject,
        template_name=template_name,
        context=context
    )


def send_admin_notification(subject: str, message: str, admin_emails: Optional[List[str]] = None):
    """Send notification to admins"""
    if not admin_emails:
        # Default admin emails from settings
        admin_emails = getattr(settings, 'ADMIN_EMAILS', ['admin@kcdd.org'])
    
    context = {
        'message': message,
        'portal_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
    }
    
    return email_service.send_email(
        to_emails=admin_emails,
        subject=f"KCDD Portal: {subject}",
        template_name="admin_notification",
        context=context
    )


def send_request_denial_email(request_obj, reason=""):
    """Send denial notification email to CBO"""
    context = {
        'request': request_obj,
        'organization': request_obj.organization,
        'reason': reason,
        'portal_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
    }
    
    return email_service.send_email(
        to_emails=[request_obj.organization.email],
        subject=f"Request Denied - ${request_obj.amount}",
        template_name="request_denied",
        context=context
    )


def send_request_approval_email(request_obj):
    """Send approval notification email to CBO"""
    context = {
        'request': request_obj,
        'organization': request_obj.organization,
        'portal_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
    }
    
    return email_service.send_email(
        to_emails=[request_obj.organization.email],
        subject=f"Request Approved - ${request_obj.amount}",
        template_name="request_approved",
        context=context
    )


def create_request_notification(request_obj, notification_type, title, message, recipient):
    """Create a notification record for a request status change"""
    from .models import RequestNotification
    
    try:
        notification = RequestNotification.objects.create(
            request=request_obj,
            notification_type=notification_type,
            title=title,
            message=message,
            recipient=recipient
        )
        logger.info(f"Created notification: {notification}")
        return notification
    except Exception as e:
        logger.error(f"Failed to create notification: {str(e)}")
        return None


def send_request_denial_notification(request_obj, reason=""):
    """Send denial notification to CBO (both email and in-app notification)"""
    # Create in-app notification
    notification = create_request_notification(
        request_obj=request_obj,
        notification_type='denied',
        title=f"Request Denied - ${request_obj.amount}",
        message=f"Your request for ${request_obj.amount} has been denied. Reason: {reason}",
        recipient=request_obj.organization.user
    )
    
    # Send email notification
    email_sent = send_request_denial_email(request_obj, reason)
    
    return notification, email_sent


def send_request_approval_notification(request_obj):
    """Send approval notification to CBO (both email and in-app notification)"""
    # Create in-app notification
    notification = create_request_notification(
        request_obj=request_obj,
        notification_type='approved',
        title=f"Request Approved - ${request_obj.amount}",
        message=f"Your request for ${request_obj.amount} has been approved and is now visible to donors.",
        recipient=request_obj.organization.user
    )
    
    # Send email notification
    email_sent = send_request_approval_email(request_obj)
    
    return notification, email_sent
