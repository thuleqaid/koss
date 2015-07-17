from django.shortcuts import render
from django.http import HttpResponse
from .models import CheckItem

# Create your views here.
def index(request):
	ci = CheckItem(title='Check Item 1')
	ci.history_save()
	return HttpResponse('Hello' + str(ci))
