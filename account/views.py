from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from .utils import *

# Create your views here.
@login_required
def index(request):
    return HttpResponseRedirect(reverse('review:index', args=()))

@never_cache
def login(request):
    index_path = reverse('account:index')
    if request.method == 'GET' and logged_in(request):
        return HttpResponseRedirect(index_path)
    from django.contrib.auth.views import login
    from django.contrib.auth.forms import AuthenticationForm
    context = {}
    if (REDIRECT_FIELD_NAME not in request.GET and
            REDIRECT_FIELD_NAME not in request.POST):
        context[REDIRECT_FIELD_NAME] = index_path
    defaults = {
            'extra_context': context,
            'authentication_form': AuthenticationForm,
            'template_name': 'account/login.html',
            }
    return login(request, **defaults)

@never_cache
def logout(request):
    from django.contrib.auth.views import logout
    defaults = {
        'template_name': 'account/logged_out.html',
    }
    return logout(request, **defaults)

