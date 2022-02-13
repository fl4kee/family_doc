from django.db import models


# Create your models here.
class WeatherInformation(models.Model):
    date = models.CharField(max_length=200)
    city = models.CharField(max_length=200)
    data = models.JSONField(default=None)
    country_code = models.CharField(max_length=20)
