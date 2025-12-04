from django.contrib import admin
from .models import (
    UserProfile, Chama, Membership, Contribution, 
    Transaction, Announcement, Message
)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'phone_number', 'created_at']
    list_filter = ['role', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone_number']

@admin.register(Chama)
class ChamaAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_by', 'contribution_amount', 'contribution_frequency', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'chama', 'role', 'is_active', 'joined_at']
    list_filter = ['role', 'is_active', 'joined_at']
    search_fields = ['user__username', 'chama__name']

@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    list_display = ['membership', 'amount', 'date', 'created_at']
    list_filter = ['date', 'created_at']
    search_fields = ['membership__user__username', 'notes']
    date_hierarchy = 'date'

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['chama', 'transaction_type', 'amount', 'date', 'purpose', 'created_by']
    list_filter = ['transaction_type', 'date', 'created_at']
    search_fields = ['chama__name', 'purpose', 'description']
    date_hierarchy = 'date'

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['chama', 'title', 'created_by', 'is_important', 'created_at']
    list_filter = ['is_important', 'created_at']
    search_fields = ['title', 'content', 'chama__name']

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'recipient', 'subject', 'chama', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['subject', 'content', 'sender__username', 'recipient__username']
