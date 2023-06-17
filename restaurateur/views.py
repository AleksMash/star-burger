from django import forms
from django.db.models import F, Q, Count, ObjectDoesNotExist
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
from geodata.models import Place

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

def get_distance(places: tuple, places_cache: dict = None):
    '''
    get the distance between two places using GeoPy and Yandex geocoder
    first trying to get coordinates in the following order:
     - from places_cache (if given), from DB, from Yandex geocoder
    :param places: tuple of two places: str
    :param places_cache: if given, coordinates are searched here first
    :return: distance in km
    '''
    if not len(places) == 2 or not (places[0] and places[1]) :
        raise ValueError()
    coordinates = []
    for place in places:
        try:
            coordinates.append(places_cache[place])
        except Exception:
            try:
                lon, lat = Place.objects.values_list('lon', 'lat').get(place=place)
            except ObjectDoesNotExist:
                lon, lat = fetch_coordinates(YNDX_GEO_API_KEY, place)
                if not (lon and lat):
                    raise ValueError
                Place.objects.create(place=place, lon=lon, lat=lat)
            coordinates.append((lat, lon))
            if not places_cache is None:
                places_cache[place] = (lat, lon)
    return dist.distance(coordinates[0], coordinates[1]).km


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
    orders = Order.objects.orders_for_manager()
    menu_items = RestaurantMenuItem.objects.filter(availability=True).values('restaurant', 'product')
    product_restaurans_cache = {}
    places_cache = {}
    for order in orders:
        if order.restaurant is None:
            # product_ids = order.products.values_list('id', flat=True).all()
            first_product_id = order.products.all()[0].product.id
            restaurants_for_product = product_restaurans_cache.get(first_product_id)
            if not restaurants_for_product:
                restaurants_for_product = list(menu_items.filter(product__id=first_product_id) \
                    .values_list('restaurant__id', 'restaurant__name', 'restaurant__address'))
                product_restaurans_cache[first_product_id] = restaurants_for_product
            order_restaurants = restaurants_for_product
            if order.products_count > 1:
                for product in order.products.all()[1:]:
                    restaurants_for_product = product_restaurans_cache.get(product.product.id)
                    if not restaurants_for_product:
                        restaurants_for_product = list(menu_items.filter(product=product.id)\
                            .values_list('restaurant__id','restaurant__name','restaurant__address'))
                        product_restaurans_cache[product.id] = restaurants_for_product
                    product_restaurant_ids = [t[0] for t in restaurants_for_product]
                    order_restaurants = list(
                        filter(lambda item: item[0] in product_restaurant_ids, order_restaurants)
                    )
                    if not order_restaurants:
                        break
            order_restaurants = list(map(lambda v: list(v), order_restaurants))
            for restaurant in order_restaurants:
                try:
                    distance = round(get_distance((restaurant[2], order.address), places_cache),0)
                except Exception:
                    restaurant.append('error')
                else:
                    restaurant.append(distance)
            if len(order_restaurants) > 1:
                order.restaurants_capable = sorted(order_restaurants, key=lambda v: v[3])
            else:
                order.restaurants_capable = order_restaurants
        else:
            order.restaurant_appointed = order.restaurant.name
    return render(request, template_name='order_items.html', context={
        'order_items': orders
    })
