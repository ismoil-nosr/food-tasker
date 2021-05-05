import json
from collections import OrderedDict

import stripe
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from oauth2_provider.models import AccessToken
from rest_framework import permissions, status
from rest_framework.decorators import permission_classes
from rest_framework.views import APIView

from foodtasker.settings import STRIPE_API_KEY
from .models import Customer, Meal, Order, OrderDetails, Restaurant, User
from .pagination import PaginationHandlerMixin
from .restaurant_apis import BasicPagination
from .serializers import MealSerializer, OrderCustomerSerializer, OrderSerializer, RestaurantSerializer, UserSerializer


###############
# CUSTOMERS
###############
class RegisterCustomer(APIView):
    permission_classes([permissions.AllowAny])

    def post(self, request, *args, **kwargs):
        cust_data = OrderedDict(
            [
                ('name', request.POST.get('name')),
                ('phone', request.POST.get('phone')),
                ('address', request.POST.get('address')),
                ('avatar', request.FILES['avatar']),
            ]
        )
        user_data = OrderedDict(
            [
                ('first_name', request.POST.get('first_name')),
                ('last_name', request.POST.get('last_name')),
            ]
        )
        user_serializer = UserSerializer(data = user_data, partial = True)
        customer_serializer = OrderCustomerSerializer(data = cust_data)
        if customer_serializer.is_valid():
            user = user_serializer.update(instance = request.user, validated_data = user_data)
            customer = customer_serializer.save(user = request.user)
            return JsonResponse({"message": "Success"},
                                status = status.HTTP_201_CREATED)
        else:
            return JsonResponse({"error": {"customer": customer_serializer.errors}},
                                status = status.HTTP_400_BAD_REQUEST)


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = UserSerializer(User.objects.get(
            auth_token = request.user.auth_token), many = False, context = {"request": request}).data
        customer = OrderCustomerSerializer(Customer.objects.get(
            id = request.user.customer.id), many = False, context = {"request": request}).data
        return JsonResponse({"user": user, "customer": customer})

    def post(self, request, *args, **kwargs):
        user_serializer = UserSerializer(request.user, data = request.data, partial = True)
        customer_serializer = OrderCustomerSerializer(request.user.customer, data = request.data, partial = True)
        if user_serializer.is_valid() & customer_serializer.is_valid():
            user_serializer.save()
            customer_serializer.save(user = request.user)
            return JsonResponse({"user": customer_serializer.data, "customer": customer_serializer.data},
                                status = status.HTTP_201_CREATED)
        else:
            return JsonResponse({"error": {"customer": customer_serializer.errors, "user": user_serializer.errors}},
                                status = status.HTTP_400_BAD_REQUEST)


def customer_get_restaurants(request):
    restaurant = RestaurantSerializer(
        Restaurant.objects.all().order_by("-id"),
        many = True,
        context = {"request": request},
    ).data

    return JsonResponse({"restaurants": restaurant}, )


def customer_get_meals(request, restaurant_id):
    meals = MealSerializer(
        Meal.objects.filter(
            restaurant_id = restaurant_id).order_by("-id"),
        many = True,
        context = {"request": request},
    ).data

    return JsonResponse({"meals": meals})


@csrf_exempt
def customer_add_order(request):
    """
    :param request:
        access_token
        restaurant_id
        address
        order_details (json format), example:
            [{"meal_id": 1, "quantity": 2},{"meal_id": 2, "quantity": 3}]
        stripe_token
    :return:
        {"status": "success"}
    """
    stripe.api_key = STRIPE_API_KEY

    if request.method == "POST":
        # Get token
        # access_token = AccessToken.objects.get(
        #     token = request.POST.get("access_token"),
        #     expires__gt = timezone.now()
        # )

        # Get profile
        customer = request.user.customer

        # Get stripe token
        post_data = json.loads(request.body)
        stripe_token = post_data["stripe_token"]
        # Check whether customer has any order that is not delivered
        if Order.objects.filter(customer = customer).exclude(
                status = Order.DELIVERED):
            return JsonResponse(
                {"error": "Your last order must be completed."}, status = status.HTTP_400_BAD_REQUEST)

        # Check Address
        if not post_data['address']:
            return JsonResponse(
                {"error": "Address is required."}, status = status.HTTP_400_BAD_REQUEST)

        # Get Order Details

        order_details = post_data['order_details']

        order_total = 0
        order_total_restaurant = {}
        for restaurant_id, meals in order_details.items():
            total = 0
            order_total_restaurant[restaurant_id] = 0
            for meal in meals:
                total += Meal.objects.get(
                    id = meal["meal_id"]).price * meal["quantity"]
                order_total += total
            order_total_restaurant[restaurant_id] = total

        if len(order_details) > 0:
            # Create a charge: this will charge customer's card
            charge = stripe.Charge.create(
                amount = order_total * 100,  # Amount in cents
                currency = "usd",
                source = stripe_token,
            )

            if charge.status != "failed":
                # Step 1 - Create an Order
                for restaurant_id, meals in order_details.items():
                    order = Order.objects.create(
                        customer = customer,
                        restaurant_id = restaurant_id,
                        total = order_total_restaurant[restaurant_id],
                        status = Order.COOKING,
                        address = post_data["address"]
                    )
                    # Step 2 - Create Order Details
                    for meal in meals:
                        print(type(meal))
                        OrderDetails.objects.create(
                            order = order,
                            meal_id = meal["meal_id"],
                            quantity = meal["quantity"],
                            sub_total = Meal.objects.get(
                                id = meal["meal_id"]).price * meal["quantity"],
                        )

                return JsonResponse({"status": "success"})

            else:
                return JsonResponse({"error": "Fail connect to Stripe."}, status = status.HTTP_400_BAD_REQUEST)


def customer_get_latest_order(request):
    customer = request.user.customer
    order = OrderSerializer(

        Order.objects.filter(
            customer = customer).last()).data

    return JsonResponse({"order": order})


class OrderView(APIView, PaginationHandlerMixin):
    pagination_class = BasicPagination
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrderSerializer

    def get(self, request, *args, **kwargs):
        instance = Order.objects.filter(
            status = Order.DELIVERED,
            customer = request.user.customer).order_by("-id")
        page = self.paginate_queryset(instance)
        if page is not None:
            serializer = self.get_paginated_response(
                self.serializer_class(page, many = True, context = {"request": request}).data)
        else:
            serializer = self.serializer_class(instance, many = True)
        return JsonResponse({"orders": serializer.data})

class LastOrdersView(APIView, PaginationHandlerMixin):
    pagination_class = BasicPagination
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrderSerializer

    def get(self, request, *args, **kwargs):
        instance = Order.objects.filter(
            status__in = [Order.READY, Order.COOKING, Order.ONTHEWAY],
            customer = request.user.customer).order_by("-id")
        page = self.paginate_queryset(instance)
        if page is not None:
            serializer = self.get_paginated_response(
                self.serializer_class(page, many = True, context = {"request": request}).data)
        else:
            serializer = self.serializer_class(instance, many = True)
        return JsonResponse({"orders": serializer.data})

# GET - params: access_token


def customer_get_driver_location(request):
    access_token = AccessToken.objects.get(
        token = request.GET.get("access_token"),
        expires__gt = timezone.now()
    )

    customer = access_token.user.customer

    # Get driver's location related to this customers current order
    current_order = Order.objects.filter(
        customer = customer,
        status = Order.ONTHEWAY
    ).last()
    location = current_order.driver.location

    return JsonResponse({"location": location})
