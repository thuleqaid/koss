import json
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.forms.formsets import formset_factory
from .models import *
from .forms import *
from .utils import *

# Create your views here.
def index(request):
    prjs = Project.latest()
    return render(request, 'review/index.html', {'projects':prjs,})

def importchkitm(request):
    if request.method == 'POST':
        if request.POST['excel_tab']:
            data=request.POST['excel_tab'].splitlines()
            cread = CSVReader(data)
            return render(request, 'review/previewchkitm.html', {'data':cread,})
    return render(request, 'review/importchkitm.html', {})

def projectedit(request, projectcode):
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
                        return render(request, 'review/projectedit.html', {'projectcode':projectcode,'form':form,'initial':json.dumps(initial),})
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
        prjlist = list(Project.latest('WHERE code="%s"'%(projectcode,)))
        if len(prjlist) > 0:
            prj = prjlist[0]
            initial = {'title':prj.title, 'status':prj.status, 'code':prj.code, 'version':prj.version}
        else:
            initial = {'title':'', 'status':Project.StatusChoice[0][0], 'code':'', 'version':0}
        form = ProjectForm(initial, initial=initial)
    return render(request, 'review/projectedit.html', {'projectcode':projectcode,'form':form,'initial':json.dumps(initial),})

def projectview(request, projectcode):
    prjlist = list(Project.latest('WHERE code="%s"'%(projectcode,)))
    if len(prjlist) > 0:
        prj = prjlist[0]
        grps = CheckGroup.latest('WHERE project="%s"' % (prj.code,))
        chks = CheckList.latest('WHERE project="%s"' % (prj.code,))
        return render(request, 'review/project.html', {'project':prj, 'groups':grps, 'checks':chks})
    else:
        raise Http404("Project does not exist")

def reportnew(request, checklistcode):
    chklist = list(CheckList.latest('WHERE code="%s"'%(checklistcode,)))
    if len(chklist) > 0:
        chk = chklist[0]
        formname,nestformname = dynamicForm(chk)
        form = []
        groups = [CheckList.GroupItem(*x) for x in json.loads(chk.groups)]
        grpobjs = CheckGroup.objects.filter(pk__in = [x.id for x in groups if x.valid]).order_by('code')
        for grp in grpobjs:
            form.append({'group':grp,'item':[]})
            items = [CheckGroup.GroupDetailItem(*x) for x in json.loads(grp.details)]
            for item in CheckItem.objects.filter(pk__in = [x.id for x in items if x.valid]).order_by('code'):
                form[-1]['item'].append([globals()[formname](initial={'title':item.title}, prefix='item%d'%(item.id,))])
                form[-1]['item'][-1].append(globals()[nestformname](prefix='itembug%d'%(item.id,)))
        return render(request, 'review/reportnew.html', {'checklist':chk,'form':form,})
    else:
        raise Http404("CheckList does not exist")

def dynamicForm(chklist):
    dynname = 'CheckItemForm%d'%(chklist.id,)
    bugform = 'CheckItemBugForm%d'%(chklist.id,)
    if dynname not in globals():
        userdata_org = [CheckList.InputConfig(*x) for x in json.loads(chklist.userdata)]
        userdata = [x for x in sorted(userdata_org, key=lambda t:t.order) if x.valid]
        if len(userdata) > 0:
            checkitembugform = []
            checkitembugform.append('class %s(forms.Form):'%(bugform,))
            bug1_org = [CheckList.BugStatus(*x) for x in json.loads(chklist.bugstatus)]
            bug1 = [(idx, x.text) for idx,x in enumerate(sorted(bug1_org, key=lambda t:t.order)) if x.valid]
            if len(bug1) > 0:
                checkitembugform.append('    status = forms.ChoiceField(choices=%s, widget=forms.Select(attrs={\'class\':\'form-control\'}))'%(str(bug1),))
            bug2_org = [CheckList.BugCategory(*x) for x in json.loads(chklist.bugcategory)]
            bug2 = [(idx, x.text) for idx,x in enumerate(sorted(bug2_org, key=lambda t:t.order)) if x.valid]
            if len(bug2) > 0:
                checkitembugform.append('    category = forms.ChoiceField(choices=%s, widget=forms.Select(attrs={\'class\':\'form-control\'}))'%(str(bug2),))
            for useritm in userdata:
                if useritm.type=='TextArea':
                    checkitembugform.append('    %s = forms.CharField(label="%s", widget=forms.Textarea(attrs={\'class\':\'form-control\',\'rows\':\'2\',}))'%(useritm.label,useritm.labeltext))
            exec(compile('\n'.join(checkitembugform), '<string>', 'exec'),globals())
            exec(compile('%sSet = formset_factory(%s, extra=2)'%(bugform,bugform),'<string>','exec'),globals())
        choices_org = [CheckList.ChoiceItem(*x) for x in json.loads(chklist.choices)]
        choices = [(idx, x.text) for idx,x in enumerate(choices_org) if x.valid]
        checkitemform = []
        checkitemform.append('class %s(forms.Form):'%(dynname,))
        checkitemform.append('    title = forms.CharField(max_length=240, widget=forms.TextInput(attrs={\'class\':\'form-control\',\'readonly\':\'readonly\'}))')
        checkitemform.append('    choice = forms.ChoiceField(choices=%s, widget=forms.RadioSelect())'%(str(choices),))
        exec(compile('\n'.join(checkitemform), '<string>', 'exec'),globals())
    return dynname,bugform+"Set"

def setup(request):
    CheckList.objects.all().delete()
    CheckGroup.objects.all().delete()
    CheckItem.objects.all().delete()
    Project.objects.all().delete()
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
    details.append(CheckGroup.GroupDetailItem(True,ci.code,ci.version,ci.id))
    ci = CheckItem(version=1, title='Check Item 21')
    ci.setCode(itemcode,itemno+1)
    ci.save()
    details.append(CheckGroup.GroupDetailItem(True,ci.code,ci.version,ci.id))
    ci = CheckItem(version=2, title='Check Item 22')
    ci.setCode(itemcode,itemno+1)
    ci.save()
    details.append(CheckGroup.GroupDetailItem(True,ci.code,ci.version,ci.id))
    ci = CheckItem(version=3, title='Check Item 23')
    ci.setCode(itemcode,itemno+1)
    ci.save()
    details.append(CheckGroup.GroupDetailItem(True,ci.code,ci.version,ci.id))
    ci = CheckItem(version=2, title='Check Item 12')
    ci.setCode(itemcode,itemno)
    ci.save()
    details.append(CheckGroup.GroupDetailItem(True,ci.code,ci.version,ci.id))
    grp.details=CheckGroup.packDetails(details)
    grp.save()
    chklist = CheckList(project=prj.code, title='Checklist 1')
    chkgrps = []
    chkgrps.append(CheckList.GroupItem(True, grp.code, grp.version, grp.id))
    chklist.groups = json.dumps(chkgrps)
    chklist.setCode('Chk',1)
    chklist.save()
    return HttpResponseRedirect(reverse('review:index', args=()))
