from django.core.mail import EmailMessage  # Used to create and send emails
from hashlib import sha1  # Used to securely hash data
from datetime import datetime, timedelta  # To handle dates and times
from .models import ResetToken  # ResetToken model from .models
from django.urls import reverse  # To get URL from named paths


def generate_reset_url(user):
    """Generate a special reset link for user."""

    # Create a unique token by hashing username and current time
    token = sha1((user.username + str(datetime.now())).encode()).hexdigest()

    # Set token to expire in 30 min from now
    expiry = datetime.now() + timedelta(minutes=30)

    # Save this token and expiry time in the database linked to the user
    ResetToken.objects.create(user=user, token=token, expiry_date=expiry)

    # Return the Url path for the password reset page, including the token
    # This URL will be something like /store_front/reset_password/<token>/
    return reverse('store_front:password_reset_token', kwargs={'token': token})


def build_email(user, url):
    """This function creates the email that will be sent to the user"""
    subject = 'Password Reset Request'  # Email subject line

    # Email message body, showing the user their reset link
    # The URL includes the reset token,
    # So they can reset their password securely
    body = (
        f'Hello {user.username},\n\n'
        'Click the link below to reset your password:\n\n'
        f'http://localhost:8000{url}'
    )

    # Create the email object, setting the recipient
    # To the user's email address
    email = EmailMessage(subject, body, to=[user.email])

    return email  # Return the email object so it can be sent later
