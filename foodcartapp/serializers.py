from rest_framework.serializers import ModelSerializer
from django.db import transaction

from .models import Order, ProductsInOrder


class ProductsInOrderSerializer(ModelSerializer):
    class Meta:
        model = ProductsInOrder
        fields = ['product', 'quantity']



class OrderSerializer(ModelSerializer):
    products = ProductsInOrderSerializer(many=True, write_only=True, allow_empty=False)

    def validate_address(self, value: str):
        return ' '.join(value.split())

    def create(self, validated_data=None):
        print('Start create')
        products = self.validated_data.pop('products')
        order = Order.objects.create(**self.validated_data)
        with transaction.atomic():
            products_in_order_prepared = [ProductsInOrder(order=order, price=0, **fields) for fields in products]
            ProductsInOrder.objects.bulk_create(products_in_order_prepared)
            products_in_order_saved = list(ProductsInOrder.objects.filter(order=order))
            for product_in_order in products_in_order_saved:
                product_in_order.price = product_in_order.product.price
            ProductsInOrder.objects.bulk_update(products_in_order_saved, fields=['price'])
        return order

    class Meta:
        model = Order
        fields = ['products','firstname', 'lastname', 'address', 'phonenumber']