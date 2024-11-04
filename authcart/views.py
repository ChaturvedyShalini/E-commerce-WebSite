from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.models import User

# Create your views here.
def signup(request):
    if request.method == "POST":
        email = request.POST['email']
        password = request.POST['pass1']
        confirm_password = request.POST['pass2']

        if password != confirm_password:
            return HttpResponse("Password incorrect.")

        # Check if the email already exists
        try:
            if User.objects.get(username=email):
                return HttpResponse("Email already exists.")
        except User.DoesNotExist:
            # This will only execute if the email doesn't already exist
            user = User.objects.create_user(username=email, email=email, password=password)
            user.is_active = False
            user.save()
            return HttpResponse("User created")

    # If GET request or after form submission
    return render(request, "signup.html")


def handlelogin(request):
    return render(request, "login.html")


def handlelogout(request):
    return redirect('/auth/login')
