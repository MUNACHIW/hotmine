from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from .forms import SignUpForm, LoginForm, UserUpdateForm, PasswordUpdateForm
from .models import UserProfile, Investment


# Create your views here.
def home(request):
    return render(request, "hotmine/home.html")


def dashboard(request):
    if request.user.is_authenticated:
        return render(request, "hotmine/dashboard.html")
    else:
        return redirect("login")


def package_view(request):
    if request.user.is_authenticated:
        return render(request, "hotmine/investmentplans.html")
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
    if request.user.is_authenticated:
        if request.method == "POST":
            form = UserUpdateForm(request.POST, instance=request.user)
            if form.is_valid():
                form.save()
                return redirect("profile")
        else:
            form = UserUpdateForm(instance=request.user)

        return render(
            request,
            "hotmine/profile.html",
            {"user": request.user, "form": form},
        )
    else:
        return redirect("login")


@login_required
def change_password(request):
    if request.method == "POST":
        form = PasswordUpdateForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            # Important: Update session to prevent logout
            from django.contrib.auth import update_session_auth_hash

            update_session_auth_hash(request, form.user)
            return redirect("dashboard")
    else:
        form = PasswordUpdateForm(request.user)
    return render(request, "hotmine/password.html", {"form": form})


def invest_view(request):
    plans = [
        "Conservative Crypto Plan",
        "Balanced Growth Plan",
        "Aggressive High-Yield Plan",
        "Starter Portfolio",
        "Intermediate Portfolio",
        "Advanced Portfolio",
        "HODL Strategy",
        "Swing Trading Plan",
        "Day Trading Plan",
        "Stablecoin Income Plan",
        "NFT & Metaverse Plan",
        "DeFi Power Plan",
    ]
    selected_plan = request.GET.get("plan", "")
    user = request.user

    if request.method == "POST":
        plan = request.POST.get("plan")
        amount = request.POST.get("amount")
        wallet = request.POST.get("wallet")

        Investment.objects.create(
            user=user, plan=plan, amount=amount, wallet_address=wallet
        )
        return redirect("investment_success")

    return render(
        request, "hotmine/invest.html", {"plans": plans, "selected_plan": selected_plan}
    )


def investment_success(request):
    return render(request, "hotmine/success.html")


def investment_record(request):
    user = request.user
    investments = Investment.objects.filter(user=user)
    return render(request, "hotmine/myinvestment.html", {"investments": investments})


def buy_view(request):
    if request.method == "POST":
        # Handle the buy action
        pass
    return render(request, "hotmine/buy.html")


def withdraw_view(request):
    if request.method == "POST":
        # Handle the withdrawal action
        pass
    return render(request, "hotmine/withdrawal.html")
