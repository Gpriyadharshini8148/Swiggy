from django.db.models.signals import post_save
from django.dispatch import receiver
from admin.users.models import Users
from admin.access.models import UserAuth

@receiver(post_save, sender=Users)
def create_user_auth(sender, instance, created, **kwargs):
    if created:
        auth_type_mapping = {
            'USER': 'USER',
            'ADMIN': 'ADMIN',
            'SUPERADMIN': 'ADMIN',
        }
        assigned_auth_type = 'USER' 
        if instance.role == 'ADMIN':
            if instance.admin_type == 'RESTAURANT':
                assigned_auth_type = 'RESTAURANT'
            elif instance.admin_type == 'DELIVERY':
                assigned_auth_type = 'DELIVERY'
            else:
                assigned_auth_type = 'ADMIN'
        elif instance.role == 'SUPERADMIN':
            assigned_auth_type = 'SUPERADMIN'
            
        UserAuth.objects.create(
            user=instance, 
            auth_type=assigned_auth_type
        )
