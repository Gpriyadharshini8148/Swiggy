from django.db import models
from admin.access.models import Images

class Category(models.Model):
    name = models.CharField(max_length=100)
    image = models.ForeignKey(Images, related_name='category_image', on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return self.name

class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=100)
    image = models.ForeignKey(Images, related_name='subcategory_image', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.category.name} -> {self.name}"
