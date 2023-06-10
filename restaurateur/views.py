from django import forms
from django.db.models import F, Q, Count
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views
from django.conf import settings

import requests

from geopy import distance as dist

from foodcartapp.models import Product, Restaurant, Order, RestaurantMenuItem

YNDX_GEO_API_KEY = settings.YNDX_GEO_API_KEY


def fetch_coordinates(apikey, address):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(base_url, params={
        "geocode": address,
        "apikey": apikey,
        "format": "json",
    })
    response.raise_for_status()
    found_places = response.json()['response']['GeoObjectCollection']['featureMember']

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lon, lat

def get_distance(place_1, place_2):
    if not (place_1 and place_2):
        raise ValueError('Оба или один из адресов представлен пустой строкой')
    lon_1, lat_1 = fetch_coordinates(YNDX_GEO_API_KEY, place_1)
    lon_2, lat_2 = fetch_coordinates(YNDX_GEO_API_KEY, place_2)
    return dist.distance((lat_1, lon_1), (lat_2, lon_2)).km


class Login(forms.Form):
    username = forms.CharField(
        label='Логин', max_length=75, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Укажите имя пользователя'
        })
    )
    password = forms.CharField(
        label='Пароль', max_length=75, required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "login.html", context={
            'form': form
        })

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(request, "login.html", context={
            'form': form,
            'ivalid': True,
        })


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_products(request):
    restaurants = list(Restaurant.objects.order_by('name'))
    products = list(Product.objects.prefetch_related('menu_items'))

    products_with_restaurant_availability = []
    for product in products:
        availability = {item.restaurant_id: item.availability for item in product.menu_items.all()}
        ordered_availability = [availability.get(restaurant.id, False) for restaurant in restaurants]

        products_with_restaurant_availability.append(
            (product, ordered_availability)
        )

    return render(request, template_name="products_list.html", context={
        'products_with_restaurant_availability': products_with_restaurant_availability,
        'restaurants': restaurants,
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(request, template_name="restaurants_list.html", context={
        'restaurants': Restaurant.objects.all(),
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    orders = list(Order.objects.all().exclude(status=Order.DONE)\
        .prefetch_related('products', 'restaurant').cost().order_by('status'))
    menu_items = RestaurantMenuItem.objects.filter(availability=True).values('restaurant', 'product')
    product_restaurans_cache = {}
    restaurans_cache ={}
    for order in orders:
        if order.restaurant is None:
            order_restaurants={}
            for product in order.products.all():
                restaurants_for_product = product_restaurans_cache.get(product.id)
                if not restaurants_for_product:
                    restaurants_for_product = menu_items.filter(product=product)\
                        .values_list('restaurant__id', 'restaurant__name','restaurant__address' )
                    product_restaurans_cache[product.id] = restaurants_for_product
                for restaurant_id, *other_info in restaurants_for_product:
                    if not restaurant_id in order_restaurants:
                        other_info = list(other_info)
                        try:
                            distance = round(get_distance(other_info[1], order.address),0)
                        except Exception as e:
                            other_info.append('error')
                        else:
                            other_info.append(distance)
                        order_restaurants[restaurant_id] = other_info
            order.restaurants_capable = sorted(list(order_restaurants.values()), key=lambda d: d[2])
        else:
            order.restaurant_appointed = order.restaurant.name

    return render(request, template_name='order_items.html', context={
        'order_items': orders
    })
