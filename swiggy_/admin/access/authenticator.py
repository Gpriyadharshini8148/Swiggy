from rest_framework_simplejwt.tokens import RefreshToken

def get_tokens_for_user(user):
    # Manually create tokens for custom User model to avoid "OutstandingToken" foreign key constraint errors
    # if the custom User model is not the default AUTH_USER_MODEL.
    refresh = RefreshToken()
    refresh['user_id'] = user.id
    refresh['role'] = user.role
    print(f"-------- Generated Tokens for User ID: {user.id} --------")
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }