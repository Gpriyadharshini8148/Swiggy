import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser
from django.http import HttpResponse
from tablib import Dataset
from admin.access.models import Users, Address, Rewards, Wishlist, State, City, Images
from admin.access.admin import UsersResource, AddressResource, RewardsResource, WishlistResource, StateResource, CityResource, ImagesResource
from admin.restaurants.models import Restaurant, FoodItem, Coupon, Category, SubCategory
from admin.restaurants.admin import RestaurantResource, FoodItemResource, CouponResource, CategoryResource, SubCategoryResource
from admin.delivery.models import DeliveryPartner, Orders, OrderItem
from admin.delivery.admin import DeliveryPartnerResource, OrdersResource, OrderItemResource

logger = logging.getLogger(__name__)

MODEL_REGISTRY = {
    'users': {'model': Users, 'resource': UsersResource},
    'address': {'model': Address, 'resource': AddressResource},
    'rewards': {'model': Rewards, 'resource': RewardsResource},
    'wishlist': {'model': Wishlist, 'resource': WishlistResource},
    'state': {'model': State, 'resource': StateResource},
    'city': {'model': City, 'resource': CityResource},
    'images': {'model': Images, 'resource': ImagesResource},
    'restaurant': {'model': Restaurant, 'resource': RestaurantResource},
    'fooditem': {'model': FoodItem, 'resource': FoodItemResource},
    'coupon': {'model': Coupon, 'resource': CouponResource},
    'category': {'model': Category, 'resource': CategoryResource},
    'subcategory': {'model': SubCategory, 'resource': SubCategoryResource},
    'deliverypartner': {'model': DeliveryPartner, 'resource': DeliveryPartnerResource},
    'orders': {'model': Orders, 'resource': OrdersResource},
    'orderitem': {'model': OrderItem, 'resource': OrderItemResource},
}

def get_allowed_queryset(user, model_name):
    """
    Returns the queryset for the given user role and model name.
    """
    if model_name not in MODEL_REGISTRY:
        return None
        
    config = MODEL_REGISTRY[model_name]
    model = config['model']
    base_qs = model.objects.all()
    
    if getattr(user, 'is_superuser', False) or getattr(user, 'role', None) == 'SUPERADMIN':
        return base_qs
        
    role = getattr(user, 'role', None)
    
    if role in ['RESTAURANT', 'RESTAURANT_ADMIN']:
        if model == Restaurant:
            return base_qs.filter(user=user)
        elif model == FoodItem:
            return base_qs.filter(restaurant__user=user)
        elif model == Orders:
            return base_qs.filter(restaurant__user=user)
        elif model == OrderItem:
            return base_qs.filter(order__restaurant__user=user)
        elif model == Coupon:
            if hasattr(model, 'restaurant'):
                return base_qs.filter(restaurant__user=user)
            return base_qs # If global default coupons exist
        elif model in [Category, SubCategory]:
            return base_qs # Read-only for global categories list
        return base_qs.none()
        
    elif role in ['DELIVERY', 'DELIVERY_ADMIN']:
        if model == DeliveryPartner:
            return base_qs.filter(user=user)
        elif model == Orders:
            return base_qs.filter(delivery_partner__user=user)
        return base_qs.none()
        
    return base_qs.none()

def enforce_import_data_rules(user, model_name, dataset):
    """
    Applies security logic to dataset during import ensuring non-superadmins 
    can only import data associated with themselves.
    """
    if getattr(user, 'is_superuser', False) or getattr(user, 'role', None) == 'SUPERADMIN':
        return True, dataset, None
        
    role = getattr(user, 'role', None)
    config = MODEL_REGISTRY[model_name]
    model = config['model']
    
    if role in ['RESTAURANT', 'RESTAURANT_ADMIN']:
        restaurant = Restaurant.objects.filter(user=user).first()
        if not restaurant:
            return False, dataset, "User has no associated restaurant profile."
            
        if model == FoodItem:
            if 'restaurant' in dataset.headers:
                del dataset['restaurant']
            dataset.append_col([str(restaurant.name)] * len(dataset), header='restaurant')
            return True, dataset, None
        elif model == Restaurant:
            if 'user' in dataset.headers:
                del dataset['user']
            dataset.append_col([user.id] * len(dataset), header='user')
            return True, dataset, None
        elif model == Coupon:
            if hasattr(model, 'restaurant'):
                if 'restaurant' in dataset.headers:
                    del dataset['restaurant']
                dataset.append_col([str(restaurant.name)] * len(dataset), header='restaurant')
            return True, dataset, None
        elif model in [Category, SubCategory]:
            return True, dataset, None # Can define global elements depending on app rules
            
        return False, dataset, "Restaurants are not authorized to import this data."
        
    if role in ['DELIVERY', 'DELIVERY_ADMIN']:
        if model == DeliveryPartner:
            if 'user' in dataset.headers:
                del dataset['user']
            dataset.append_col([user.id] * len(dataset), header='user')
            return True, dataset, None
        return False, dataset, "Delivery partners are not authorized to import this data."
        
    return False, dataset, "Permission denied for importing."


class GenericExportAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, model_name):
        model_name = model_name.lower().replace('-', '')
        if model_name not in MODEL_REGISTRY:
            return Response({"error": "Model not found or not registered for export."}, status=status.HTTP_404_NOT_FOUND)
            
        queryset = get_allowed_queryset(request.user, model_name)
        
        # If the queryset is forcefully empty and they aren't superadmin
        if not (getattr(request.user, 'is_superuser', False) or getattr(request.user, 'role', None) == 'SUPERADMIN'):
            if queryset is None or not queryset.exists():
                # Even if it's empty, we might just return an empty CSV to avoid leaking presence.
                # However, if it's .none() conceptually they don't have access.
                pass
                
        # Handle cases where model_name exists but role explicitly gets none()
        # We still return zero rows, which is correct behavior for RBAC filters.

        resource_class = MODEL_REGISTRY[model_name]['resource']
        resource = resource_class()
        
        dataset = resource.export(queryset)
        export_format = request.query_params.get('format', 'csv').lower()
        
        if export_format in ['xlsx', 'excel']:
            response = HttpResponse(dataset.xlsx, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = f'attachment; filename="{model_name}.xlsx"'
        elif export_format == 'xls':
            response = HttpResponse(dataset.xls, content_type='application/vnd.ms-excel')
            response['Content-Disposition'] = f'attachment; filename="{model_name}.xls"'
        else:
            response = HttpResponse(dataset.csv, content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{model_name}.csv"'
            
        return response


class GenericImportAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]
    
    def post(self, request, model_name):
        model_name = model_name.lower().replace('-', '')
        if model_name not in MODEL_REGISTRY:
            return Response({"error": "Model not found or not registered for import."}, status=status.HTTP_404_NOT_FOUND)
            
        file = request.FILES.get('file')
        if not file:
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)
            
        dataset = Dataset()
        try:
            file_extension = file.name.split('.')[-1].lower() if '.' in file.name else 'csv'
            if file_extension in ['xlsx', 'xls']:
                dataset.load(file.read(), format=file_extension)
            else:
                dataset.load(file.read().decode('utf-8'), format='csv')
        except Exception as e:
            logger.error(f"Failed to parse file: {e}")
            return Response({"error": f"Failed to parse file: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
            
        is_allowed, dataset, error_msg = enforce_import_data_rules(request.user, model_name, dataset)
        if not is_allowed:
            return Response({"error": error_msg}, status=status.HTTP_403_FORBIDDEN)
            
        resource_class = MODEL_REGISTRY[model_name]['resource']
        resource = resource_class()
        
        result = resource.import_data(dataset, dry_run=True)
        
        if not result.has_errors():
            resource.import_data(dataset, dry_run=False)
            return Response({"message": f"Successfully imported {len(dataset)} {model_name} records."})
        else:
            errors = []
            for i, row_errors in enumerate(result.row_errors()):
                for error in row_errors[1]:
                    errors.append(f"Row {row_errors[0]}: {str(error.error)}")
            return Response({"error": "Import failed", "details": errors}, status=status.HTTP_400_BAD_REQUEST)
