from django.contrib import admin
from .models import UserProfile

# Register your models here.


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "phone_number", "created_at"]
    search_fields = ["user__username", "user__email", "phone_number"]
    list_filter = ["created_at"]
