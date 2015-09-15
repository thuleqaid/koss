from django.conf.urls import url
from . import views

urlpatterns = [
	url(r'^$', views.index, name='index'),
	url(r'^project/edit/(?P<projectcode>\S+)$', views.projectedit, name='projectedit'),
	url(r'^project/(?P<projectcode>\S+)$', views.projectview, name='projectview'),
	url(r'^report/new/(?P<checklistcode>\S+)$', views.reportnew, name='reportnew'),
	url(r'^import/checkitem/(?P<projectcode>\S+)$', views.importchkitm, name='importcheckitem'),
	url(r'^manage/checkgroup/(?P<projectcode>\S+)$', views.managechkgrp, name='managecheckgroup'),
	url(r'^manage/checklist/(?P<projectcode>\S+)$', views.managechklst, name='managechecklist'),
	url(r'^add/checkgroup$', views.addchkgrp, name='addcheckgroup'),
	url(r'^add/checklist$', views.addchklst, name='addchecklist'),
	url(r'^add/subproject/(?P<projectcode>\S+)$', views.addsubprj, name='addsubproject'),
	url(r'^setup$', views.setup, name='setup'),
	url(r'^subproject/(?P<subprojectcode>\S+)$', views.subproject, name='subproject'),
	url(r'^selfcheck/new/(?P<subprojectcode>\S+)/(?P<checklistcode>\S+)$', views.selfchecknew, name='newselfcheck'),
	url(r'^selfcheck/edit/(?P<reportid>\S+)$', views.selfcheckedit, name='editselfcheck'),
	url(r'^peercheck/new/(?P<subprojectcode>\S+)/(?P<checklistcode>\S+)$', views.peerchecknew, name='newpeercheck'),
	url(r'^peercheck/edit/(?P<reportid>\S+)$', views.peercheckedit, name='editpeercheck'),
	]
