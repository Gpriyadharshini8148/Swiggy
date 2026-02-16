from django.urls import path
from admin.restaurants.views import CartViewSet
from admin.delivery.views import RazorpayPaymentViewSet
from .views import (
    UserAuthViewSet,
    list_restaurants_api, restaurant_menu_api,
    place_order_api, get_order_status_api, list_user_orders_api,
    push_notification_api, list_notifications_api, mark_notification_read_api,
    submit_review_api, restaurant_reviews_api,
    food_items_api, user_profile_api
)

urlpatterns = [
    # Auth
    path('auth/signup', UserAuthViewSet.as_view({'post': 'signup'}), name='user_signup'),
    path('auth/verify-otp', UserAuthViewSet.as_view({'post': 'verify_otp'}), name='user_verify_otp'),
    path('auth/login', UserAuthViewSet.as_view({'post': 'login'}), name='user_login'),
    path('auth/logout', UserAuthViewSet.as_view({'post': 'logout'}), name='user_logout'),
    path('profile', user_profile_api, name='user_profile'),

    
    # Location
    path('user/location', UserAuthViewSet.as_view({'post': 'set_location'}), name='user_set_location'),
    path('user/addresses', UserAuthViewSet.as_view({'get': 'get_addresses'}), name='user_get_addresses'),
    
    # Restaurants
    path('restaurants', list_restaurants_api, name='user_list_restaurants'),
    path('restaurants/<int:restaurant_id>/menu', restaurant_menu_api, name='user_restaurant_menu'),
    path('restaurants/<int:restaurant_id>/reviews', restaurant_reviews_api, name='user_restaurant_reviews'),
    path('food-items', food_items_api, name='user_list_food_items'),
    
    # Cart
    path('cart/add', CartViewSet.as_view({'post': 'add_item'}), name='user_add_to_cart'),
    path('cart/price-summary', CartViewSet.as_view({'get': 'price_summary'}), name='user_cart_price_summary'),
    path('cart/clear', CartViewSet.as_view({'post': 'clear_cart'}), name='user_clear_cart'),
    
    # Orders
    path('orders', place_order_api, name='user_place_order'),
    path('orders/history', list_user_orders_api, name='user_orders_history'),
    path('orders/<int:order_id>/status', get_order_status_api, name='user_order_status'),
    
    # Payments
    path('payments/initiate', RazorpayPaymentViewSet.as_view({'post': 'create_order'}), name='user_payment_initiate'),
    path('payments/confirm', RazorpayPaymentViewSet.as_view({'post': 'verify_payment'}), name='user_payment_confirm'),
    
    # Notifications
    path('notifications/push', push_notification_api, name='user_push_notification'),
    path('notifications', list_notifications_api, name='user_list_notifications'),
    path('notifications/<int:notification_id>/read', mark_notification_read_api, name='user_mark_notification_read'),
    
    # Reviews
    path('reviews', submit_review_api, name='user_submit_review'),
]
