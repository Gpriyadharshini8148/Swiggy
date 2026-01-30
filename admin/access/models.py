from django.db import models
from admin.models import BaseModel
from admin.users.models import Users

class UserAuth(BaseModel):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    auth_type = models.CharField(max_length=50)
    password_hash = models.TextField(null=True, blank=True)
    otp = models.CharField(max_length=10, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    last_login = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Auth for {self.user}"
