from django.db import models


class Place(models.Model):
    place = models.CharField(
        verbose_name='Наименование локации',
        unique=True,
        max_length=150
    )
    lon = models.FloatField(
        verbose_name='Долгота'
    )
    lat = models.FloatField(
        verbose_name='Широта'
    )
