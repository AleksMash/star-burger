import json
import traceback

from django.http import JsonResponse
from django.templatetags.static import static
from rest_framework import status
from rest_framework.decorators import APIView ,api_view
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from rest_framework.serializers import ValidationError

from phonenumber_field.phonenumber import PhoneNumber

from .models import Product, Order, ProductsInOrder

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
    products = ProductsInOrderSerializer(many=True)

    def validate_products(self, values):
        if not values:
            raise ValidationError('Этот список не может быть пустым')
        return values

    class Meta:
        model = Order
        fields = ['products','firstname', 'lastname', 'address', 'phonenumber']


@api_view(['POST'])
def register_order(request):
    serializer = OrderSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        order = Order(
            firstname=serializer.validated_data['firstname'],
            lastname=serializer.validated_data['lastname'],
            phonenumber=serializer.validated_data['phonenumber'],
            address=serializer.validated_data['address']
        )
        order.save()
        products_in_order_fields = serializer.validated_data['products']
        products_in_order = [ProductsInOrder(order=order, **fields) for fields in products_in_order_fields]
        ProductsInOrder.objects.bulk_create(products_in_order)
    except Exception:
        return Response({'error': traceback.format_exc()},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response({}, status=status.HTTP_200_OK)
