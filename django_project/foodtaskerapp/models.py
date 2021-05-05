from django.db import models
from django.contrib.auth.models import User


# from django.contrib.auth.models import AbstractUser
# class LocalUser(AbstractUser):
#   pass
# Create your models here.
from django.utils import timezone


class Restaurant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='restaurant')
    name = models.CharField(verbose_name='Restaurant Name', max_length=500)
    phone = models.CharField(max_length=500, null=True, blank=True)
    address = models.CharField(verbose_name='Restaurant Address', max_length=500)
    logo = models.ImageField(verbose_name='Restaurant Logo', upload_to='restaurant_logo/', blank=False)

    def __str__(self):
        return self.name

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer')
    avatar = models.ImageField(verbose_name='Customer Avatar', upload_to='customer_avatar/', blank=True)
    phone = models.CharField(max_length=500, blank=True)
    address = models.CharField(max_length=500, blank=True)

    def __str__(self):
        return self.user.get_full_name()

class Driver(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='driver')
    avatar = models.ImageField(verbose_name='Driver Avatar', upload_to='driver_avatar/', blank=True)
    phone = models.CharField(max_length=500, blank=True)
    address = models.CharField(max_length=500, blank=True)
    location = models.CharField(max_length=500, blank=True)

    def __str__(self):
        return self.user.get_full_name()


class FoodType(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    name = models.CharField(max_length = 50)

    def __str__(self):
        return str(self.name)
#
#
# class Categories(models.Model):
#     # type = models.ForeignKey(FoodType, related_name = 'food_type', on_delete = models.CASCADE)
#     name = models.CharField(max_length = 50)
#
#     def __str__(self):
#         return str(self.name)


class Meal(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    food_type = models.ForeignKey(FoodType, on_delete = models.CASCADE, default = 5, related_name = 'food_type')
    name = models.CharField(max_length=500)
    short_description = models.CharField(max_length=500)
    image = models.ImageField(upload_to='meal/images/', blank=False)
    price = models.IntegerField(default=0)

    def __str__(self):
        return self.name

class Order(models.Model):
    COOKING = 1
    READY = 2
    ONTHEWAY = 3
    DELIVERED = 4

    STATUS_CHOICES = (
        (COOKING, "Cooking"),
        (READY, "Ready"),
        (ONTHEWAY, "On the way"),
        (DELIVERED, "Delivered"),
    )

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    driver = models.ForeignKey(Driver, blank = True, null = True, on_delete=models.CASCADE)
    address = models.CharField(max_length=500)
    total = models.IntegerField()
    status = models.IntegerField(choices=STATUS_CHOICES)
    created_at = models.DateTimeField(default=timezone.now)
    picked_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return str(self.id)

class OrderDetails(models.Model):
    order = models.ForeignKey(Order, related_name='order_details', on_delete=models.CASCADE)
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    sub_total = models.IntegerField()

    def __str__(self):
        return str(self.id)


