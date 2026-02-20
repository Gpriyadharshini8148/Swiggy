from django.urls import path
from admin.delivery.views import RazorpayPaymentViewSet
from .views import (
    UserAuthViewSet,
    UserCartViewSet, 
    UserWishlistViewSet,
    list_restaurants_api, restaurant_menu_api,
    place_order_api, get_order_status_api, list_user_orders_api,
    push_notification_api, list_notifications_api, get_notification_detail_api,
    submit_review_api, restaurant_reviews_api,
    food_items_api, user_profile_api,
    initiate_payment_api, confirm_payment_api
)

urlpatterns = [
    # Auth
    path('auth/signup/', UserAuthViewSet.as_view({'post': 'signup'}), name='user_signup'),
    path('auth/verify-otp/', UserAuthViewSet.as_view({'post': 'verify_otp'}), name='user_verify_otp'),
    path('auth/login/', UserAuthViewSet.as_view({'post': 'login'}), name='user_login'),
    path('auth/logout/', UserAuthViewSet.as_view({'post': 'logout'}), name='user_logout'),
    path('profile/', user_profile_api, name='user_profile'),

    
    # Location
    path('user/location/', UserAuthViewSet.as_view({'post': 'set_location'}), name='user_set_location'),
    path('user/addresses/', UserAuthViewSet.as_view({'get': 'get_addresses'}), name='user_get_addresses'),
    
    # Restaurants
    path('restaurants/', list_restaurants_api, name='user_list_restaurants'),
    path('restaurants/<int:restaurant_id>/menu/', restaurant_menu_api, name='user_restaurant_menu'),
    path('restaurants/<int:restaurant_id>/reviews/', restaurant_reviews_api, name='user_restaurant_reviews'),
    path('food-items/', food_items_api, name='user_list_food_items'),
    
    # Cart
    path('cart/', UserCartViewSet.as_view({'get': 'my_cart'}), name='user_my_cart'),
    path('cart/toggle/', UserCartViewSet.as_view({'post': 'toggle'}), name='user_cart_toggle'),
    path('cart/price-summary/', UserCartViewSet.as_view({'get': 'price_summary'}), name='user_cart_price_summary'),
    # Wishlist
    path('wishlist/', UserWishlistViewSet.as_view({'get': 'my_wishlist'}), name='user_my_wishlist'),
    path('wishlist/toggle/', UserWishlistViewSet.as_view({'post': 'toggle'}), name='user_wishlist_toggle'),
    
    # Orders
    path('orders/create/', place_order_api, name='user_place_order'),
    path('orders/history/', list_user_orders_api, name='user_orders_history'),
    path('orders/<int:order_id>/status/', get_order_status_api, name='user_order_status'),
    
    # Payments
    path('payments/initiate/', initiate_payment_api, name='user_payment_initiate'), 
    path('payments/confirm/', confirm_payment_api, name='user_payment_confirm'),
    
    # Notifications
    path('notifications/push/', push_notification_api, name='user_push_notification'),
    path('notifications/', list_notifications_api, name='user_list_notifications'),
    path('notifications/<int:pk>/', get_notification_detail_api, name='user_notification_detail'),
    
    # Reviews
    path('reviews/', submit_review_api, name='user_submit_review'),
]
