# To render HTML pages and redirect users
from django.shortcuts import render, redirect
# Django's built-in user, group and permission models
from django.contrib.auth.models import User, Group, Permission
# Functions to handle login and logout
from django.contrib.auth import authenticate, login, logout
# For redirecting users or sending responses
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy  # Helps get URLs by their names
# Makes sure only logged-in users can access pages
from django.contrib.auth.decorators import login_required
import secrets  # For generating secure random tokens
from datetime import timedelta
from hashlib import sha1  # To hash tokens securely
from django.utils import timezone  # Handle dates and times in django
# For handling cases where an object is not found
from django.core.exceptions import ObjectDoesNotExist
# Helper functions for email and token generation
from django.db import IntegrityError
from .models import ResetToken  # Reset Token model
from django.core.mail import EmailMessage  # To send emails
# To hash passwords before saving
from django.contrib.auth.hashers import make_password


def login_user(request):
    """
    This function handles user login.
    After getting the login credentials, check if the user exists,
    set session expiry and redirect to welcome page.
    """
    if request.method == 'POST':
        # When the login form is submitted
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Check if the username and password match a user in the database
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # Set the session to expire 30 days from login
            exp_date = timedelta(days=30)
            exp_seconds = int(exp_date.total_seconds())
            if exp_seconds > 0:
                request.session.set_expiry(exp_seconds)

            # Save user info in the session
            request.session['user_id'] = user.id
            request.session['username'] = user.username

            # Redirect to welcome page after successful login
            return HttpResponseRedirect(reverse('store_front:welcome'))

        else:
            # If login failed, reload login page with error message
            return render(request, 'store_front/login.html',
                          {'error': 'Invalid credentials'})

    # If user just opened the login page, show the login form
    return render(request, 'store_front/login.html')


def register_user(request):
    """This function handles user registration (signing up)"""
    if request.method == 'POST':
        # Get data from form
        username = request.POST.get('username')
        password = request.POST.get('password')
        conf_password = request.POST.get('conf_password')
        email = request.POST.get('email')
        account_type = request.POST.get('account_type')

        if User.objects.filter(email=email).exists():
            return render(request, 'store_front/register.html', {
                'error': 'Email already in use.'
            })

        # Check if passwords match
        if conf_password != password:
            return render(request, 'store_front/register.html',
                          {'error': 'Passwords do not match'})

        # Create a new user in the database
        try:
            user = User.objects.create_user(username=username,
                                            password=password,
                                            email=email)
        except IntegrityError:
            return render(request, 'store_front/register.html', {
                'error': 'Username already in use.'
            })

        # Add user to correct account type group
        if account_type == 'vendor':
            # Try to add the new user to the 'Vendors' group
            try:
                vendors_group = Group.objects.get(name='Vendors')
                user.groups.add(vendors_group)
            except Group.DoesNotExist:
                pass  # If group doesn't exist, just ignore

        else:
            # Try to add the new user to the 'Vendors' group
            try:
                buyers_group = Group.objects.get(name='Buyers')
                user.groups.add(buyers_group)
            except Group.DoesNotExist:
                pass

        # Try to give the user permission to view products (fallback)
        try:
            permission = Permission.objects.get(
                codename='view_products',
                content_type__app_label='eCommerce')
            user.user_permissions.add(permission)
        except Permission.DoesNotExist:
            pass  # Ignore if permission doesn't exist

        user.save()  # Save changes to database

        login(request, user)  # Login the new user

        # Redirect to welcome page after registration
        return redirect(reverse('store_front:welcome'))

    # If user visits registration page, show the registration form
    return render(request, 'store_front/register.html')


def change_user_password(username, new_password):
    """Helper function to change a user's password securely"""
    user = User.objects.get(username=username)  # Find user in database

    # Set the new password (hashed automatically)
    user.set_password(new_password)

    user.save()  # Save changes to database


def logout_user(request):
    """Logs the user out and redirects to login page"""
    if request.user is not None:
        logout(request)  # Log out the current user
        return HttpResponseRedirect(reverse('store_front:login'))


# Only logged-in users can see the welcome page
@login_required(login_url=reverse_lazy('store_front:login'))
def welcome(request):
    return render(request, 'store_front/welcome.html')  # Show the welcome page


def build_email(user, reset_url):
    """Creates the email object to send for password reset"""
    subject = "Password Reset"
    user_email = user.email
    domain_email = "admin@shopperz.com"
    body = (f"Hi {user.username},\n"
            f"Here is your link to reset your password: {reset_url}")

    email = EmailMessage(subject, body, domain_email, [user_email])
    return email


def generate_reset_url(user):
    """Creates a secure reset URL with a token that expires in 30 minutes"""
    domain = "http://127.0.0.1:8000"
    app_name = "store_front"
    url = f"{domain}/{app_name}/reset_password/"

    token = secrets.token_urlsafe(16)  # Generate a random secure token

    # Token expires in 30 minutes
    expiry = timezone.now() + timedelta(minutes=30)

    # Hash the token to store securely
    hashed_token = sha1(token.encode()).hexdigest()

    # Save the hashed token and expiry date to the database
    ResetToken.objects.create(
        user=user,
        token=hashed_token,
        expiry_date=expiry
    )

    # Add the raw token to the URL for verification later
    url += f"{token}/"
    return url


def send_password_reset(request):
    """
    Handles sending the password reset email after user submits their email
    """
    if request.method == 'POST':
        user_email = request.POST.get('email')
        try:
            user = User.objects.get(email=user_email)  # Find user by email
            # Generate reset link with token
            reset_url = generate_reset_url(user)
            email = build_email(user, reset_url)  # Create the email message
            email.send()  # Send the email

            # Show a confirmation page that email was sent
            return render(request, 'store_front/reset_email_sent.html', {
                'email': user_email
            })

        except ObjectDoesNotExist:
            # Even if no user found, still show confirmation
            # (to avoid info leaks)
            return render(request, 'store_front/reset_email_sent.html', {
                'email': user_email
            })

    # Show the form where user can enter their email
    return render(request, 'store_front/request_password_reset.html')


def reset_user_password(request, token):
    """This view is called when user clicks the reset link in their email"""
    hashed_token = sha1(token.encode()).hexdigest()

    try:
        # For timezone awareness (UTC)
        current_time = timezone.now()
        # Look for token in database
        user_token = ResetToken.objects.get(token=hashed_token)

        # Check if token expired
        if user_token.expiry_date < current_time:
            user_token.delete()  # Delete expired token
            # Show expired token message
            return render(request, 'store_front/password_reset_expired.html')

        # Save user and token in session to verify next step
        request.session['user'] = user_token.user.username
        request.session['reset_token'] = token

        # Show the password reset form
        return render(request, 'store_front/password_reset.html',
                      {'token': token})

    except ResetToken.DoesNotExist:
        # Token not found or already used
        return render(request, 'store_front/password_reset_invalid.html')


def reset_password(request):
    """
    Handles the password reset form submission (when user enters new password)
    """
    if request.method == 'POST':
        username = request.session.get('user')
        token = request.session.get('reset_token')
        password = request.POST.get('password')
        password_conf = request.POST.get('password_conf')

        # Check if all required data is present
        if not all([username, token, password, password_conf]):
            return render(request, 'store_front/password_reset.html', {
                'error': 'Missing fields or session expired.',
                'token': token
            })

        # Check if passwords match
        if password != password_conf:
            return render(request, 'store_front/password_reset.html', {
                'error': 'Passwords do not match.',
                'token': token
            })

        try:
            user = User.objects.get(username=username)  # Find user by username
            hashed_token = sha1(token.encode()).hexdigest()
            reset_token = ResetToken.objects.get(token=hashed_token)
            current_time = timezone.now()

            # Check token expiry again (just to be safe)
            if reset_token.expiry_date < current_time:
                reset_token.delete()
                return render(
                    request,
                    'store_front/password_reset_expired.html'
                )

            # Update the user's password (hashed securely)
            user.password = make_password(password)
            user.save()

            # Delete the token and clear session info
            reset_token.delete()
            request.session.flush()

            # Redirect user to login page after successful password reset
            return HttpResponseRedirect(reverse('store_front:login'))

        except (User.DoesNotExist, ResetToken.DoesNotExist):
            return render(request, 'store_front/password_reset_invalid.html')

    # If the page was accessed with GET or any other method,
    # Redirect to login page
    return HttpResponseRedirect(reverse('store_front:login'))
