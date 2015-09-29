from django.conf.urls import url
from . import views

urlpatterns = [
	url(r'^$', views.index, name='index'),
	url(r'^import/user$', views.importusr, name='importuser'),
	url(r'^dashbord/user/(?P<projectcode>\w+)$', views.dashusr, name='dashboarduser'),
	url(r'^project/(?P<projectcode>\w+)$', views.projectview, name='projectview'),
	url(r'^project/(?P<projectcode>\w+)/dashboard$', views.projectdash, name='projectdash'),
	url(r'^project/(?P<projectcode>\w+)/edit$', views.projectedit, name='projectedit'),
	url(r'^project/(?P<projectcode>\w+)/import/checkitem$', views.importchkitm, name='importcheckitem'),
	url(r'^project/(?P<projectcode>\w+)/manage/checkgroup$', views.managechkgrp, name='managecheckgroup'),
	url(r'^project/(?P<projectcode>\w+)/manage/checklist$', views.managechklst, name='managechecklist'),
	url(r'^project/(?P<projectcode>\w+)/manage/user$', views.manageusr, name='manageuser'),
	url(r'^project/(?P<projectcode>\w+)/add/checkgroup$', views.addchkgrp, name='addcheckgroup'),
	url(r'^project/(?P<projectcode>\w+)/add/checklist$', views.addchklst, name='addchecklist'),
	url(r'^project/(?P<projectcode>\w+)/add/subproject$', views.addsubprj, name='addsubproject'),
	url(r'^project/(?P<projectcode>\w+)/modify/checkitem/(?P<itemcode>\w+)$', views.modifychkitm, name='modifycheckitem'),
	url(r'^project/(?P<projectcode>\w+)/sub/(?P<subprojectcode>\w+)$', views.subproject, name='subproject'),
	url(r'^project/(?P<projectcode>\w+)/selfcheck/new/(?P<subprojectcode>\w+)/(?P<checklistcode>\w+)$', views.selfchecknew, name='newselfcheck'),
	url(r'^project/(?P<projectcode>\w+)/selfcheck/edit/(?P<reportid>\w+)$', views.selfcheckedit, name='editselfcheck'),
	url(r'^project/(?P<projectcode>\w+)/peercheck/new/(?P<subprojectcode>\w+)/(?P<checklistcode>\w+)$', views.peerchecknew, name='newpeercheck'),
	url(r'^project/(?P<projectcode>\w+)/peercheck/edit/(?P<reportid>\w+)$', views.peercheckedit, name='editpeercheck'),
	url(r'^project/(?P<projectcode>\w+)/lockcheck/(?P<reportcode>\w+)$', views.lockcheck, name='lockcheck'),
	url(r'^setup$', views.setup, name='setup'),
	]
