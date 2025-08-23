from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from .forms import SignUpForm, LoginForm
from .models import UserProfile


# Create your views here.
def home(request):
    return render(request, "hotmine/home.html")


def dashboard(request):
    if request.user.is_authenticated:
        return render(request, "hotmine/dashboard.html")
    else:
        return redirect("login")


def signup_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Save phone number to user profile
            try:
                user_profile = user.userprofile
            except UserProfile.DoesNotExist:
                user_profile = UserProfile.objects.create(user=user)

            user_profile.phone_number = form.cleaned_data["phone_number"]
            user_profile.save()

            username = form.cleaned_data.get("username")
            messages.success(
                request, f"Account created for {username}! You can now log in."
            )
            return redirect("login")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = SignUpForm()

    return render(request, "hotmine/signup.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.first_name}!")
                # Redirect to next page or home
                next_page = request.GET.get("next", "dashboard")
                return redirect(next_page)
        else:
            messages.error(request, "Invalid username/email or password.")
    else:
        form = LoginForm()

    return render(request, "hotmine/login.html", {"form": form})


def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect("login")


@login_required
def profile_view(request):
    return render(request, "hotmine/profile.html", {"user": request.user})
