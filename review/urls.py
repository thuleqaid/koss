from django.conf.urls import url
from . import views

urlpatterns = [
	url(r'^$', views.index, name='index'),
	url(r'^import/user$', views.importusr, name='importuser'),
	url(r'^project/(?P<projectcode>\S+)/edit$', views.projectedit, name='projectedit'),
	url(r'^project/(?P<projectcode>\S+)/view$', views.projectview, name='projectview'),
	#url(r'^report/new/(?P<checklistcode>\S+)$', views.reportnew, name='reportnew'),
	url(r'^project/(?P<projectcode>\S+)/import/checkitem$', views.importchkitm, name='importcheckitem'),
	url(r'^project/(?P<projectcode>\S+)/manage/checkgroup$', views.managechkgrp, name='managecheckgroup'),
	url(r'^project/(?P<projectcode>\S+)/manage/checklist$', views.managechklst, name='managechecklist'),
	url(r'^project/(?P<projectcode>\S+)/manage/user$', views.manageusr, name='manageuser'),
	url(r'^project/(?P<projectcode>\S+)/add/checkgroup$', views.addchkgrp, name='addcheckgroup'),
	url(r'^project/(?P<projectcode>\S+)/add/checklist$', views.addchklst, name='addchecklist'),
	url(r'^project/(?P<projectcode>\S+)/add/subproject$', views.addsubprj, name='addsubproject'),
	url(r'^project/(?P<projectcode>\S+)/sub/(?P<subprojectcode>\S+)$', views.subproject, name='subproject'),
	url(r'^project/(?P<projectcode>\S+)/selfcheck/new/(?P<subprojectcode>\S+)/(?P<checklistcode>\S+)$', views.selfchecknew, name='newselfcheck'),
	url(r'^project/(?P<projectcode>\S+)/selfcheck/edit/(?P<reportid>\S+)$', views.selfcheckedit, name='editselfcheck'),
	url(r'^project/(?P<projectcode>\S+)/peercheck/new/(?P<subprojectcode>\S+)/(?P<checklistcode>\S+)$', views.peerchecknew, name='newpeercheck'),
	url(r'^project/(?P<projectcode>\S+)/peercheck/edit/(?P<reportid>\S+)$', views.peercheckedit, name='editpeercheck'),
	url(r'^setup$', views.setup, name='setup'),
	]
