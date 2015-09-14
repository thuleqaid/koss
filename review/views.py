import json
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.forms.formsets import formset_factory
from django.utils import timezone
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
    form = {}
    # DataStructure for Form
    # {'checklist':checklist-info, 'groups':[ group-info, ... ], 'choice': [], 'bugstatus':[], 'buglevel':[]}
    # group-info: {'group': grpobj, 'items': [ item-info, ... ] }
    # item-info: {'title': title, 'choice': choice, 'bugs': [ bug-info, ... ] }
    # bug-info: {'question':question, 'answer':answer, 'status': status, 'level': bug-level }
    if request.method == 'POST':
        # 整理POST数据
        initvalue = json.loads(request.POST['initvalue'])
        for key in ('checklist', 'choice', 'bugstatus', 'buglevel'):
            form[key] = initvalue[key]
        form['groups'] = []
        flag_checkall = True
        for grp in initvalue['groups']:
            form['groups'].append({'group':grp['group'], 'items':[]})
            form['groups'][-1]['group']['valid'] = request.POST['group-valid-{}'.format(form['groups'][-1]['group']['id'])]
            if form['groups'][-1]['group']['valid'] == '0':
                groupvalid = False
            else:
                groupvalid = True
            for itm in grp['items']:
                form['groups'][-1]['items'].append(itm)
                form['groups'][-1]['items'][-1]['bugs'] = []
                # read value from POST
                choicekey = form['groups'][-1]['items'][-1]['name']+'-choice'
                bugkey1 = 'bug-'+form['groups'][-1]['items'][-1]['name']+'-status-{}'
                bugkey2 = 'bug-'+form['groups'][-1]['items'][-1]['name']+'-level-{}'
                bugkey3 = 'bug-'+form['groups'][-1]['items'][-1]['name']+'-question-{}'
                bugkey4 = 'bug-'+form['groups'][-1]['items'][-1]['name']+'-answer-{}'
                form['groups'][-1]['items'][-1]['choice'] = request.POST.get(choicekey, '')
                bugcount = int(request.POST.get('bug-count-'+form['groups'][-1]['items'][-1]['name'],'0'))
                auto_choice = ''
                valid_bug = 0
                for i in range(bugcount):
                    question = request.POST.get(bugkey3.format(i+1),'').strip()
                    if question:
                        # Question不为空时，记录指摘
                        form['groups'][-1]['items'][-1]['bugs'].append({})
                        form['groups'][-1]['items'][-1]['bugs'][-1]['status'] = request.POST.get(bugkey1.format(i+1),'')
                        form['groups'][-1]['items'][-1]['bugs'][-1]['level'] = request.POST.get(bugkey2.format(i+1),'')
                        form['groups'][-1]['items'][-1]['bugs'][-1]['question'] = question
                        form['groups'][-1]['items'][-1]['bugs'][-1]['answer'] = request.POST.get(bugkey4.format(i+1),'').strip()
                        valid_bug += 1
                        if form['groups'][-1]['items'][-1]['bugs'][-1]['status'].startswith('P'):
                            # 只要有一个处理中的指摘，检查项就为NG
                            auto_choice='NG'
                if valid_bug > 0:
                    if auto_choice == '':
                        # 所有指摘都处理完成是，检查项为OK
                        auto_choice = 'OK'
                    form['groups'][-1]['items'][-1]['choice'] = auto_choice
                if groupvalid and not form['groups'][-1]['items'][-1]['choice']:
                    flag_checkall = False
                    form['groups'][-1]['items'][-1]['error'] = 'Not Checked'
                if len(form['groups'][-1]['items'][-1]['bugs']) < 1:
                    # 至少保留一个指摘记入位置
                    form['groups'][-1]['items'][-1]['bugs'].append({'question':'', 'answer':'', 'status':form['bugstatus'][0][0], 'level':form['buglevel'][0][0]})
        if flag_checkall:
            # 全部检查项已经check过，保存数据
            title = '{}[{}]'.format(form['checklist']['title'],timezone.now())
            chklist = CheckListResult(title=title, listcode=form['checklist']['code'], listversion=form['checklist']['version'], groupcount=len(form['groups']))
            chklist.setCode('RLIST',CheckListResult.nextCode('RLIST'))
            chklist.save()
            for grp in form['groups']:
                buglist = []
                if form['groups'][-1]['group']['valid'] == '0':
                    grpobj = CheckGroupResult(checklist=chklist, groupcode=grp['code'], groupversion=grp['version'], status='IG')
                else:
                    count_ok, count_ng, count_ig = 0, 0, 0
                    for itm in grp['items']:
                        if itm['choice'] == 'IG':
                            count_ig += 1
                        elif itm['choice'] == 'OK':
                            count_ok += 1
                        elif itm['choice'] == 'NG':
                            count_ng += 1
                        else:
                            pass
                        for bug in itm['bugs']:
                            if bug['question']:
                                bugobj = CheckBugItem(question=bug['question'], answer=bug['answer'],status=bug['status'],level=bug['level'])
                                bugobj.itemcode = item['code']
                                bugobj.itemversion = item['version']
                                bugobj.setCode('BUG',CheckBugItem.nextCode('BUG'))
                                bugobj.save()
                                buglist.append(CheckGroupResult.Result(code=bugobj.code, version=bugobj.version, status=bugobj.status, level=bugobj.level))
                    if count_ng > 0:
                        group_status = 'NG'
                    else:
                        group_status = 'OK'
                    grpobj = CheckGroupResult(checklist=chklist, groupcode=grp['group']['code'], groupversion=grp['group']['version'], status=group_status)
                    grpobj.summary=json.dumps([('IG',count_ig),('OK',count_ok),('NG',count_ng)])
                    grpobj.buglist = json.dumps(buglist)
                grpobj.setCode('RGRP', CheckGroupResult.nextCode('RGRP'))
                grpobj.save()
            return HttpResponse("Save OK")
        else:
            return render(request, 'review/reportnew.html', {'form':form,'initvalue':request.POST['initvalue'],})
    else:
        # 初次进入，设置初期值
        chklist = list(CheckList.latest('WHERE code="%s"'%(checklistcode,)))
        if len(chklist) > 0:
            chk = chklist[0]
            form['checklist'] = {'code':chk.code,'version':chk.version, 'title':chk.title}
            choices_org = [CheckList.ChoiceItem(*x) for x in json.loads(chk.choices)]
            choices = [(x.value, x.text) for idx,x in enumerate(choices_org) if x.valid]
            bug1_org = [CheckList.BugStatus(*x) for x in json.loads(chk.bugstatus)]
            bug1 = [(x.value, x.text) for idx,x in enumerate(bug1_org) if x.valid]
            bug2_org = [CheckList.BugCategory(*x) for x in json.loads(chk.bugcategory)]
            bug2 = [(x.value, x.text) for idx,x in enumerate(bug2_org) if x.valid]
            form['choice']    = tuple(choices)
            form['bugstatus'] = tuple(bug1)
            form['buglevel']  = tuple(bug2)
            groups = [CheckList.GroupItem(*x) for x in json.loads(chk.groups)]
            grpobjs = CheckGroup.objects.filter(pk__in = [x.id for x in groups if x.valid]).order_by('code')
            form['groups'] = []
            for grp in grpobjs:
                form['groups'].append({'group':{'id':grp.id, 'code':grp.code, 'version':grp.version, 'title':grp.title, 'valid':'1'},'items':[]})
                items = [CheckGroup.GroupDetailItem(*x) for x in json.loads(grp.details)]
                for item in CheckItem.objects.filter(pk__in = [x.id for x in items if x.valid]).order_by('code'):
                    form['groups'][-1]['items'].append({'code':item.code, 'version':item.version, 'name':'item{}'.format(item.id),'title':item.title, 'choice':'', 'error':'', 'buginitcount':0, 'bugs':[]})
                    form['groups'][-1]['items'][-1]['bugs'].append({'question':'', 'answer':'', 'status':form['bugstatus'][0][0], 'level':form['buglevel'][0][0]})
            return render(request, 'review/reportnew.html', {'form':form,'initvalue':json.dumps(form),})
        else:
            raise Http404("CheckList does not exist")

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
