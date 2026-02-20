from rest_framework import viewsets, status, permissions
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from admin.restaurants.models import Restaurant
from django.db.models import Q, Count
from admin.delivery.models.orders import Orders
from admin.restaurants.serializers import RestaurantSerializer, RestaurantOrderSerializer
from admin.access.models import Users     
from admin.restaurants.models.review import Review
from admin.restaurants.serializers import ReviewSerializer
from django.db.models import Sum 
import random     

class IsRestaurantOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        print(f"User: {request.user}, Role: {getattr(request.user, 'role', 'No Role')}, Superuser: {getattr(request.user, 'is_superuser', False)}")
        
        if getattr(request.user, 'is_superuser', False):
            return True
            
        return request.user and request.user.is_authenticated and (getattr(request.user, 'role', None) in ['RESTAURANT', 'RESTAURANT_ADMIN', 'SUPERADMIN'])

class RestaurantDashboardViewSet(viewsets.ViewSet):
    permission_classes = [IsRestaurantOwner]

    def get_restaurant(self, request):
        # Handle Super Admin (Django User)
        if getattr(request.user, 'is_superuser', False) or getattr(request.user, 'role', None) == 'SUPERADMIN':
            restaurant_id = request.query_params.get('restaurant_id')
            if restaurant_id:
                try:
                    return Restaurant.objects.get(id=restaurant_id)
                except Restaurant.DoesNotExist:
                    pass
            return None
        # Handle Restaurant User (Custom Users model)
        try:
            # Verify if request.user is an instance of the custom Users model
            if isinstance(request.user, Users):
                return Restaurant.objects.get(user=request.user)
            return None
        except Restaurant.DoesNotExist:
            return None

    def list(self, request):
        return Response({
            "profile": request.build_absolute_uri("profile/"),
            "orders": request.build_absolute_uri("orders/"),
            "dashboard_stats": request.build_absolute_uri("dashboard_stats/"),
            "reviews": request.build_absolute_uri("reviews/"),
        })

    @action(detail=False, methods=['get', 'put', 'patch'])
    def profile(self, request):
        restaurant = self.get_restaurant(request)
        if not restaurant:
            return Response({"error": "Restaurant profile not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if request.method == 'GET':
            serializer = RestaurantSerializer(restaurant)
            return Response(serializer.data)
        
        elif request.method in ['PUT', 'PATCH']:
            serializer = RestaurantSerializer(restaurant, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    @action(detail=False, methods=['get'])
    def orders(self, request):
        restaurant = self.get_restaurant(request)
        
        # If Super Admin and no restaurant_id provided, show ALL orders or filter by param
        if not restaurant:
             if getattr(request.user, 'is_superuser', False) or getattr(request.user, 'role', None) == 'SUPERADMIN':
                 # List all orders for Super Admin if no specific restaurant selected
                 orders = Orders.objects.select_related('user', 'address', 'address__city', 'address__state').order_by('-created_at')
             else:
                 return Response({"error": "Restaurant profile not found"}, status=status.HTTP_404_NOT_FOUND)
        else:
            orders = Orders.objects.filter(restaurant=restaurant).select_related('user', 'address', 'address__city', 'address__state').order_by('-created_at')
        
        status_filter = request.query_params.get('status')
        
        if status_filter:
            orders = orders.filter(order_status=status_filter.upper())
            
        paginator = PageNumberPagination()
        paginator.page_size = 10
        paginator.page_size_query_param = 'page_size'
        result_page = paginator.paginate_queryset(orders, request)
        serializer = RestaurantOrderSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @action(detail=True, methods=['post'])
    def update_order_status_detail(self, request, pk=None):
        restaurant = self.get_restaurant(request)
        if not restaurant:
            return Response({"error": "Restaurant profile not found"}, status=status.HTTP_404_NOT_FOUND)
            
        try:
            order = Orders.objects.get(id=pk, restaurant=restaurant)
        except Orders.DoesNotExist:
             return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
             
        new_status = request.data.get('status')
        if not new_status:
             return Response({"error": "Status is required"}, status=status.HTTP_400_BAD_REQUEST)
             
        new_status = new_status.upper()
        if new_status not in dict(Orders.ORDER_STATUS_CHOICES):
             return Response({"error": "Invalid Status"}, status=status.HTTP_400_BAD_REQUEST)
        # Logic for timestamp updates
        if new_status == 'ACCEPTED':
            if order.order_status != 'PENDING':
                return Response({"error": "Can only accept pending orders"}, status=status.HTTP_400_BAD_REQUEST)
        elif new_status == 'CANCELLED': # Reject logic
             if order.order_status == 'DELIVERED':
                 return Response({"error": "Cannot cancel delivered orders"}, status=status.HTTP_400_BAD_REQUEST)
             # Basic Refund Logic Placeholder
             if order.payment_status == 'PAID':
                 # Initiate Refund via Razorpay/Gateway
                 pass
             order.payment_status = 'REFUNDED'
             
        elif new_status == 'PREPARING':
            order.preparation_timestamp = timezone.now()
        elif new_status == 'READY':
            order.ready_timestamp = timezone.now()
            # Generate 6-digit OTP
            order.handover_otp = f"{random.randint(100000, 999999)}" 
            # In a real app, you would send this OTP to the delivery partner via notification/SMS here.
        elif new_status == 'PICKED_UP':
             order.pickup_timestamp = timezone.now()
             # Logic to assign delivery partner could be triggered here or separate
        elif new_status == 'DELIVERED':
             order.delivered_timestamp = timezone.now()
             order.payment_status = 'PAID' # Assuming Prepaid settled
        
        order.order_status = new_status
        order.save()
        
        return Response({"message": f"Order status updated to {new_status}"})

    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        restaurant = self.get_restaurant(request)
        if not restaurant:
            return Response({"error": "Restaurant profile not found"}, status=status.HTTP_404_NOT_FOUND)
            
        today = timezone.now().date()
        today_orders = Orders.objects.filter(restaurant=restaurant, created_at__date=today)
        
        
        
        stats = today_orders.aggregate(
            total_orders=Count('id'),
            revenue=Sum('total_amount', filter=Q(order_status__in=['DELIVERED', 'COMPLETED']))
        )
        
        # Manually count status-specific queries or use conditional aggregation if Django version supports (ref django.db.models.functions)
        completed_orders = today_orders.filter(order_status='DELIVERED').count()
        pending_orders = today_orders.filter(order_status='PENDING').count()
        
        revenue = stats['revenue'] or 0
        total_orders = stats['total_orders']
        
        return Response({
            "today_orders": total_orders,
            "completed_orders": completed_orders,
            "pending_orders": pending_orders,
            "today_revenue": revenue
        })
    @action(detail=False, methods=['get'])
    def earnings(self, request):
        restaurant = self.get_restaurant(request)
        if not restaurant:
            return Response({"error": "Restaurant profile not found"}, status=status.HTTP_404_NOT_FOUND)
            
        today = timezone.now().date()
        # You might want to allow filtering by date range here
        
        # Calculate daily earnings
        today_orders = Orders.objects.filter(restaurant=restaurant, created_at__date=today, order_status='DELIVERED')
        daily_revenue = today_orders.aggregate(total=Sum('total_amount'))['total'] or 0
        
        # Simple Logic
        # Platform Commission: 20%
        # GST: 18% (on commission or total? usually on food bill, but let's say 5% GST on food + commission)
        # Let's approximate for the dashboard view
        
        platform_commission = float(daily_revenue) * 0.20
        taxes = float(daily_revenue) * 0.05 # 5% GST on food
        net_earnings = float(daily_revenue) - platform_commission - taxes
        
        return Response({
            "daily_revenue": daily_revenue,
            "platform_commission": platform_commission,
            "taxes": taxes,
            "net_earnings": net_earnings,
            "date": today
        })

    @action(detail=False, methods=['patch'])
    def status(self, request):
        restaurant = self.get_restaurant(request)
        if not restaurant:
            return Response({"error": "Restaurant profile not found"}, status=status.HTTP_404_NOT_FOUND)
            
        # Toggle is_active or use a dedicated 'is_open' field if model has one.
        # Check model: Restaurant has 'is_active'. Let's use that for Open/Close for now.
        
        is_open = request.data.get('is_open')
        if is_open is None:
             return Response({"error": "is_open field is required (boolean)"}, status=status.HTTP_400_BAD_REQUEST)
             
        restaurant.is_active = is_open
        restaurant.save()
        
        status_text = "OPEN" if restaurant.is_active else "CLOSED"
        return Response({"message": f"Restaurant is now {status_text}", "is_active": restaurant.is_active})
        
    @action(detail=False, methods=['get'])
    def reviews(self, request):
        restaurant = self.get_restaurant(request)
        if not restaurant:
            return Response({"error": "Restaurant profile not found"}, status=status.HTTP_404_NOT_FOUND)
        reviews = Review.objects.filter(restaurant=restaurant).select_related('user').order_by('-created_at')
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)
