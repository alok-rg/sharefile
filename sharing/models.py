from django.db import models
from django.utils import timezone
import uuid


class OnlineUser(models.Model):
    """Represents an online user in the file sharing pool"""
    session_id = models.CharField(max_length=100, unique=True)
    username = models.CharField(max_length=100)
    joined_at = models.DateTimeField(default=timezone.now)
    last_seen = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-joined_at']
    
    def __str__(self):
        return f"{self.username} ({self.session_id})"


class FileTransfer(models.Model):
    """Represents a file transfer request between users"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    transfer_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    sender_session = models.CharField(max_length=100)
    sender_username = models.CharField(max_length=100)
    receiver_session = models.CharField(max_length=100)
    receiver_username = models.CharField(max_length=100)
    filename = models.CharField(max_length=255)
    filesize = models.BigIntegerField()  # Size in bytes
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.filename} from {self.sender_username} to {self.receiver_username}"
    
    def get_filesize_display(self):
        """Return human-readable file size"""
        size = self.filesize
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"
