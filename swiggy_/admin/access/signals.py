from django.dispatch import Signal, receiver
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status
from .utils import executor
import threading

otp_generated = Signal()
account_acceptance_email = Signal()
restaurant_request_email = Signal()
delivery_request_email = Signal()

def send_email_thread(subject, message, recipient_list, from_email=None):
    try:
        send_mail(
            subject,
            message,
            from_email or settings.EMAIL_HOST_USER,
            recipient_list,
            fail_silently=False
        )
        print(f"Email sent successfully to {recipient_list}")
    except Exception as e:
        print(f"Failed to send email to {recipient_list}: {str(e)}")

@receiver(otp_generated)
def send_otp_email(sender, email, otp, **kwargs):
    """
    Signal receiver to send OTP email asynchronously.
    """
    print(f"Signal received! Sending OTP email to {email} in background...")
    subject = 'Your Swiggy Signup OTP'
    message = f'Your Signup OTP is: {otp}'
    
    executor.submit(send_email_thread, subject, message, [email], from_email=settings.EMAIL_HOST_USER)

@receiver(account_acceptance_email)
def send_acceptance_email(sender, email, password, approve_link, reject_link, phone=None, **kwargs):
    """
    Signal receiver to send account acceptance email asynchronously.
    """
    print(f"Signal received! Sending acceptance email to {email} in background...")
    message = f"""
Welcome to Swiggy!
Your account has been initiated by the Super Admin.

Here are your credentials (valid after acceptance):
Username: {email or phone}
Password: {password}

ACTION REQUIRED:
Please Accept or Reject this account creation request.

Click here to ACCEPT (Create & Activate Account):
{approve_link}

Click here to REJECT (Cancel Request):
{reject_link}
"""
    subject = 'Swiggy Account Acceptance Request'
    executor.submit(send_email_thread, subject, message, [email], from_email=settings.EMAIL_HOST_USER)

@receiver(restaurant_request_email)
def send_restaurant_request_email(sender, super_admin_email, restaurant_name, approve_link, reject_link, **kwargs):
    """
    Signal receiver to send restaurant approval request to Super Admin asynchronously.
    """
    print(f"Signal received! Sending restaurant request email to Super Admin: {super_admin_email} in background...")
    message = f"""
New Restaurant Signup Request!

Restaurant Name: {restaurant_name}

A new restaurant has requested to join the platform. Please review the request.

ACTION REQUIRED:
Please Accept or Reject this restaurant creation request.

Click here to APPROVE (Create & Activate User and Restaurant):
{approve_link}

Click here to REJECT (Cancel Request):
{reject_link}
"""
    subject = 'New Restaurant Signup Request - Action Required'
    executor.submit(send_email_thread, subject, message, [super_admin_email], from_email=settings.EMAIL_HOST_USER)

@receiver(delivery_request_email)
def send_delivery_request_email(sender, super_admin_email, partner_name, approve_link, reject_link, **kwargs):
    """
    Signal receiver to send delivery partner approval request to Super Admin asynchronously.
    """
    print(f"Signal received! Sending delivery request email to Super Admin: {super_admin_email} in background...")
    message = f"""
New Delivery Partner Signup Request!

Partner Name: {partner_name}

A new delivery partner has requested to join the platform. Please review the request.

ACTION REQUIRED:
Please Accept or Reject this delivery partner creation request.

Click here to APPROVE (Create & Activate User and Delivery Partner):
{approve_link}

Click here to REJECT (Cancel Request):
{reject_link}
"""
    subject = 'New Delivery Partner Signup Request - Action Required'
    # If partner_name is an email, use it as from_email as requested
    from_email = partner_name if '@' in partner_name else settings.EMAIL_HOST_USER
    executor.submit(send_email_thread, subject, message, [super_admin_email], from_email=from_email)
