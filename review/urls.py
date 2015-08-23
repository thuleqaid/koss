from django.conf.urls import url
from . import views

urlpatterns = [
	url(r'^$', views.index, name='index'),
	url(r'^project/edit/(?P<projectid>\d+)$', views.projectedit, name='projectedit'),
	url(r'^project/(?P<projectid>\d+)$', views.projectview, name='projectview'),
	url(r'^import/checkitem$', views.importchkitm, name='importcheckitem'),
	url(r'^setup$', views.setup, name='setup'),
	]
