# Generated by Django 3.2.15 on 2023-06-07 19:31

from django.db import migrations
from django.db.models import F
from django.db.models import Subquery, OuterRef

def get_price(apps, schema_editor):

    ProductsInOrder = apps.get_model('foodcartapp', 'ProductsInOrder')
    for product_in_order in ProductsInOrder.objects.all():
        product_in_order.price = product_in_order.product.price
        product_in_order.save(update_fields=['price'])

class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0042_productsinorder_price'),
    ]

    operations = [
        migrations.RunPython(get_price),
    ]
