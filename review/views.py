from django.shortcuts import render
from django.http import HttpResponse
from .models import CheckItem
from django.utils import timezone

# Create your views here.
def index(request):
	ci = CheckItem(code='AZ0001', version=3, title='Check Item 1', author=request.user, update_time=timezone.now())
	ci.save()
	cis = CheckItem.latest()
	return HttpResponse("<br />".join([str(x) for x in cis]))

