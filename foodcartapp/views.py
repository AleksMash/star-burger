import json
import traceback

from django.http import JsonResponse
from django.templatetags.static import static

from phonenumber_field.phonenumber import PhoneNumber

from .models import Product, Order, ProductsInOrder


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
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
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


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
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def register_order(request):
    try:
        order_serialized = json.loads(request.body.decode())
        order = Order(
            first_name=order_serialized['firstname'],
            last_name=order_serialized['lastname'],
            phone_number=PhoneNumber.from_string(order_serialized['phonenumber'], region='RU'),
            address=order_serialized['address']
        )
        order.save()
        print(order_serialized['products'])
        for order_product in order_serialized['products']:
            ProductsInOrder.objects.create(
                product_id=order_product['product'],
                order=order,
                quantity=order_product['quantity'],
            )
    except Exception:
        return JsonResponse({'error': traceback.format_exc()})
    return JsonResponse({})
