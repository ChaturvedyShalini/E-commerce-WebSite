from django.shortcuts import render, redirect
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
from django.urls import reverse  # Import reverse for URL generation


# View to handle the signup functionality
def signup(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('pass1')
        confirm_password = request.POST.get('pass2')

        if password != confirm_password:
            messages.warning(request, "Passwords do not match.")
            return render(request, 'signup.html')

        if User.objects.filter(username=email).exists():
            existing_user = User.objects.get(username=email)
            if not existing_user.is_active:
                send_activation_email(existing_user, request)
                messages.info(request, "Activate your account by clicking the link in your email.")
                return render(request, 'signup.html')
            messages.info(request, "Email is already registered and activated.")
            return render(request, 'signup.html')

        user = User.objects.create_user(username=email, email=email, password=password)
        user.is_active = False  # Initially set the account as inactive
        user.save()

        send_activation_email(user, request)
        messages.success(request, "Activate your account by clicking the link in your email.")
        return redirect('/auth/login')

    return render(request, "signup.html")


# Function to send account activation email
def send_activation_email(user, request):
    email_subject = "Activate Your Account"
    message = render_to_string(
        'activate.html',
        {
            'user': user,
            'domain': request.get_host(),
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': generate_token.make_token(user),
        }
    )
    email_message = EmailMessage(
        email_subject, message, settings.EMAIL_HOST_USER, [user.email]
    )
    email_message.send()


# Class-based view to handle account activation through an email link
class ActivateAccountView(View):
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (DjangoUnicodeDecodeError, User.DoesNotExist):
            user = None

        if user and generate_token.check_token(user, token):
            user.is_active = True
            user.save()
            messages.success(request, "Account activated successfully!")
            return redirect('/auth/login')

        messages.error(request, "Invalid activation link or user not found.")
        return render(request, 'activatefail.html')


# View to handle the login functionality
def handlelogin(request):
    if request.method == "POST":
        username = request.POST.get('email')
        userpassword = request.POST.get('pass1')

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
    logout(request)
    messages.info(request, "Logout Success")
    return redirect('/auth/login')


# New view for password reset request
class RequestResetEmailView(View):
    def get(self, request):
        return render(request, 'request_reset_email.html')  # Template for requesting password reset

    def post(self, request):
        email = request.POST.get('email')

        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
            token = generate_token.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_url = reverse('password_reset', kwargs={'uidb64': uid, 'token': token})

            # Render the reset email
            message = render_to_string('reset_password_email.html', {
                'user': user,
                'reset_url': reset_url,
            })

            email_message = EmailMessage(
                'Password Reset Request',
                message,
                settings.EMAIL_HOST_USER,
                [email],
            )
            email_message.send()

            messages.success(request, 'Password reset link sent to your email.')
        else:
            messages.error(request, 'No user with that email found.')

        return redirect('request-reset-email')


# New view for password reset form (set new password)
class ResetPasswordView(View):
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (DjangoUnicodeDecodeError, User.DoesNotExist):
            user = None

        if user and generate_token.check_token(user, token):
            return render(request, 'reset_password_form.html', {'uidb64': uidb64, 'token': token})

        messages.error(request, "Invalid or expired reset link.")
        return redirect('request-reset-email')

    def post(self, request, uidb64, token):
        password = request.POST.get('password')
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (DjangoUnicodeDecodeError, User.DoesNotExist):
            user = None

        if user and generate_token.check_token(user, token):
            user.set_password(password)
            user.save()
            messages.success(request, "Your password has been reset successfully.")
            return redirect('login')

        messages.error(request, "Invalid reset link or user not found.")
        return redirect('request-reset-email')
