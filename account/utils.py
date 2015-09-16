def logged_in(request):
    return request.user.is_active

def current_userid(request):
    return request.user.id
