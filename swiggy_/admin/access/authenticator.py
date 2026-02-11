from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from admin.access.models import Users
from django.contrib.auth.models import User as AdminUser

def get_tokens_for_user(user):
    refresh = RefreshToken()
    refresh['user_id'] = user.id
    refresh['role'] = getattr(user, 'role', 'No Role')
    
    if isinstance(user, Users):
        refresh['user_type'] = 'custom'
    else:
        refresh['user_type'] = 'admin'
        
    print(f" Generated Tokens for User ID: {user.id} ({refresh['user_type']}) ")
    return {
        'refresh_token': str(refresh),
        'access_token': str(refresh.access_token),
    }

class CustomJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        try:
            user_id = validated_token['user_id']
            user_type = validated_token.get('user_type', 'custom') # Default to custom for backward compatibility
            
            if user_type == 'admin':
                user = AdminUser.objects.get(id=user_id)
                # Monkey-patch role onto AdminUser instance for consistent access
                user.role = 'SUPERADMIN' 
                return user
            else:
                user = Users.objects.get(id=user_id)
                return user
                
        except KeyError:
            raise InvalidToken('Token contained no recognized user identification')
        except Users.DoesNotExist:
            # Fallback check: if user_type was defaulted to custom but user might be admin (legacy token case or verify edge case)
            if user_type == 'custom':
                 try:
                     user = AdminUser.objects.get(id=user_id)
                     user.role = 'SUPERADMIN'
                     return user
                 except AdminUser.DoesNotExist:
                     pass
            raise AuthenticationFailed(f"User with ID {user_id} and type '{user_type}' not found", code='user_not_found')
        except AdminUser.DoesNotExist:
            raise AuthenticationFailed(f"Admin User with ID {user_id} not found", code='user_not_found')