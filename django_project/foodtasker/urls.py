"""foodtasker URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_view
from django.conf.urls.static import static
from django.conf import settings

from foodtaskerapp import views, apis, restaurant_apis, customer_apis, drivers_apis
from .api import router

urlpatterns = [
    path('app', apis.app),
    path('admin/', admin.site.urls),
    #Restaurant REST
    path('api/auth/', include('djoser.urls.authtoken')),
    path('api/users/', include('djoser.urls.base')),
    # path('api/v1/', include(router.urls)),
    path('api/v1/check_roles', apis.check_role),
    path('api/v1/restaurants/orders', restaurant_apis.OrderView.as_view()),
    path('api/v1/restaurants/meals', restaurant_apis.MealView.as_view()),
    path('api/v1/restaurants/me/', restaurant_apis.MeView.as_view()),
    path('api/v1/restaurant/register/', restaurant_apis.RegisterRestaurant.as_view()),
    path('api/v1/restaurants/report/<int:id>', restaurant_apis.restaurant_report),
    path('', views.restaurant_home, name='restaurant-home'),
    path('api/v1/restaurants/food-types/', restaurant_apis.FoodTypeView.as_view()),

                  #Customer REST
    path('api/v1/customers/register/', customer_apis.RegisterCustomer.as_view()),
    path('api/v1/customers/me/', customer_apis.MeView.as_view()),
    path('api/v1/customers/order/', customer_apis.customer_add_order),
    path('api/v1/customers/orders/', customer_apis.OrderView.as_view()),
    path('api/v1/customers/orders/last/', customer_apis.LastOrdersView.as_view()),

    #Driver REST
    path('api/v1/drivers/register/', drivers_apis.RegisterDriver.as_view()),
    path('api/v1/drivers/orders/', drivers_apis.OrderView.as_view()),
    path('api/v1/drivers/complete/', drivers_apis.driver_complete_order),
    path('api/v1/drivers/revenue/', drivers_apis.driver_get_revenue),
    path('api/v1/drivers/me/', drivers_apis.MeView.as_view()),


                  # Restaurant
    path(
        'restaurant/sign-in/',
        auth_view.LoginView.as_view(
            template_name='restaurant/sign_in.html'),
        name='restaurant-sign-in'),
    path(
        'restaurant/sign-out/',
        auth_view.LogoutView.as_view(
            next_page='/'),
        name='restaurant-sign-out'),
    path(
        'restaurant/',
        views.restaurant_home,
        name='restaurant-home'),
    path(
        'restaurant/sign-up/',
        views.restaurant_sign_up,
        name='restaurant-sign-up'),

    path(
        'restaurant/account',
        views.restaurant_account,
        name='restaurant-account'),
    path(
        'restaurant/meal',
        views.restaurant_meal,
        name='restaurant-meal'),
    path(
        'restaurant/meal/add/',
        views.restaurant_add_meal,
        name='restaurant-add-meal'),
    path(
        'restaurant/meal/edit/<int:meal_id>',
        views.restaurant_edit_meal,
        name='restaurant-edit-meal'),
    path(
        'restaurant/order',
        views.restaurant_order,
        name='restaurant-order'),
    path(
        'restaurant/report',
        views.restaurant_report,
        name='restaurant-report'),

    # Facebook - Sign In/Sign Up/Sign Out
    path('api/social/', include('rest_framework_social_oauth2.urls')),
    path(
        'oauth/',
        include(
            'social_django.urls',
            namespace='socialAuth')),
    # API for restaurant new order notification
    path('api/restaurant/order/notification/<str:last_viewed>/', restaurant_apis.restaurant_order_notification),

    # API restaurants
    path('api/restaurants/', restaurant_apis.restaurants_list),

    # APIs for CUSTOMERS
    path('api/customer/restaurants/', customer_apis.customer_get_restaurants),
    path(
        'api/customer/meals/<int:restaurant_id>',
        customer_apis.customer_get_meals),
    path('api/customer/order/add/', customer_apis.customer_add_order),
    path('api/customer/order/latest/',
         customer_apis.customer_get_latest_order),
    path('api/customer/driver/location/',
         customer_apis.customer_get_driver_location),

    # APIs for DRIVERS
    path('api/driver/orders/ready/', drivers_apis.driver_get_ready_orders),
    path('api/driver/order/pick/', drivers_apis.driver_pick_order),
    path('api/driver/order/latest/', drivers_apis.driver_get_latest_order),
    path('api/driver/order/complete/', drivers_apis.driver_complete_order),
    path('api/driver/revenue/', drivers_apis.driver_get_revenue),
    path('api/driver/location/update/', drivers_apis.driver_update_location),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
