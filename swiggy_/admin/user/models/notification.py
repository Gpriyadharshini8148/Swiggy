from django.db import models
from admin.access.models.base_model import BaseModel
from admin.access.models.users import Users

class Notification(BaseModel):
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    notification_type = models.CharField(max_length=50, default='General') # Order, Promo, General

    def __str__(self):
        return f"{self.user.username} - {self.title}"
