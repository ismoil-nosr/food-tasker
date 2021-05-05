from .models import Customer, Driver


def create_user_by_type(backend, strategy, user,
                        response, *args, **kwargs):
    request = strategy.request
    if backend.name == 'facebook':
        avatar = 'https://graph.facebook.com/%s/picture?type=large' % response['id']

    if request.POST.get('user_type') == "driver" and not Driver.objects.filter(
            user_id=user.id):
        Driver.objects.create(user_id=user.id, avatar=avatar)
    elif request.POST.get('user_type') == "customer" and not Customer.objects.filter(user_id=user.id):
        Customer.objects.create(user_id=user.id, avatar=avatar)
    else:
        pass
