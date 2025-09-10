from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
from django.core.paginator import Paginator
from .forms import (
    SignUpForm,
    LoginForm,
    UserUpdateForm,
    PasswordUpdateForm,
    EmailVerificationForm,
)
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.views import View


# Add these to your existing forms import
from .models import (
    Totalearnings,
    UserProfile,
    Investment,
    InvestmentPlan,
    CryptoWallet,
    totalwithdraw,
    Amount,
)


def home(request):
    return render(request, "hotmine/home.html")


def dashboard(request):
    user = request.user

    amount_obj = Amount.objects.filter(user=user).first()
    earnings_obj = Totalearnings.objects.filter(user=user).first()
    withdraw_obj = totalwithdraw.objects.filter(user=user).first()

    context = {
        "user": user,
        "amount": amount_obj.amount if amount_obj else 0,
        "total_earnings": earnings_obj.total_earnings if earnings_obj else 0,
        "total_withdraw": withdraw_obj.total_withdraw if withdraw_obj else 0,
    }

    return render(request, "hotmine/dashboard.html", context)


def package_view(request):
    if request.user.is_authenticated:
        # Get all active investment plans ordered by sort_order
        investment_plans = InvestmentPlan.objects.filter(is_active=True).order_by(
            "sort_order", "title"
        )

        context = {"investment_plans": investment_plans}
        return render(request, "hotmine/investmentplans.html", context)
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
    user = request.user

    if request.method == "POST":
        form = UserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect("profile")
    else:
        form = UserUpdateForm(instance=user)

    # Get financial data
    amount_obj = Amount.objects.filter(user=user).first()
    withdraw_obj = totalwithdraw.objects.filter(user=user).first()
    earnings_obj = Totalearnings.objects.filter(user=user).first()
    context = {
        "user": user,
        "form": form,
        "amount": amount_obj.amount if amount_obj else 0,
        "total_earnings": earnings_obj.total_earnings if earnings_obj else 0,
        "total_withdraw": withdraw_obj.total_withdraw if withdraw_obj else 0,
    }

    return render(request, "hotmine/profile.html", context)


from django.contrib.auth import update_session_auth_hash


@login_required
def change_password(request):
    user = request.user

    if request.method == "POST":
        form = PasswordUpdateForm(user, request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)  # Prevent logout
            messages.success(request, "Password updated successfully!")
            return redirect("dashboard")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PasswordUpdateForm(user)

    # Get financial data
    amount_obj = Amount.objects.filter(user=user).first()
    withdraw_obj = totalwithdraw.objects.filter(user=user).first()
    earnings_obj = Totalearnings.objects.filter(user=user).first()

    context = {
        "form": form,
        "amount": amount_obj.amount if amount_obj else 0,
        "total_withdraw": withdraw_obj.total_withdraw if withdraw_obj else 0,
        "total_earnings": earnings_obj.total_earnings if earnings_obj else 0,
    }

    return render(request, "hotmine/password.html", context)


@login_required
def invest_view(request):
    # Get all active investment plans
    plans = InvestmentPlan.objects.filter(is_active=True).order_by(
        "sort_order", "title"
    )
    selected_plan_id = request.GET.get("plan_id", "")
    selected_plan = None

    if selected_plan_id:
        try:
            selected_plan = InvestmentPlan.objects.get(
                id=selected_plan_id, is_active=True
            )
        except InvestmentPlan.DoesNotExist:
            pass

    if request.method == "POST":
        plan_id = request.POST.get("plan_id")
        amount = request.POST.get("amount")

        try:
            investment_plan = InvestmentPlan.objects.get(id=plan_id, is_active=True)
            amount = float(amount)

            # Validate investment amount
            if amount < investment_plan.minimum_deposit:
                messages.error(
                    request,
                    f"Minimum investment for {investment_plan.title} is ${investment_plan.minimum_deposit}",
                )
                return redirect(f"/invest/?plan_id={plan_id}")

            if (
                investment_plan.maximum_deposit
                and amount > investment_plan.maximum_deposit
            ):
                messages.error(
                    request,
                    f"Maximum investment for {investment_plan.title} is ${investment_plan.maximum_deposit}",
                )
                return redirect(f"/invest/?plan_id={plan_id}")

            # Create investment record
            Investment.objects.create(
                user=request.user,
                investment_plan=investment_plan,
                amount=amount,
                wallet_address_used=investment_plan.crypto_wallet.wallet_address,
                # Legacy fields for compatibility
                plan=investment_plan.title,
                wallet_address=investment_plan.crypto_wallet.wallet_address,
            )

            messages.success(
                request,
                f"Investment of ${amount} in {investment_plan.title} submitted successfully!",
            )
            return redirect("investment_success")

        except InvestmentPlan.DoesNotExist:
            messages.error(request, "Invalid investment plan selected.")
        except ValueError:
            messages.error(request, "Invalid investment amount.")
        except Exception as e:
            messages.error(
                request, "An error occurred while processing your investment."
            )

    context = {
        "plans": plans,
        "selected_plan": selected_plan,
    }
    return render(request, "hotmine/invest.html", context)


def get_plan_details(request, plan_id):
    """AJAX endpoint to get plan details"""
    try:
        plan = InvestmentPlan.objects.get(id=plan_id, is_active=True)
        return JsonResponse(
            {
                "success": True,
                "plan": {
                    "id": plan.id,
                    "title": plan.title,
                    "description": plan.description,
                    "minimum_deposit": float(plan.minimum_deposit),
                    "maximum_deposit": (
                        float(plan.maximum_deposit) if plan.maximum_deposit else None
                    ),
                    "daily_earnings_percentage": float(plan.daily_earnings_percentage),
                    "investment_duration_days": plan.investment_duration_days,
                    "deposit_return": plan.deposit_return,
                    "wallet_address": plan.crypto_wallet.wallet_address,
                    "wallet_type": plan.crypto_wallet.get_wallet_type_display(),
                    "investment_range": plan.investment_range_display,
                    "total_return_percentage": float(plan.total_return_percentage),
                },
            }
        )
    except InvestmentPlan.DoesNotExist:
        return JsonResponse({"success": False, "error": "Plan not found"})


def investment_success(request):
    return render(request, "hotmine/success.html")


@login_required
def investment_record(request):
    user = request.user
    investments_list = Investment.objects.filter(user=user).order_by("-date_invested")

    # Add pagination
    paginator = Paginator(investments_list, 10)  # Show 10 investments per page
    page_number = request.GET.get("page")
    investments = paginator.get_page(page_number)

    # Calculate summary statistics
    total_invested = sum(inv.amount for inv in investments_list)
    total_earnings = sum(inv.total_earnings for inv in investments_list)
    active_count = investments_list.filter(status="ACTIVE").count()
    completed_count = investments_list.filter(status="COMPLETED").count()

    context = {
        "investments": investments,
        "total_invested": total_invested,
        "total_earnings": total_earnings,
        "active_count": active_count,
        "completed_count": completed_count,
    }
    return render(request, "hotmine/myinvestment.html", context)


def buy_view(request):
    if request.method == "POST":
        # Handle the buy action
        pass
    return render(request, "hotmine/buy.html")


from django.views.decorators.http import require_http_methods
from django.db import transaction
from decimal import Decimal
from .models import WithdrawalRequest
import logging

logger = logging.getLogger(__name__)


@login_required
def withdraw_view(request):
    """Display withdrawal page with only queried amount from DB"""
    user = request.user

    # Ensure user profile exists
    # user_profile, created = UserProfile.objects.get_or_create(
    #     user=user, defaults={"withdrawal_enabled": False}
    # )

    # Get user's balance from Amount table
    amount_obj = Amount.objects.filter(user=user).first()
    user_balance = amount_obj.amount if amount_obj else Decimal("0.00")

    # Get user's recent withdrawals
    recent_withdrawals = WithdrawalRequest.objects.filter(user=user).order_by(
        "-created_at"
    )[:5]

    context = {
        "withdrawal_disabled": not user_profile.withdrawal_enabled,
        "disabled_reason": getattr(user_profile, "withdrawal_disabled_reason", ""),
        "amount": user_balance,
        "recent_withdrawals": recent_withdrawals,
    }

    return render(request, "hotmine/withdrawal.html", context)


@login_required
def withdrawal_history(request):
    """Display user's withdrawal history"""
    user = request.user
    withdrawals = WithdrawalRequest.objects.filter(user=user)

    context = {
        "withdrawals": withdrawals,
    }

    return render(request, "hotmine/withdrawal_history.html", context)


@login_required
@require_http_methods(["POST"])
def cancel_withdrawal(request, withdrawal_id):
    """Cancel a pending withdrawal request"""
    withdrawal = get_object_or_404(
        WithdrawalRequest, id=withdrawal_id, user=request.user
    )

    if not withdrawal.can_be_cancelled:
        messages.error(request, "This withdrawal request cannot be cancelled")
        return redirect("withdrawal_history")

    try:
        with transaction.atomic():
            withdrawal.status = "cancelled"
            withdrawal.save()

            # If funds were deducted, return them (uncomment if you deduct funds immediately)
            # amount_obj = Amount.objects.get(user=request.user)
            # amount_obj.amount += withdrawal.amount
            # amount_obj.save()

            messages.success(request, "Withdrawal request cancelled successfully")
    except Exception as e:
        logger.error(f"Error cancelling withdrawal {withdrawal_id}: {str(e)}")
        messages.error(request, "An error occurred while cancelling your withdrawal")

    return redirect("withdrawal_history")


@login_required
def investment_history_view(request):
    user = request.user
    investments = Investment.objects.filter(user=user).order_by("-date_invested")

    context = {"investments": investments}
    return render(request, "hotmine/history.html", context)


@method_decorator(csrf_protect, name="dispatch")
class SimplePasswordResetView(View):
    """Single-step password reset - email verification and password reset in one form"""

    template_name = "hotmine/password_reset.html"
    form_class = EmailVerificationForm

    def get(self, request):
        form = self.form_class()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = self.form_class(request.POST)

        if form.is_valid():
            user = form.save()

            if user:
                messages.success(
                    request,
                    f"Password successfully updated for {user.email}! You can now login with your new password.",
                )
                return redirect("login")
            else:
                messages.error(request, "An error occurred. Please try again.")

        return render(request, self.template_name, {"form": form})
