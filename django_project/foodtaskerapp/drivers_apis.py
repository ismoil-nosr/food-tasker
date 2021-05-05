import json
from collections import OrderedDict

from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from oauth2_provider.models import AccessToken
from rest_framework import permissions, status
from rest_framework.decorators import permission_classes
from rest_framework.views import APIView

from .models import Order, User, Driver
from .pagination import PaginationHandlerMixin
from .restaurant_apis import BasicPagination
from .serializers import OrderDriverSerializer, OrderSerializer, UserSerializer


###############
# DRIVERS
###############
class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = UserSerializer(User.objects.get(
            auth_token = request.user.auth_token), many = False, context = {"request": request}).data
        driver = OrderDriverSerializer(Driver.objects.get(
            id = request.user.driver.id), many = False, context = {"request": request}).data
        return JsonResponse({"user": user, "driver": driver})

    def post(self, request, *args, **kwargs):
        user_serializer = UserSerializer(request.user, data = request.data, partial = True)
        order_serializer = OrderDriverSerializer(request.user.driver, data = request.data, partial = True)
        if user_serializer.is_valid() & order_serializer.is_valid():
            user_serializer.save()
            order_serializer.save(user = request.user)
            return JsonResponse({"user": order_serializer.data, "order": order_serializer.data},
                                status = status.HTTP_201_CREATED)
        else:
            return JsonResponse({"error": {"order": order_serializer.errors, "user": user_serializer.errors}},
                                status = status.HTTP_400_BAD_REQUEST)


class RegisterDriver(APIView):
    permission_classes([permissions.AllowAny])

    def post(self, request, *args, **kwargs):
        driver_data = OrderedDict(
            [
                ('name', request.POST.get('name')),
                ('phone', request.POST.get('phone')),
                ('address', request.POST.get('address')),
                ('avatar', request.FILES.get('avatar')),
            ]
        )
        user_data = OrderedDict(
            [
                ('first_name', request.POST.get('first_name')),
                ('last_name', request.POST.get('last_name')),
            ]
        )
        user_serializer = UserSerializer(data = user_data, partial = True)
        driver_serializer = OrderDriverSerializer(data = driver_data)
        if driver_serializer.is_valid():
            user = user_serializer.update(instance = request.user, validated_data = user_data)
            driver = driver_serializer.save(user = request.user)
            return JsonResponse({"message": "Success"},
                                status = status.HTTP_201_CREATED)
        else:
            return JsonResponse({"error": {"driver": driver_serializer.errors}},
                                status = status.HTTP_400_BAD_REQUEST)


class OrderView(APIView, PaginationHandlerMixin):
    pagination_class = BasicPagination
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrderSerializer

    def post(self, request, *args, **kwargs):
        driver = request.user.driver
        body = json.loads(request.body)

        if Order.objects.filter(driver = driver).exclude(
                status = Order.ONTHEWAY and Order.DELIVERED).count() > 5:
            return JsonResponse({
                "error": "You can only pick 5 orders at max at a time"
            }, status = status.HTTP_400_BAD_REQUEST)
        try:
            order = Order.objects.get(
                id = body["order_id"],
                driver = None,
                status = Order.READY
            )
            order.driver = driver
            order.status = Order.ONTHEWAY
            order.picked_at = timezone.now()
            order.save()

            return JsonResponse({"status": "success", })

        except Order.DoesNotExist:

            return JsonResponse({
                "error": "This order has been picked up"
            }, status = status.HTTP_400_BAD_REQUEST)

        return JsonResponse({})

    def get(self, request, *args, **kwargs):
        request_status = request.GET.get('status', None)
        specific_driver = request.GET.get('is_driver', None)
        driver_id = request.GET.get('driver_id', None)

        if specific_driver:
            specific_driver = request.user.driver
        elif driver_id:
            specific_driver = driver_id

        if request_status is None:
            instance = Order.objects.filter(
                status = Order.READY,
                driver = specific_driver).order_by("-id")
            page = self.paginate_queryset(instance)
            if page is not None:
                serializer = self.get_paginated_response(
                    self.serializer_class(page, many = True, context = {"request": request}).data)
            else:
                serializer = self.serializer_class(instance, many = True)
            return JsonResponse({"orders": serializer.data})
        else:
            instance = Order.objects.filter(
                status = request_status,
                driver = specific_driver
            ).order_by("-id")
            page = self.paginate_queryset(instance)
            if page is not None:
                serializer = self.get_paginated_response(
                    self.serializer_class(page, many = True, context = {"request": request}).data)
            else:
                serializer = self.serializer_class(instance, many = True)
            return JsonResponse({"orders": serializer.data})


def driver_get_ready_orders(request):
    orders = OrderSerializer(
        Order.objects.filter(
            status = Order.READY,
            driver = None).order_by("-id"),
        many = True,
    ).data

    return JsonResponse({"orders": orders})


# POST
# params: access_token, order_id


@csrf_exempt
def driver_pick_order(request):
    access_token = AccessToken.objects.get(
        token = request.POST.get("access_token"),
        expires__gt = timezone.now()
    )

    driver = access_token.user.driver

    if Order.objects.filter(driver = driver).exclude(
            status = Order.ONTHEWAY and Order.DELIVERED):
        return JsonResponse({
            "status": "failed",
            "error": "You can only pick one order at a time"
        })
    try:
        order = Order.objects.get(
            id = request.POST.get("order_id"),
            driver = None,
            status = Order.READY
        )
        order.driver = driver
        order.status = Order.ONTHEWAY
        order.picked_at = timezone.now()
        order.save()

        return JsonResponse({"status": "success", })

    except Order.DoesNotExist:

        return JsonResponse({
            "status": "failed",
            "error": "This order has been picked up"
        })

    return JsonResponse({})


def driver_get_latest_order(request):
    access_token = AccessToken.objects.get(
        token = request.GET.get("access_token"),
        expires__gt = timezone.now()
    )

    driver = access_token.user.driver

    order = OrderSerializer(
        Order.objects.filter(
            driver = driver).order_by("picked_at").last()
    ).data

    return JsonResponse({"order": order})


@csrf_exempt
def driver_complete_order(request):
    driver = request.user.driver
    body = json.loads(request.body)

    order = Order.objects.get(
        id = body["order_id"],
        driver = driver)
    order.status = Order.DELIVERED
    order.save()

    return JsonResponse({"status": "success"})


# GET params: access_token


def driver_get_revenue(request):
    driver = request.user.driver

    from datetime import timedelta

    revenue = {}
    today = timezone.now()
    current_weekdays = (
        today +
        timedelta(
            days = i) for i in range(
        0 -
        today.weekday(),
        7 -
        today.weekday()))

    for day in current_weekdays:
        orders = Order.objects.filter(
            driver = driver,
            status = Order.DELIVERED,
            created_at__year = day.year,
            created_at__month = day.month,
            created_at__day = day.day,
        )

        revenue[day.strftime("%a")] = sum(
            order.total for order in orders)

    return JsonResponse({"revenue": revenue})


# POST - params: access_token, "lat,lng"


@csrf_exempt
def driver_update_location(request):
    if request.method == "POST":
        access_token = AccessToken.objects.get(
            token = request.POST.get("access_token"),
            expires__gt = timezone.now()
        )

        driver = access_token.user.driver

        # Set location string => database
        driver.location = request.POST.get("location")
        driver.save()

        return JsonResponse({"status": "success"})
