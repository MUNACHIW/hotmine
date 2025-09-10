from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    withdrawal_enabled = models.BooleanField(
        default=True, help_text="Allow this user to make withdrawal requests"
    )
    withdrawal_disabled_reason = models.TextField(
        blank=True, null=True, help_text="Reason for disabling withdrawals (optional)"
    )
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile" if self.user else "No User"

    @property
    def can_withdraw(self):
        """Check if user can make withdrawals"""
        return self.withdrawal_enabled


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, "userprofile"):
        instance.userprofile.save()


class CryptoWallet(models.Model):
    WALLET_TYPES = [
        ("BTC", "Bitcoin"),
        ("ETH", "Ethereum"),
        ("BNB", "Binance Coin"),
        ("USDT", "Tether (TRC20)"),
        ("LTC", "Litecoin"),
        ("ADA", "Cardano"),
        ("DOT", "Polkadot"),
        ("SOL", "Solana"),
    ]

    wallet_type = models.CharField(
        max_length=10, choices=WALLET_TYPES, unique=True, null=True, blank=True
    )
    wallet_address = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return (
            f"{self.get_wallet_type_display()} - {self.wallet_address[:20]}..."
            if self.wallet_type
            else "No Wallet Type"
        )

    class Meta:
        verbose_name = "Crypto Wallet"
        verbose_name_plural = "Crypto Wallets"


class InvestmentPlan(models.Model):
    title = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    minimum_deposit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(1)],
        null=True,
        blank=True,
    )
    maximum_deposit = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    daily_earnings_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0.01), MaxValueValidator(50.00)],
        help_text="Daily earnings percentage (e.g., 1.80 for 1.8%)",
        null=True,
        blank=True,
    )
    investment_duration_days = models.PositiveIntegerField(
        help_text="Investment duration in days", null=True, blank=True
    )
    deposit_return = models.BooleanField(
        default=True, help_text="Return initial deposit after duration"
    )
    crypto_wallet = models.ForeignKey(
        CryptoWallet,
        on_delete=models.CASCADE,
        help_text="Crypto wallet for this plan",
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(
        default=0,
        help_text="Order to display plans (lower numbers first)",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title or "No Title"

    @property
    def investment_range_display(self):
        if self.minimum_deposit is None:
            return "N/A"
        if self.maximum_deposit is not None:
            return f"${self.minimum_deposit:,.0f} - ${self.maximum_deposit:,.0f}"
        return f"${self.minimum_deposit:,.0f}+"

    @property
    def total_return_percentage(self):
        if (
            self.daily_earnings_percentage is None
            or self.investment_duration_days is None
        ):
            return None
        return self.daily_earnings_percentage * self.investment_duration_days

    @property
    def estimated_total_return(self):
        if (
            self.daily_earnings_percentage is None
            or self.minimum_deposit is None
            or self.investment_duration_days is None
        ):
            return None
        daily_return = (self.daily_earnings_percentage / 100) * self.minimum_deposit
        total_earnings = daily_return * self.investment_duration_days
        if self.deposit_return:
            return total_earnings + self.minimum_deposit
        return total_earnings

    class Meta:
        ordering = ["sort_order", "title"]
        verbose_name = "Investment Plan"
        verbose_name_plural = "Investment Plans"


class Investment(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("ACTIVE", "Active"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    investment_plan = models.ForeignKey(
        InvestmentPlan, on_delete=models.CASCADE, null=True, blank=True
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    wallet_address_used = models.CharField(
        max_length=255,
        help_text="Wallet address that was used for this investment",
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="PENDING",
        null=True,
        blank=True,
    )
    date_invested = models.DateTimeField(auto_now_add=True)
    date_completed = models.DateTimeField(null=True, blank=True)
    total_earnings = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, null=True, blank=True
    )

    # Legacy fields
    plan = models.CharField(max_length=100, blank=True, null=True)
    wallet_address = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        if self.user and self.investment_plan:
            return (
                f"{self.user.username} - {self.investment_plan.title} - ${self.amount}"
            )
        return "Incomplete Investment"

    @property
    def daily_earnings(self):
        if not self.investment_plan or self.amount is None:
            return None
        return (self.investment_plan.daily_earnings_percentage / 100) * self.amount

    @property
    def expected_total_earnings(self):
        if self.daily_earnings is None or not self.investment_plan:
            return None
        return self.daily_earnings * self.investment_plan.investment_duration_days

    @property
    def expected_total_return(self):
        if self.expected_total_earnings is None:
            return None
        if self.investment_plan.deposit_return:
            return self.expected_total_earnings + self.amount
        return self.expected_total_earnings

    @property
    def days_remaining(self):
        from django.utils import timezone

        if not self.investment_plan:
            return None
        if self.status == "COMPLETED":
            return 0
        days_elapsed = (timezone.now().date() - self.date_invested.date()).days
        return max(0, self.investment_plan.investment_duration_days - days_elapsed)

    @property
    def progress_percentage(self):
        from django.utils import timezone

        if not self.investment_plan:
            return None
        if self.status == "COMPLETED":
            return 100
        days_elapsed = (timezone.now().date() - self.date_invested.date()).days
        total_days = self.investment_plan.investment_duration_days
        return min(100, (days_elapsed / total_days) * 100)

    def save(self, *args, **kwargs):
        if self.plan and not self.investment_plan_id:
            try:
                plan = InvestmentPlan.objects.filter(
                    title__icontains=self.plan.split()[0]
                ).first()
                if plan:
                    self.investment_plan = plan
            except:
                pass
        if self.wallet_address and not self.wallet_address_used:
            self.wallet_address_used = self.wallet_address
        super().save(*args, **kwargs)

    class Meta:
        ordering = ["-date_invested"]
        verbose_name = "Investment"
        verbose_name_plural = "Investments"


class Amount(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - ${self.amount}" if self.user else "No User"


class Totalearnings(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    total_earnings = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return (
            f"{self.user.username} - ${self.total_earnings}" if self.user else "No User"
        )


class totalwithdraw(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    total_withdraw = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return (
            f"{self.user.username} - ${self.total_withdraw}" if self.user else "No User"
        )


class WithdrawalRequest(models.Model):
    WITHDRAWAL_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("rejected", "Rejected"),
        ("cancelled", "Cancelled"),
    ]

    WITHDRAWAL_METHOD_CHOICES = [
        ("bank", "Bank Transfer"),
        ("paypal", "PayPal"),
        ("crypto", "Cryptocurrency"),
        ("mobile_money", "Mobile Money"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="withdrawal_requests"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    withdrawal_method = models.CharField(
        max_length=20, choices=WITHDRAWAL_METHOD_CHOICES
    )
    account_details = models.TextField()
    withdrawal_note = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20, choices=WITHDRAWAL_STATUS_CHOICES, default="pending"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(blank=True, null=True)

    # Admin fields
    admin_note = models.TextField(
        blank=True, null=True, help_text="Admin notes for this withdrawal"
    )
    processed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="processed_withdrawals",
    )

    # Transaction details
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Withdrawal Request"
        verbose_name_plural = "Withdrawal Requests"

    def __str__(self):
        return f"{self.user.username} - ${self.amount} - {self.status}"

    @property
    def can_be_cancelled(self):
        """Check if withdrawal can be cancelled by user"""
        return self.status in ["pending", "processing"]

    def mark_as_completed(self, processed_by=None, transaction_id=None):
        """Mark withdrawal as completed"""
        self.status = "completed"
        self.processed_at = timezone.now()
        self.processed_by = processed_by
        if transaction_id:
            self.transaction_id = transaction_id
        self.save()

    def mark_as_rejected(self, reason, processed_by=None):
        """Mark withdrawal as rejected"""
        self.status = "rejected"
        self.rejection_reason = reason
        self.processed_at = timezone.now()
        self.processed_by = processed_by
        self.save()
