import json
import math
from collections import OrderedDict

from django.db.models import Case, Count, Sum, When
from django.http import JsonResponse
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import (
    permission_classes,
)
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import FileUploadParser, FormParser, MultiPartParser
from rest_framework.views import APIView

from foodtaskerapp.pagination import PaginationHandlerMixin
from .forms import RestaurantForm, UserFormForEdit
from .models import Driver, FoodType, Meal, Order, Restaurant, User
from .serializers import FoodTypeSerializer, MealSerializer, OrderSerializer, RestaurantSerializer, UserSerializer


###############
# RESTAURANTS
###############
class RegisterRestaurant(APIView):
    permission_classes([permissions.AllowAny])

    def post(self, request, *args, **kwargs):
        rest_data = OrderedDict(
            [
                ('name', request.POST.get('name')),
                ('phone', request.POST.get('phone')),
                ('address', request.POST.get('address')),
                ('logo', request.FILES.get('logo')),
            ]
        )
        user_data = OrderedDict(
            [
                ('first_name', request.POST.get('first_name')),
                ('last_name', request.POST.get('last_name')),
            ]
        )
        user_serializer = UserSerializer(data = user_data, partial = True)
        restaurant_serializer = RestaurantSerializer(data = rest_data)
        if restaurant_serializer.is_valid():
            user = user_serializer.update(instance = request.user, validated_data = user_data)
            restaurant = restaurant_serializer.save(user = request.user)
            return JsonResponse({"message": "Success"},
                                status = status.HTTP_201_CREATED)
        else:
            return JsonResponse({"error": {"restaurant": restaurant_serializer.errors}},
                                status = status.HTTP_400_BAD_REQUEST)


class BasicPagination(PageNumberPagination):
    page_size_query_param = 'limit'


class RestaurantViewSet(viewsets.ModelViewSet):
    queryset = Restaurant.objects.all()
    serializer_class = RestaurantSerializer

    def get_object(self):
        return self.queryset.get(id = self.kwargs['pk'])

    def create(self, request):
        name = request.POST.get("name", None)
        phone = request.POST.get("phone", None)
        address = request.POST.get("address", None)
        logo = request.FILES.get('logo', None)
        Restaurant.objects.create(user_id = self.request.user.id, name = name, phone = phone, address = address,
                                  logo = logo)
        return JsonResponse({"message": 'success'})


class AppViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_object(self):
        print(self.request.user)
        return JsonResponse({"test": 'test'})


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = UserSerializer(User.objects.get(
            auth_token = request.user.auth_token), many = False, context = {"request": request}).data
        restaurant = RestaurantSerializer(Restaurant.objects.get(
            id = request.user.restaurant.id), many = False, context = {"request": request}).data
        return JsonResponse({"user": user, "restaurant": restaurant})

    def post(self, request, *args, **kwargs):
        user_serializer = UserSerializer(request.user, data = request.data, partial = True)
        restaurant_serializer = RestaurantSerializer(request.user.restaurant, data = request.data, partial = True)
        if user_serializer.is_valid() & restaurant_serializer.is_valid():
            user_serializer.save()
            restaurant_serializer.save(user = request.user)
            return JsonResponse({"user": restaurant_serializer.data, "restaurant": restaurant_serializer.data},
                                status = status.HTTP_201_CREATED)
        else:
            return JsonResponse({"error": {"restaurant": restaurant_serializer.errors, "user": user_serializer.errors}},
                                status = status.HTTP_400_BAD_REQUEST)


class FoodTypeView(APIView, PaginationHandlerMixin):
    pagination_class = BasicPagination
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FoodTypeSerializer

    def post(self, request, *args, **kwargs):
        food_type_serializer = FoodTypeSerializer(data = request.data)
        food_type = FoodType.objects.filter(name = request.POST.get('name', None), restaurant = request.user.restaurant).last()

        if food_type is None:
            if food_type_serializer.is_valid():
                food_type_serializer.save(restaurant = request.user.restaurant)
                return JsonResponse({"success": "success"})
            else:
                return JsonResponse({"error": food_type_serializer.errors}, status = status.HTTP_400_BAD_REQUEST)
        else:
            return JsonResponse({"error": "You already have this food type"}, status = status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        instance = FoodType.objects.filter(
            restaurant = request.user.restaurant).order_by("-id")
        page = self.paginate_queryset(instance)
        if page is not None:
            serializer = self.get_paginated_response(
                self.serializer_class(page, many = True, context = {"request": request}).data)
        else:
            serializer = self.serializer_class(instance, many = True)
        return JsonResponse({"food_types": serializer.data})


def restaurant_account(request):
    user_form = UserFormForEdit(instance = request.user)
    restaurant_form = RestaurantForm(instance = request.user.restaurant)

    if request.method == "POST":
        user_form = UserFormForEdit(
            request.POST, instance = request.user)
        restaurant_form = RestaurantForm(
            request.POST,
            request.FILES,
            instance = request.user.restaurant)

        if user_form.is_valid() and restaurant_form.is_valid():
            user_form.save()
            restaurant_form.save()
    return JsonResponse(
        {"user_form": user_form,
         "restaurant_form": restaurant_form, }
    )


def restaurants_list(request):
    page = 1
    per_page = 3
    if 'page' in request.GET:
        page = int(request.GET['page'])
    if 'per_page' in request.GET:
        per_page = int(request.GET['per_page'])
    restaurant = RestaurantSerializer(
        # Restaurant.objects.all().order_by("-id"),
        Restaurant.objects.all().order_by("-id")[(page * per_page) - per_page:page * per_page],
        many = True,
        context = {"request": request},
    ).data

    total = Restaurant.objects.all().count()
    last_page = math.ceil(total / per_page)

    response = JsonResponse(
        {"data": restaurant, "current_page": page, "last_page": last_page, "per_page": per_page, "total": total})
    response["Access-Control-Allow-Origin"] = " "
    response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response["Access-Control-Max-Age"] = "1000"
    response["Access-Control-Allow-Headers"] = "X-Requested-With, Content-Type"
    return response


def restaurant_order_notification(request, last_viewed):
    notification = Order.objects.filter(
        restaurant = request.user.restaurant,
        created_at__gt = last_viewed,
    ).count()

    return JsonResponse({"notification": notification})


class OrderView(APIView, PaginationHandlerMixin):
    pagination_class = BasicPagination
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrderSerializer

    def post(self, request, *args, **kwargs):
        body = json.loads(request.body)
        order = Order.objects.get(
            id = body['id'],
            restaurant = request.user.restaurant)
        if order.status == Order.COOKING:
            order.status = Order.READY
            order.save()
            return JsonResponse({"success": "success"})
        if order.status == Order.READY:
            order.status = Order.ONTHEWAY
            order.save()
            return JsonResponse({"success": "success"})
        if order.status == Order.ONTHEWAY:
            order.status = Order.DELIVERED
            order.save()
            return JsonResponse({"success": "success"})

    def get(self, request, *args, **kwargs):
        instance = Order.objects.filter(
            restaurant = request.user.restaurant).order_by("-id")
        page = self.paginate_queryset(instance)
        if page is not None:
            serializer = self.get_paginated_response(
                self.serializer_class(page, many = True, context = {"request": request}).data)
        else:
            serializer = self.serializer_class(instance, many = True)
        return JsonResponse({"orders": serializer.data})


@permission_classes([permissions.IsAuthenticated])
def restaurant_order(request):
    if hasattr(request.user, 'restaurant'):
        if request.method == "POST":
            order = Order.objects.get(
                id = request.POST['id'],
                restaurant = request.user.restaurant)

            if order.status == Order.COOKING:
                order.status = Order.READY
                order.save()

        orders = OrderSerializer(Order.objects.filter(
            restaurant = request.user.restaurant).order_by("-id"), many = True, context = {"request": request}).data

        return JsonResponse({"orders": orders})
    return JsonResponse({'asd': 'asd'})


@permission_classes([permissions.IsAuthenticated])
def restaurant_edit_meal(request, meal_id):
    pass


class MealView(APIView, PaginationHandlerMixin):
    pagination_class = BasicPagination
    permission_classes = [permissions.IsAuthenticated]
    parser_class = (MultiPartParser, FormParser,)
    serializer_class = MealSerializer

    def post(self, request, *args, **kwargs):
        meal_serializer = MealSerializer(data = request.data)
        if meal_serializer.is_valid():
            meal_serializer.save(restaurant = request.user.restaurant)
            return JsonResponse({"success": meal_serializer.data}, status = status.HTTP_201_CREATED)
        else:
            return JsonResponse({"error": meal_serializer.errors}, status = status.HTTP_400_BAD_REQUEST)

    def patch(self, request, *args, **kwargs):
        meal = Meal.objects.get(id = request.POST.get('meal_id', None))
        meal_serializer = MealSerializer(meal, data = request.data, partial = True)
        if meal_serializer.is_valid():
            meal_serializer.update(instance = meal, validated_data = request.data)
            return JsonResponse({"success": meal_serializer.data}, status = status.HTTP_201_CREATED)
        else:
            return JsonResponse({"error": meal_serializer.errors}, status = status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        instance = Meal.objects.filter(
            restaurant = request.user.restaurant).order_by("-id")
        page = self.paginate_queryset(instance)
        if page is not None:
            serializer = self.get_paginated_response(
                self.serializer_class(page, many = True, context = {"request": request}).data)
        else:
            serializer = self.serializer_class(instance, many = True)
        return JsonResponse({"meals": serializer.data})


@permission_classes([permissions.IsAuthenticated])
def restaurant_meal(request):
    parser_classes = (FileUploadParser,)
    if request.method == "POST":
        name = request.POST.get('name')
        short_description = request.POST.get('short_description')
        price = request.POST.get('price')
        image = request.FILES['image']
        destination = open('media/meal/images/' + image.name, 'wb+')
        image_path = 'meal/images/' + image.name
        for chunk in image.chunks():
            destination.write(chunk)
        destination.close()
        formData = OrderedDict([('name', name),
                                ('short_description', short_description),
                                ('image', image_path),
                                ('price', price)
                                ])
        formDataSerializer = MealSerializer(data = formData)
        if (formDataSerializer.is_valid()):
            formDataSerializer.save(restaurant = request.user.restaurant)
            return JsonResponse({"message": "Success"})
        return JsonResponse({
            "message": 'Failed to add the meal'
        })
    if request.method == 'GET':
        meals = MealSerializer(Meal.objects.filter(
            restaurant = request.user.restaurant).order_by("-id"), many = True, context = {"request": request}).data
        return JsonResponse({"meals": meals})
    return JsonResponse({"message": "Incorrect request"})


@permission_classes([permissions.IsAuthenticated])
def restaurant_report(request, id):
    # Calculate revenue and number of order by current week
    from datetime import datetime, timedelta

    revenue = []
    orders = []

    # Calculate weekdays
    today = datetime.now()
    current_weekdays = (
        today +
        timedelta(
            days = i) for i in range(
        0 -
        today.weekday(),
        7 -
        today.weekday()))

    for day in current_weekdays:
        delivered_orders = Order.objects.filter(
            restaurant = request.user.restaurant,
            status = Order.DELIVERED,
            created_at__year = day.year,
            created_at__month = day.month,
            created_at__day = day.day,
        )

        revenue.append(sum(order.total for order in delivered_orders))
        orders.append(delivered_orders.count())

    # Top 3 Meals
    top3_meals = Meal.objects.filter(restaurant = request.user.restaurant) \
                     .annotate(total_order = Sum('orderdetails__quantity')) \
                     .order_by("-total_order")[:3]

    meal = {
        "labels": [meal.name for meal in top3_meals],
        "data": [meal.total_order or 0 for meal in top3_meals]
    }

    # Top 3 Drivers
    top3_drivers = Driver.objects.annotate(
        total_order = Count(
            Case(
                When(order__restaurant = request.user.restaurant, then = 1)
            )
        )
    ).order_by("-total_order")[:3]

    driver = {
        "labels": [driver.user.get_full_name() for driver in top3_drivers],
        "data": [driver.total_order or 0 for driver in top3_drivers]
    }

    return JsonResponse({
        "revenue": revenue,
        "orders": orders,
        "meal": meal,
        "driver": driver,
    })
