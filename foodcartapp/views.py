import json
import traceback

from django.templatetags.static import static
from django.db import transaction, IntegrityError
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from rest_framework.serializers import ValidationError

from .models import Product, Order, ProductsInOrder

from geodata.models import Place

@api_view(['GET'])
def banners_list_api(request):
    # FIXME move data to db?
    return Response([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ])


@api_view(['GET'])
def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return Response(dumped_products)


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

    def create(self, validated_data):
        products = validated_data.pop('products')
        order = Order.objects.create(**validated_data)
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


@api_view(['POST'])
def register_order(request):
    serializer = OrderSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        with transaction.atomic():
            order = serializer.create(serializer.validated_data)
    except Exception:
        return Response({'error': traceback.format_exc()},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        serializer = OrderSerializer(order)
        return Response(serializer.data)
