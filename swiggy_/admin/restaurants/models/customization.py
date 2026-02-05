from django.db import models

class Customization(models.Model):
    suggestions = models.CharField(max_length=255)
    number_of_ingredients = models.IntegerField()
