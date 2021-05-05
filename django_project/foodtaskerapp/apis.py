from django.http import JsonResponse
from rest_framework import status

from .models import Customer, Driver, Restaurant


###############
# APP
###############

def app(request):
    response = JsonResponse(
        {'app-settings': [{'test': request.META['HTTP_AUTHORIZATION']}, request.META['HTTP_CUSTOM']]})
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET"
    response["Access-Control-Max-Age"] = "1000"
    response["Access-Control-Allow-Headers"] = "X-Requested-With, Content-Type"
    return response


def check_role(request):
    print(request.user)
    driver = Driver.objects.filter(user_id = request.user.id).exists()
    res = []
    if driver:
        res.append('Driver')

    customer = Customer.objects.filter(user_id = request.user.id).exists()
    if customer:
        res.append('Customer')

    restaurant = Restaurant.objects.filter(user_id = request.user.id).exists()
    if restaurant:
        res.append('Restaurant')

    if len(res) != 0:
        return JsonResponse({"roles": res})
    else:
        return JsonResponse({"message": "The user does not have any role specified"},
                            status = status.HTTP_400_BAD_REQUEST)
