from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    UserProfile,
    Investment,
    InvestmentPlan,
    CryptoWallet,
    Amount,
    Totalearnings,
    totalwithdraw,
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "phone_number", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["user__username", "user__email", "phone_number"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(CryptoWallet)
class CryptoWalletAdmin(admin.ModelAdmin):
    list_display = ["wallet_type", "wallet_address_short", "is_active", "updated_at"]
    list_filter = ["wallet_type", "is_active"]
    list_editable = ["is_active"]
    search_fields = ["wallet_address"]
    readonly_fields = ["created_at", "updated_at"]

    def wallet_address_short(self, obj):
        """Display shortened wallet address for better readability"""
        if len(obj.wallet_address) > 30:
            return f"{obj.wallet_address[:15]}...{obj.wallet_address[-10:]}"
        return obj.wallet_address

    wallet_address_short.short_description = "Wallet Address"


@admin.register(InvestmentPlan)
class InvestmentPlanAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "investment_range_display_admin",
        "daily_earnings_percentage",
        "investment_duration_days",
        "deposit_return_display",
        "crypto_wallet",
        "is_active",
        "sort_order",
    ]
    list_filter = [
        "is_active",
        "deposit_return",
        "crypto_wallet__wallet_type",
    ]
    list_editable = ["is_active", "sort_order"]
    search_fields = ["title", "description"]
    readonly_fields = [
        "created_at",
        "updated_at",
        "total_return_percentage",
        "estimated_total_return_display",
    ]
    ordering = ["sort_order", "title"]

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("title", "description", "is_active", "sort_order")},
        ),
        (
            "Investment Details",
            {
                "fields": (
                    "minimum_deposit",
                    "maximum_deposit",
                    "daily_earnings_percentage",
                    "investment_duration_days",
                    "deposit_return",
                )
            },
        ),
        ("Crypto Configuration", {"fields": ("crypto_wallet",)}),
        (
            "Calculated Fields",
            {
                "fields": ("total_return_percentage", "estimated_total_return_display"),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def investment_range_display_admin(self, obj):
        return obj.investment_range_display or "N/A"

    investment_range_display_admin.short_description = "Investment Range"

    def deposit_return_display(self, obj):
        if obj.deposit_return:
            return format_html('<span style="color: green;">✓ Yes</span>')
        return format_html('<span style="color: red;">✗ No</span>')

    deposit_return_display.short_description = "Deposit Return"

    def estimated_total_return_display(self, obj):
        if obj.estimated_total_return is None:
            return "N/A"
        return f"${obj.estimated_total_return:,.2f}"

    estimated_total_return_display.short_description = (
        "Estimated Total Return (Min Investment)"
    )


@admin.register(Investment)
class InvestmentAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "investment_plan_title",
        "amount",
        "daily_earnings_display",
        "status",
        "progress_display",
        "date_invested",
    ]
    list_filter = ["status", "investment_plan", "date_invested"]
    search_fields = [
        "user__username",
        "user__email",
        "investment_plan__title",
        "wallet_address_used",
    ]
    readonly_fields = [
        "date_invested",
        "daily_earnings_display",
        "expected_total_earnings_display",
        "expected_total_return_display",
        "progress_percentage_display",
        "days_remaining_display",
    ]
    list_editable = ["status"]
    date_hierarchy = "date_invested"

    fieldsets = (
        (
            "Investment Information",
            {
                "fields": (
                    "user",
                    "investment_plan",
                    "amount",
                    "wallet_address_used",
                    "status",
                )
            },
        ),
        (
            "Earnings & Progress",
            {
                "fields": (
                    "total_earnings",
                    "daily_earnings_display",
                    "expected_total_earnings_display",
                    "expected_total_return_display",
                    "progress_percentage_display",
                    "days_remaining_display",
                )
            },
        ),
        ("Dates", {"fields": ("date_invested", "date_completed")}),
        (
            "Legacy Fields",
            {
                "fields": ("plan", "wallet_address"),
                "classes": ("collapse",),
                "description": "These fields are kept for backward compatibility",
            },
        ),
    )

    def investment_plan_title(self, obj):
        if obj.investment_plan:
            return obj.investment_plan.title
        return obj.plan or "N/A"

    investment_plan_title.short_description = "Investment Plan"

    def daily_earnings_display(self, obj):
        if obj.investment_plan:
            return f"${obj.daily_earnings:,.2f}"
        return "N/A"

    daily_earnings_display.short_description = "Daily Earnings"

    def expected_total_earnings_display(self, obj):
        if obj.investment_plan:
            return f"${obj.expected_total_earnings:,.2f}"
        return "N/A"

    expected_total_earnings_display.short_description = "Expected Total Earnings"

    def expected_total_return_display(self, obj):
        if obj.investment_plan:
            return f"${obj.expected_total_return:,.2f}"
        return "N/A"

    expected_total_return_display.short_description = "Expected Total Return"

    def progress_display(self, obj):
        if obj.investment_plan:
            percentage = obj.progress_percentage
            if percentage >= 100:
                color = "green"
                icon = "✓"
            elif percentage >= 50:
                color = "orange"
                icon = "◐"
            else:
                color = "blue"
                icon = "○"
            return format_html(
                f'<span style="color: {color};">{icon} {percentage:.1f}%</span>'
            )
        return "N/A"

    progress_display.short_description = "Progress"

    def progress_percentage_display(self, obj):
        if obj.investment_plan:
            return f"{obj.progress_percentage:.2f}%"
        return "N/A"

    progress_percentage_display.short_description = "Progress Percentage"

    def days_remaining_display(self, obj):
        if obj.investment_plan:
            days = obj.days_remaining
            if days == 0:
                return format_html('<span style="color: green;">Completed</span>')
            elif days <= 7:
                return format_html(f'<span style="color: orange;">{days} days</span>')
            else:
                return format_html(f'<span style="color: blue;">{days} days</span>')
        return "N/A"

    days_remaining_display.short_description = "Days Remaining"

    actions = ["mark_as_active", "mark_as_completed", "mark_as_cancelled"]

    def mark_as_active(self, request, queryset):
        updated = queryset.update(status="ACTIVE")
        self.message_user(request, f"{updated} investments marked as active.")

    mark_as_active.short_description = "Mark selected investments as active"

    def mark_as_completed(self, request, queryset):
        from django.utils import timezone

        updated = queryset.update(status="COMPLETED", date_completed=timezone.now())
        self.message_user(request, f"{updated} investments marked as completed.")

    mark_as_completed.short_description = "Mark selected investments as completed"

    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(status="CANCELLED")
        self.message_user(request, f"{updated} investments marked as cancelled.")

    mark_as_cancelled.short_description = "Mark selected investments as cancelled"


@admin.register(Amount)
class AmountAdmin(admin.ModelAdmin):
    list_display = ("user", "amount", "created_at", "updated_at")
    search_fields = ("user__username",)
    list_filter = ("created_at", "updated_at")


@admin.register(Totalearnings)
class TotalearningsAdmin(admin.ModelAdmin):
    list_display = ("user", "total_earnings", "created_at", "updated_at")
    search_fields = ("user__username",)
    list_filter = ("created_at", "updated_at")


@admin.register(totalwithdraw)
class TotalWithdrawAdmin(admin.ModelAdmin):
    list_display = ("user", "total_withdraw", "created_at", "updated_at")
    search_fields = ("user__username",)
    list_filter = ("created_at", "updated_at")


# Customize admin site headers
admin.site.site_header = "HotmineAdmin"
admin.site.site_title = "Hotmine Admin"
admin.site.index_title = "Welcome HotmineAdmin"
