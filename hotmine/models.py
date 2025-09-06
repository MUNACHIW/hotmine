from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MinValueValidator, MaxValueValidator


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, "userprofile"):
        instance.userprofile.save()


class CryptoWallet(models.Model):
    """Model to store crypto wallet addresses that admin can update"""

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

    wallet_type = models.CharField(max_length=10, choices=WALLET_TYPES, unique=True)
    wallet_address = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_wallet_type_display()} - {self.wallet_address[:20]}..."

    class Meta:
        verbose_name = "Crypto Wallet"
        verbose_name_plural = "Crypto Wallets"


class InvestmentPlan(models.Model):
    """Model for investment plans that admin can manage"""

    title = models.CharField(max_length=100)
    description = models.TextField()
    minimum_deposit = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(1)]
    )
    maximum_deposit = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    daily_earnings_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0.01), MaxValueValidator(50.00)],
        help_text="Daily earnings percentage (e.g., 1.80 for 1.8%)",
    )
    investment_duration_days = models.PositiveIntegerField(
        help_text="Investment duration in days"
    )
    deposit_return = models.BooleanField(
        default=True, help_text="Return initial deposit after duration"
    )
    crypto_wallet = models.ForeignKey(
        CryptoWallet, on_delete=models.CASCADE, help_text="Crypto wallet for this plan"
    )
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(
        default=0, help_text="Order to display plans (lower numbers first)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    @property
    def investment_range_display(self):
        if self.maximum_deposit:
            return f"${self.minimum_deposit:,.0f} - ${self.maximum_deposit:,.0f}"
        return f"${self.minimum_deposit:,.0f}+"

    @property
    def total_return_percentage(self):
        """Calculate total return percentage over the investment period"""
        return self.daily_earnings_percentage * self.investment_duration_days

    @property
    def estimated_total_return(self):
        """Calculate estimated total return for minimum investment"""
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

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    investment_plan = models.ForeignKey(
        InvestmentPlan, on_delete=models.CASCADE, null=True
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    wallet_address_used = models.CharField(
        max_length=255,
        help_text="Wallet address that was used for this investment",
        null=True,
        blank=True,
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="PENDING")
    date_invested = models.DateTimeField(auto_now_add=True)
    date_completed = models.DateTimeField(null=True, blank=True)
    total_earnings = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Legacy fields for backward compatibility
    plan = models.CharField(
        max_length=100,
        blank=True,
        help_text="Legacy field - use investment_plan instead",
    )
    wallet_address = models.CharField(
        max_length=255,
        blank=True,
        help_text="Legacy field - use wallet_address_used instead",
    )

    def __str__(self):
        return f"{self.user.username} - {self.investment_plan.title} - ${self.amount}"

    @property
    def daily_earnings(self):
        """Calculate daily earnings for this investment"""
        return (self.investment_plan.daily_earnings_percentage / 100) * self.amount

    @property
    def expected_total_earnings(self):
        """Calculate expected total earnings over the investment period"""
        return self.daily_earnings * self.investment_plan.investment_duration_days

    @property
    def expected_total_return(self):
        """Calculate expected total return including principal if applicable"""
        total_earnings = self.expected_total_earnings
        if self.investment_plan.deposit_return:
            return total_earnings + self.amount
        return total_earnings

    @property
    def days_remaining(self):
        """Calculate days remaining in investment period"""
        from django.utils import timezone

        if self.status == "COMPLETED":
            return 0

        days_elapsed = (timezone.now().date() - self.date_invested.date()).days
        return max(0, self.investment_plan.investment_duration_days - days_elapsed)

    @property
    def progress_percentage(self):
        """Calculate investment progress as percentage"""
        from django.utils import timezone

        if self.status == "COMPLETED":
            return 100

        days_elapsed = (timezone.now().date() - self.date_invested.date()).days
        total_days = self.investment_plan.investment_duration_days
        return min(100, (days_elapsed / total_days) * 100)

    def save(self, *args, **kwargs):
        # Migrate legacy data if needed
        if self.plan and not self.investment_plan_id:
            # Try to find matching investment plan or create a default one
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
