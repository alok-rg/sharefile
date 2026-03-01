from django.contrib import admin
from .models import OnlineUser, FileTransfer


@admin.register(OnlineUser)
class OnlineUserAdmin(admin.ModelAdmin):
    list_display = ['username', 'session_id', 'joined_at', 'last_seen']
    search_fields = ['username', 'session_id']
    list_filter = ['joined_at']


@admin.register(FileTransfer)
class FileTransferAdmin(admin.ModelAdmin):
    list_display = ['filename', 'sender_username', 'receiver_username', 'status', 'created_at']
    search_fields = ['filename', 'sender_username', 'receiver_username']
    list_filter = ['status', 'created_at']
    readonly_fields = ['transfer_id', 'created_at', 'updated_at']
