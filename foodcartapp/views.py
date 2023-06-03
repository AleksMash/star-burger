import json
import traceback

from django.http import JsonResponse
from django.templatetags.static import static
from rest_framework import status
from rest_framework.decorators import APIView ,api_view
from rest_framework.response import Response

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


@api_view(['POST'])
def register_order(request):
    order_serialized: dict = request.data
    products = order_serialized.get('products')

    if products == None:
        return Response({'error': 'Products list is not presented or is null'},
                        status=status.HTTP_400_BAD_REQUEST)
    if not products:
        return Response({'error': 'Products list is empty'},
                        status=status.HTTP_400_BAD_REQUEST)
    if not isinstance(products, list):
        return Response({'error': 'Products are not represented as a list'},
                        status=status.HTTP_400_BAD_REQUEST)
    product_ids: list = []
    product_quantities: list = []
    for product in products:
        try:
            product_ids.append(product['product'])
            product_quantities.append(product['quantity'])
        except KeyError:
            return Response({'error': 'Invalid key in the "product-quantity" dictionary'},
                            status=status.HTTP_400_BAD_REQUEST)

    db_products = Product.objects.filter(pk__in=product_ids)
    if not len(db_products) == len(product_ids):
        return Response({'error': 'one ore more of the given product ids are not found in the database'},
                        status=status.HTTP_400_BAD_REQUEST)

    try:
        order = Order(
            first_name=order_serialized['firstname'],
            last_name=order_serialized['lastname'],
            phone_number=PhoneNumber.from_string(order_serialized['phonenumber'], region='RU'),
            address=order_serialized['address']
        )
        order.save()
        for i in range(len(product_ids)):
            ProductsInOrder.objects.create(
                product_id=product_ids[i],
                quantity=product_quantities[i],
                order=order
            )
    except Exception:
        return Response({'error': traceback.format_exc()},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response({}, status=status.HTTP_200_OK)
