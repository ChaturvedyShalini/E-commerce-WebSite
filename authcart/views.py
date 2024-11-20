from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str, DjangoUnicodeDecodeError
from .utils import generate_token  # Custom token generator for account activation
from django.core.mail import EmailMessage
from django.conf import settings  # Import settings to access email configurations
from django.views import View  # View class for handling account activation
from django.contrib.auth import authenticate, login, logout


# View to handle the signup functionality
def signup(request):
    if request.method == "POST":
        # Get email and password inputs from the form
        email = request.POST.get('email')
        password = request.POST.get('pass1')
        confirm_password = request.POST.get('pass2')

        # Check if the entered passwords match
        if password != confirm_password:
            messages.warning(request, "Passwords do not match.")
            return render(request, 'signup.html')

        # Check if a user with the given email already exists
        if User.objects.filter(username=email).exists():
            existing_user = User.objects.get(username=email)
            if not existing_user.is_active:
                # If user exists but isn't activated, resend activation email
                send_activation_email(existing_user, request)
                messages.info(request, "Activate your account by clicking the link in your email.")
                return render(request, 'signup.html')
            messages.info(request, "Email is already registered and activated.")
            return render(request, 'signup.html')

        # Create the user with inactive status initially
        user = User.objects.create_user(username=email, email=email, password=password)
        user.is_active = False  # Deactivate until email is verified
        user.save()

        # Send account activation email
        send_activation_email(user, request)

        # Notify the user to activate their account through email
        messages.success(request, "Activate your account by clicking the link in your email.")
        return redirect('/auth/login')  # Redirect to login page after signup

    return render(request, "signup.html")  # Display the signup form for GET requests


# Function to send an account activation email
def send_activation_email(user, request):
    email_subject = "Activate Your Account"
    # Render the email content using the 'activate.html' template
    message = render_to_string(
        'activate.html',  # The template for the email
        {
            'user': user,  # Pass the user to personalize the email
            'domain': request.get_host(),  # Get the domain for the activation link
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),  # Encode the user ID
            'token': generate_token.make_token(user),  # Generate unique token for user
        }
    )

    # Create an email message object with subject, content, and recipient
    email_message = EmailMessage(
        email_subject, message, settings.EMAIL_HOST_USER, [user.email]
    )
    email_message.send()  # Send the email


# Class-based view to handle account activation through an email link
class ActivateAccountView(View):
    def get(self, request, uidb64, token):
        try:
            # Decode the user ID from the base64 encoding
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)  # Get the user by ID
        except (DjangoUnicodeDecodeError, User.DoesNotExist):
            user = None  # If decoding fails or user does not exist

        # Check if the user and token are valid
        if user and generate_token.check_token(user, token):
            user.is_active = True  # Activate the user's account
            user.save()  # Save changes to the user model
            messages.success(request, "Account activated successfully!")
            return redirect('/auth/login')  # Redirect to login page on success

        # If activation fails, show an error message
        messages.error(request, "Invalid activation link or user not found.")
        return render(request, 'activatefail.html')  # Render error page


# View to handle the login functionality
def handlelogin(request):
    if request.method == "POST":
        username = request.POST.get('email')  # Ensure the form field name matches
        userpassword = request.POST.get('pass1')  # Ensure the form field name matches

        myuser = authenticate(username=username, password=userpassword)

        if myuser is not None:
            if myuser.is_active:  # Check if the user is activated
                login(request, myuser)
                messages.success(request, "Login successful")
                return redirect('/')  # Redirect to the home page
            else:
                messages.error(request, "Account is not activated. Check your email.")
                return redirect('/auth/login')
        else:
            messages.error(request, "Invalid Credentials")
            return redirect('/auth/login')

    return render(request, "login.html")


# View to handle logout functionality
def handlelogout(request):
    logout(request)  # Log out the user
    messages.info(request,"Logout Success")
    return redirect('/auth/login')  # Redirect to login page after logout
