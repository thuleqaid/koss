from django.shortcuts import render
from django.http import HttpResponse
from .models import CheckItem
from django.utils import timezone

# Create your views here.
def index(request):
	cis = CheckItem.latest()
	return HttpResponse("<br />".join([str(x) for x in cis]))

def setup(request):
	ci = CheckItem(code='AZ#0001', version=1, title='Check Item 11', author=request.user)
	ci.save()
	ci = CheckItem(code='AZ#0002', version=1, title='Check Item 21', author=request.user)
	ci.save()
	ci = CheckItem(code='AZ#0002', version=2, title='Check Item 22', author=request.user)
	ci.save()
	ci = CheckItem(code='AZ#0002', version=3, title='Check Item 23', author=request.user)
	ci.save()
	ci = CheckItem(code='AZ#0001', version=2, title='Check Item 12', author=request.user)
	ci.save()
	return index(request)
