from rest_framework.serializers import ModelSerializer
from django.db import transaction

from .models import Order, ProductsInOrder


class ProductsInOrderSerializer(ModelSerializer):
    class Meta:
        model = ProductsInOrder
        fields = ['product', 'quantity']



class OrderSerializer(ModelSerializer):
    products = ProductsInOrderSerializer(many=True, write_only=True, allow_empty=False)

    def create(self, validated_data=None):
        products = self.validated_data.pop('products')
        address= self.validated_data['address']
        self.validated_data['address'] = ' '.join(address.split())
        order = Order.objects.create(**self.validated_data)

        with transaction.atomic():
            products_fields = [dict(**fields) for fields in products]
            products_in_order_prepared = [
                ProductsInOrder(order=order, price=fields['product'].price, **fields) for fields in products_fields
            ]
            ProductsInOrder.objects.bulk_create(products_in_order_prepared)
        return order

    class Meta:
        model = Order
        fields = ['products','firstname', 'lastname', 'address', 'phonenumber']