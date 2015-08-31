from django.conf.urls import url
from . import views

urlpatterns = [
	url(r'^$', views.index, name='index'),
	url(r'^project/edit/(?P<projectcode>\S+)$', views.projectedit, name='projectedit'),
	url(r'^project/(?P<projectcode>\S+)$', views.projectview, name='projectview'),
	url(r'^report/new/(?P<checklistcode>\S+)$', views.reportnew, name='reportnew'),
	url(r'^import/checkitem$', views.importchkitm, name='importcheckitem'),
	url(r'^setup$', views.setup, name='setup'),
	]
