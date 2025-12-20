from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserBalance

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'kyc_verified', 'kyc_status', 
                   'balance', 'date_joined', 'is_staff')
    list_filter = ('kyc_verified', 'kyc_status', 'is_staff', 'is_superuser')
    fieldsets = UserAdmin.fieldsets + (
        ('Steam информация', {
            'fields': ('steam_id', 'avatar_url')
        }),
        ('KYC верификация', {
            'fields': ('kyc_verified', 'kyc_status', 'kyc_submitted_at', 'kyc_verified_at')
        }),
    )
    readonly_fields = ('kyc_submitted_at', 'kyc_verified_at')

@admin.register(UserBalance)
class UserBalanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'updated_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('updated_at',)
    list_per_page = 50