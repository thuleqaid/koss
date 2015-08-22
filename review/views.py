from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.utils import timezone
from .models import *

# Create your views here.
def index(request):
    cis = CheckItem.latest()
    return HttpResponse("<br />".join([str(x) for x in cis]))

def setup(request):
    prj = Project(title='Project 1')
    prj.setCode('Prj',123)
    prj.version=1
    prj.save()
    grp = CheckGroup(project=prj.code, title='CheckGroup1')
    grp.setCode('Grp',1)
    grp.version=1
    details=[]
    itemcode='SS'
    itemno=1
    ci = CheckItem(version=1, title='Check Item 11')
    ci.setCode(itemcode,itemno)
    ci.save()
    details.append(CheckGroup.GroupDetailItem(True,ci.code,ci.version))
    ci = CheckItem(version=1, title='Check Item 21')
    ci.setCode(itemcode,itemno+1)
    ci.save()
    details.append(CheckGroup.GroupDetailItem(True,ci.code,ci.version))
    ci = CheckItem(version=2, title='Check Item 22')
    ci.setCode(itemcode,itemno+1)
    ci.save()
    details.append(CheckGroup.GroupDetailItem(True,ci.code,ci.version))
    ci = CheckItem(version=3, title='Check Item 23')
    ci.setCode(itemcode,itemno+1)
    ci.save()
    details.append(CheckGroup.GroupDetailItem(True,ci.code,ci.version))
    ci = CheckItem(version=2, title='Check Item 12')
    ci.setCode(itemcode,itemno)
    ci.save()
    details.append(CheckGroup.GroupDetailItem(True,ci.code,ci.version))
    grp.details=CheckGroup.packDetails(details)
    grp.save()
    return HttpResponseRedirect(reverse('review:index', args=()))
