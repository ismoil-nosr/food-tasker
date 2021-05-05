from djoser.compat import get_user_email, get_user_email_field_name
from rest_framework import serializers

from foodtasker import settings
from .models import Restaurant, Meal, Customer, Driver, Order, OrderDetails, User, FoodType


class RestaurantSerializer(serializers.ModelSerializer):
    # logo = serializers.SerializerMethodField()
    #
    # def get_logo(self, restaurant):
    #     request = self.context.get('request')
    #     logo_url = restaurant.logo.url
    #
    #     return request.build_absolute_uri(logo_url)

    class Meta:
        model = Restaurant
        fields = ('id', 'name', 'phone', 'address', 'logo')


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (['id', 'first_name', "last_name", "email", "username"])


class FoodTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = FoodType
        fields = ('id', 'name')


class MealSerializer(serializers.ModelSerializer):
    # image = serializers.SerializerMethodField()
    #
    # def get_image(self, meal):
    #     request = self.context.get('request')
    #     image_url = meal.image.url
    #     return request.build_absolute_uri(image_url)
    #
    # def create(self, validated_data):
    #     return Meal.objects.create(**validated_data)

    class Meta:
        model = Meal
        fields = ('id', 'name', 'short_description', 'image', 'price', 'food_type')

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['food_type'] = FoodTypeSerializer(instance.food_type).data
        return response


class OrderCustomerSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source = "user.get_full_name")

    class Meta:
        model = Customer
        fields = ("id", "name", "avatar", "phone", "address")


class OrderRestaurantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = ("id", "name", "phone", "address")


class OrderDriverSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source = "user.get_full_name")

    class Meta:
        model = Driver
        fields = ("id", "name", "avatar", "phone", "address")


class OrderMealSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meal
        fields = ("id", "name", "price")


class OrderDetailsSerializer(serializers.ModelSerializer):
    meal = OrderMealSerializer()

    class Meta:
        model = OrderDetails
        fields = ("id", "meal", "quantity", "sub_total")


class OrderSerializer(serializers.ModelSerializer):
    customer = OrderCustomerSerializer()
    driver = OrderDriverSerializer()
    restaurant = OrderRestaurantSerializer()
    order_details = OrderDetailsSerializer(many = True)
    status = serializers.ReadOnlyField(source = "get_status_display")
    created_at = serializers.ReadOnlyField(read_only = True)

    class Meta:
        model = Order
        fields = ("id", "customer", "restaurant", "driver", "order_details", "total", "status", "address", "created_at")
