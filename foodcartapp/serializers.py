from rest_framework.serializers import ModelSerializer
from rest_framework.serializers import ValidationError

from .models import Order, ProductsInOrder


class ProductsInOrderSerializer(ModelSerializer):
    class Meta:
        model = ProductsInOrder
        fields = ['product', 'quantity']


class OrderSerializer(ModelSerializer):
    products = ProductsInOrderSerializer(many=True, write_only=True)

    def validate_products(self, values):
        if not values:
            raise ValidationError('Этот список не может быть пустым')
        return values

    def validate_address(self, value: str):
        return ' '.join(value.split())

    def create(self, validated_data=None):
        return Order.objects.create(**self.validated_data)

    class Meta:
        model = Order
        fields = ['products','firstname', 'lastname', 'address', 'phonenumber']