from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Avg
from .models import Review, Restaurant

@receiver(post_save, sender=Review)
@receiver(post_delete, sender=Review)
def update_restaurant_rating(sender, instance, **kwargs):
    restaurant = instance.restaurant
    reviews = Review.objects.filter(restaurant=restaurant)
    
    if reviews.exists():
        avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
        restaurant.rating = round(avg_rating, 1)
    else:
        restaurant.rating = 0.0
    
    restaurant.save()
