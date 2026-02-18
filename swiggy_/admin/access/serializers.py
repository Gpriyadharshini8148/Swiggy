from rest_framework import serializers
from .models import Users, Address, Wishlist, Rewards, City, State
from admin.restaurants.models.restaurant import Restaurant
from django.contrib.auth.models import User as AdminUser
from django.contrib.auth.hashers import check_password
from django.contrib.auth.password_validation import validate_password
import re
from django.db.models import Q
from django.core.cache import cache
from admin.delivery.models.delivery_partner import DeliveryPartner
from admin.restaurants.models.restaurant import Restaurant
class UsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        model = Users
        fields = ['id', 'role', 'username', 'email', 'phone', 'is_verified', 'is_logged_in', 'profile_image', 'last_login', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['role', 'is_verified', 'is_logged_in', 'last_login', 'is_active', 'created_at', 'updated_at', 'created_by', 'updated_by', 'deleted_by', 'deleted_at']

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'user', 'city', 'state', 'address_line_1', 'address_line_2', 'landmark', 'pincode', 'is_default', 'address_tag', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class WishlistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wishlist
        fields = '__all__'

class RewardsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rewards
        fields = '__all__'

class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = '__all__'

class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = '__all__'



class VerifyOtpSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=100, help_text="Email or Phone Number")
    otp = serializers.CharField(max_length=6)
    
    def validate(self, attrs):
        username = attrs.get('username')
        otp = attrs.get('otp')
        
        user = None
        if '@' in username:
             user = Users.objects.filter(email=username).first()
        else:
             user = Users.objects.filter(phone=username).first()
        
        if user:
            attrs['user'] = user
        
        return attrs

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(max_length=15, required=False)
    password = serializers.CharField(max_length=128, write_only=True)

class UnifiedLoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=100, help_text="Email or Phone Number")
    password = serializers.CharField(max_length=128)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        user = None
        if '@' in username:
            username = username.lower()
            user = Users.objects.filter(email=username).first()
        else:
            user = Users.objects.filter(phone=username).first()
            
        if not user:
            # Check for Super Admin (Django User)
            try:
                admin_user = None
                if '@' in username:
                    admin_user = AdminUser.objects.filter(email=username).first()
                else:
                    admin_user = AdminUser.objects.filter(username=username).first()
                
                if admin_user and check_password(password, admin_user.password):
                    admin_user.role = 'SUPERADMIN' 
                    attrs['user'] = admin_user
                    return attrs
            except Exception:
                pass

            # Check for Approved but NOT yet created user in Cache
            activation_data = cache.get(f"approved_activation_{username}")
            if activation_data:
                data = activation_data['data']
                if check_password(password, data['password_hash']):
                    act_type = activation_data['type']
                    
                    # Create User
                    user = Users.objects.create(
                        email=data.get('email'),
                        phone=data.get('phone'),
                        username=data.get('name') or data.get('restaurant_name') or data.get('username'),
                        role=data.get('role', 'ADMIN'),
                        password_hash=data['password_hash'],
                        is_verified=True,
                        created_by=data.get('created_by')
                    )

                    # Create Specific Profiles if needed
                    if act_type == 'restaurant':
                        # user.role is already set via data['role'] which should be RESTAURANT_ADMIN
                        user.save()
                        city = City.objects.get(id=data['city_id'])
                        state = State.objects.get(id=data['state_id']) if data.get('state_id') else None
                        Restaurant.objects.create(
                            user=user,
                            name=data['restaurant_name'],
                            location=data['location'],
                            address=data['address'],
                            city=city,
                            state=state,
                            category=data.get('category'),
                            is_active=True
                        )

                    
                    # Clear cache
                    cache.delete(f"approved_activation_{username}")
                    attrs['user'] = user
                    return attrs
                else:
                    raise serializers.ValidationError("Invalid Password")

            raise serializers.ValidationError(f"User '{username}' not found. If this is a new account, it may still be pending approval or the approval link may have expired.")
             
        if user.password_hash and check_password(password, user.password_hash):
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError("Invalid Password")

class SignupSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=100, help_text="Email or Phone Number")
    password = serializers.CharField(max_length=128, required=True)

    def validate(self, data):
        username = data.get('username')
        if not username:
             raise serializers.ValidationError("Username is required")

        email = None
        phone = None
        
        if '@' in username:
            email = username
            email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_regex, email):
                raise serializers.ValidationError("Enter a valid email address.")
        else:
            phone = username
            if not phone.isdigit():
                 raise serializers.ValidationError("Enter a valid phone number (digits only) or email address.")
            
        # Combine queries to check if user already exists
        query = Q()
        if email:
            query |= Q(email=email)
        if phone:
            query |= Q(phone=phone)
            
        if query:
            existing_user = Users.objects.filter(query).only('email', 'phone').first()
            if existing_user:
                if email and existing_user.email == email:
                    raise serializers.ValidationError("User with this email already exists")
                if phone and existing_user.phone == phone:
                    raise serializers.ValidationError("User with this phone already exists")
            
        password = data.get('password')
        if password:
             # Password complexity validation
            password_regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
            if not re.match(password_regex, password):
                 raise serializers.ValidationError("Password must contain at least 8 characters, one uppercase letter, one lowercase letter, one number and one special character.")

            try:
                validate_password(password)
            except Exception as e:
                raise serializers.ValidationError(str(e))
            
        return data

class LogoutSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=100, help_text="Email or Phone Number")
    def validate(self, attrs):
        username = attrs.get('username')
        user = None
        admin_user = None 
        if '@' in username:
            user = Users.objects.filter(email=username).first()
        else:
            user = Users.objects.filter(phone=username).first()
        if not user and '@' in username:
             admin_user = AdminUser.objects.filter(email=username).first()
        if not user and not admin_user:
            raise serializers.ValidationError("User not found")
            
        attrs['user'] = user
        attrs['admin_user'] = admin_user
        return attrs
class CreateAccountSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=100, help_text="Email or Phone Number")
    password = serializers.CharField(max_length=128, required=True)
    role = serializers.ChoiceField(choices=Users.ROLE_CHOICES)
    role = serializers.ChoiceField(choices=Users.ROLE_CHOICES)

    def validate(self, data):
        username = data.get('username')
        if not username:
            raise serializers.ValidationError("Username is required")

        email = None
        phone = None
        
        if '@' in username:
            email = username
            email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_regex, email):
                raise serializers.ValidationError("Enter a valid email address.")
        else:
            phone = username
            if not phone.isdigit():
                 raise serializers.ValidationError("Enter a valid phone number (digits only) or email address.")
            
        if email and Users.objects.filter(email=email).exists():
            raise serializers.ValidationError("User with this email already exists")
            
        if phone and Users.objects.filter(phone=phone).exists():
            raise serializers.ValidationError("User with this phone already exists")
            
        try:
            validate_password(data['password'])
        except Exception as e:
            raise serializers.ValidationError(str(e))
            
        return data
class RestaurantSignupSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=100, help_text="User Email or Phone Number")
    password = serializers.CharField(max_length=128, required=True, write_only=True)
    restaurant_name = serializers.CharField(max_length=255)
    location = serializers.CharField(max_length=255)
    address = serializers.CharField(required=False, allow_blank=True)
    city_id = serializers.IntegerField()
    state_id = serializers.IntegerField(required=False, allow_null=True)
    category = serializers.CharField(max_length=100, required=False, allow_blank=True)
    
    def validate(self, data):
        username = data.get('username')
        if not username:
             raise serializers.ValidationError("Username is required")

        email = None
        phone = None
        
        if '@' in username:
            email = username
            # Email format validation
            email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_regex, email):
                raise serializers.ValidationError("Enter a valid email address.")
        else:
            phone = username
            if not phone.isdigit():
                 raise serializers.ValidationError("Enter a valid phone number (digits only) or email address.")
        if email and Users.objects.filter(email=email).exists():
            raise serializers.ValidationError("User with this email already exists")
            
        if phone and Users.objects.filter(phone=phone).exists():
            raise serializers.ValidationError("User with this phone already exists")
            
        password = data['password']
        # Password complexity validation
        password_regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
        if not re.match(password_regex, password):
             raise serializers.ValidationError("Password must contain at least 8 characters, one uppercase letter, one lowercase letter, one number and one special character")

        try:
            validate_password(password)
        except Exception as e:
            raise serializers.ValidationError(str(e))
            
        return data

