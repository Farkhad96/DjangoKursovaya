from django.contrib import admin

from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "email_verified", "is_blocked")
    list_filter = ("email_verified", "is_blocked")
