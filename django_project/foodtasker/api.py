from rest_framework import routers
from foodtaskerapp import restaurant_apis

router = routers.DefaultRouter()
router.register(r'restaurants', restaurant_apis.RestaurantViewSet)
router.register(r'meals', restaurant_apis.RestaurantViewSet)
router.register(r'orders', restaurant_apis.RestaurantViewSet)
router.register(r'customers', restaurant_apis.RestaurantViewSet)
router.register(r'drivers', restaurant_apis.RestaurantViewSet)
router.register(r'app', restaurant_apis.AppViewSet)
