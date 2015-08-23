import json
import csv
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.utils import timezone
from .models import *
from .forms import *

# Create your views here.
def index(request):
    prjs = Project.latest()
    return render(request, 'review/index.html', {'projects':prjs,})

def importchkitm(request):
    if request.method == 'POST':
        if request.POST['excel_tab']:
            data=request.POST['excel_tab'].encode('utf-8').splitlines()
            cread = csv.reader(data, 'excel')
            for row in cread:
                print('\t'.join(row))
            return HttpResponse('ok')
    return render(request, 'review/importchkitm.html', {})

def projectedit(request, projectid):
    if request.method == 'POST':
        initial = json.loads(request.POST['initial'])
        form = ProjectForm(request.POST, initial=initial)
        if form.is_valid():
            if form.has_changed():
                code = form.cleaned_data['code']
                if code:
                    prjs = list(Project.objects.filter(code=code).filter(version__gte=form.cleaned_data['version']))
                    if len(prjs) > 1:
                        form.add_error('version', 'Someone has updated the project.')
                        return render(request, 'review/projectedit.html', {'projectid':projectid,'form':form,'initial':json.dumps(initial),})
                    else:
                        prj = Project(title=form.cleaned_data['title'], status=form.cleaned_data['status'],
                                      code=code, version=form.cleaned_data['version']+1)
                        prj.save()
                else:
                    codeno = Project.nextCode(Project.DefaultCategory)
                    prj = Project(title=form.cleaned_data['title'], status=form.cleaned_data['status'])
                    prj.setCode(Project.DefaultCategory, codeno)
                    prj.save()
            return HttpResponseRedirect(reverse('review:index', args=()))
    else:
        if int(projectid) > 0:
            prj = Project.objects.get(pk=projectid)
            initial = {'title':prj.title, 'status':prj.status, 'code':prj.code, 'version':prj.version}
        else:
            initial = {'title':'', 'status':Project.StatusChoice[0][0], 'code':'', 'version':0}
        form = ProjectForm(initial, initial=initial)
    return render(request, 'review/projectedit.html', {'projectid':projectid,'form':form,'initial':json.dumps(initial),})

def projectview(request, projectid):
    prj = get_object_or_404(Project, pk=projectid)
    grps = CheckGroup.latest('WHERE project="%s"' % (prj.code,))
    return render(request, 'review/project.html', {'project':prj, 'groups':grps,})

def setup(request):
    prj = Project(title='Project 1')
    prj.setCode(Project.DefaultCategory, Project.nextCode(Project.DefaultCategory))
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
