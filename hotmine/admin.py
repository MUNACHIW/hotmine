from django.contrib import admin
from .models import UserProfile, Investment

# Register your models here.


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "phone_number", "created_at"]
    search_fields = ["user__username", "user__email", "phone_number"]
    list_filter = ["created_at"]


@admin.register(Investment)
class InvestmentAdmin(admin.ModelAdmin):
    list_display = ["user", "plan", "amount", "wallet_address", "date_invested"]
    search_fields = ["user__username", "plan", "wallet_address"]
    list_filter = ["plan", "date_invested"]
