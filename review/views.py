# -*- coding:utf-8 -*-
import json
import copy
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
#from django.utils import timezone
from datetime import datetime as timezone
from .models import *
from .forms import *
from .utils import *

# Create your views here.
def index(request):
    prepareDB()
    prjs = Project.latest()
    permlevel = permissionCheck(request, 0)
    permdict = {'superuser':permlevel >= 9, 'systemuser':permlevel >= 2}
    return render(request, 'review/index.html', {'projects':prjs,'permission':permdict})

@login_required
def addchartgrp(request, projectcode):
    if request.method == 'POST':
        projectcode = request.POST['projectcode']
        grptitle    = request.POST['title'].strip()
        if grptitle:
            grpobj      = ChartGroup(project = projectcode, title = grptitle)
            grpobj.author = request.user
            grpobj.setCode('CHART', ChartGroup.nextCode('CHART'))
            grpobj.save()
        return HttpResponseRedirect(reverse('review:managechartgroup', args=(projectcode,)))

@login_required
def addchkgrp(request, projectcode):
    if request.method == 'POST':
        projectcode = request.POST['projectcode']
        grptitle    = request.POST['title'].strip()
        if grptitle:
            grpobj      = CheckGroup(project = projectcode, title = grptitle)
            grpobj.author = request.user
            grpobj.setCode('GRP', CheckGroup.nextCode('GRP'))
            grpobj.save()
        return HttpResponseRedirect(reverse('review:managecheckgroup', args=(projectcode,)))

@login_required
def addchklst(request, projectcode):
    if request.method == 'POST':
        projectcode = request.POST['projectcode']
        lsttitle    = request.POST['title'].strip()
        if lsttitle:
            if 'selfcheck' in request.POST:
                lsttype = True
            else:
                lsttype = False
            lstobj = CheckList(project = projectcode, title = lsttitle, selfcheck = lsttype)
            lstobj.author = request.user
            lstobj.setCode('LST', CheckList.nextCode('LST'))
            lstobj.save()
        return HttpResponseRedirect(reverse('review:managechecklist', args=(projectcode,)))

@login_required
def addselfcheck(request, projectcode, subprojectcode, checklistcode):
    form = {}
    # DataStructure for Form
    # {'checklist':checklist-info, 'groups':[ group-info, ... ], 'choice': [], 'bugstatus':[], 'buglevel':[]}
    # group-info: {'group': grpobj, 'items': [ item-info, ... ] }
    # item-info: {'title': title, 'choice': choice, 'bugs': [] }
    if request.method == 'POST':
        # 整理POST数据
        initvalue = json.loads(request.POST['initvalue'])
        for key in ('project', 'subproject', 'checklist', 'choice'):
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
                form['groups'][-1]['items'][-1]['choice'] = request.POST.get(choicekey, '')
                if groupvalid and not form['groups'][-1]['items'][-1]['choice']:
                    flag_checkall = False
                    form['groups'][-1]['items'][-1]['error'] = 'Not Checked'
        if flag_checkall:
            # 全部检查项已经check过，保存数据
            title = '{}[{}]'.format(form['checklist']['title'],timezone.now().strftime("%Y%m%d%H%M%S"))
            chklist = CheckListResult(subproject=form['subproject']['code'], title=title, listcode=form['checklist']['code'], listversion=form['checklist']['version'], groupcount=len(form['groups']))
            chklist.author = request.user
            groupids = []
            for grp in form['groups']:
                choiceresult = []
                if grp['group']['valid'] == '0':
                    grpobj = CheckGroupResult(groupid=grp['group']['id'],
                            groupcode=grp['group']['code'],
                            groupversion=grp['group']['version'],
                            grouptitle=grp['group']['title'],
                            status='IG')
                    for itm in grp['items']:
                        choiceresult.append(CheckGroupResult.Choice(code=itm['code'],
                            version=itm['version'],
                            id=itm['id'],
                            choice='IG'))
                    grpobj.summary=json.dumps({'IG':len(grp['items']),'OK':0,'NG':0,'BUGA':0,'BUGC':0,'BUGD':0})
                else:
                    count_ok, count_ng, count_ig = 0, 0, 0
                    for itm in grp['items']:
                        choiceresult.append(CheckGroupResult.Choice(code=itm['code'],
                            version=itm['version'],
                            id=itm['id'],
                            choice=itm['choice']))
                        if itm['choice'] == 'IG':
                            count_ig += 1
                        elif itm['choice'] == 'OK':
                            count_ok += 1
                        elif itm['choice'] == 'NG':
                            count_ng += 1
                        else:
                            pass
                    if count_ng > 0:
                        group_status = 'NG'
                    else:
                        group_status = 'OK'
                    grpobj = CheckGroupResult(groupid=grp['group']['id'],
                            groupcode=grp['group']['code'],
                            groupversion=grp['group']['version'],
                            grouptitle=grp['group']['title'],
                            status=group_status)
                    grpobj.summary=json.dumps({'IG':count_ig,'OK':count_ok,'NG':count_ng,'BUGA':0,'BUGC':0,'BUGD':0})
                grpobj.choices=json.dumps(choiceresult)
                grpobj.author = request.user
                grpobj.setCode('RGRP', CheckGroupResult.nextCode('RGRP'))
                grpobj.save()
                groupids.append(grpobj.id)
            chklist.groups = json.dumps(groupids)
            chklist.setCode('RLIST',CheckListResult.nextCode('RLIST'))
            chklist.save()
            return HttpResponseRedirect(reverse('review:subproject', args=(form['project']['code'],form['subproject']['code'],)))
        else:
            return render(request, 'review/newselfcheck.html', {'form':form,'initvalue':request.POST['initvalue'],'navbar':json.loads(request.POST['navbarinfo']), 'navbarinfo':request.POST['navbarinfo'],'permission':json.loads(request.POST['permissioninfo']),'permissioninfo':request.POST['permissioninfo']})
    else:
        # 初次进入，设置初期值
        chklist = list(CheckList.latest('WHERE code="%s"'%(checklistcode,)))
        if len(chklist) > 0:
            chk = chklist[0]
            form['project'] = {'code':projectcode}
            form['subproject'] = {'code':subprojectcode}
            form['checklist'] = {'code':chk.code,'version':chk.version, 'title':chk.title}
            prjobj = getProject(projectcode)
            prjsetting = getProjectSetting(prjobj, chk)
            choices_org = prjsetting['choice']
            choices = [(x.value, x.text) for idx,x in enumerate(choices_org) if x.valid]
            form['choice']    = tuple(choices)
            groups = [CheckList.GroupItem(*x) for x in json.loads(chk.groups)]
            grpobjs = CheckGroup.objects.filter(pk__in = [x.id for x in groups if x.valid]).order_by('code')
            form['groups'] = []
            for grp in grpobjs:
                form['groups'].append({'group':{'id':grp.id, 'code':grp.code, 'version':grp.version, 'title':grp.title, 'valid':'1'},'items':[]})
                items = [CheckGroup.GroupDetailItem(*x) for x in json.loads(grp.details)]
                for item in CheckItem.objects.filter(pk__in = [x.id for x in items if x.valid]).order_by('code'):
                    form['groups'][-1]['items'].append({'id':item.id, 'code':item.code, 'version':item.version, 'name':'item{}'.format(item.id),'title':item.title, 'details':item.details, 'choice':'', 'error':'', 'buginitcount':0, 'bugs':[]})
            subpobj = list(SubProject.latest('WHERE code="%s"'%(subprojectcode,)))
            navbar = []
            navbar.append({'link':reverse('review:projectview', args=(form['project']['code'],)), 'title':prjobj.title, 'param':['review:projectview', form['project']['code']]})
            navbar.append({'link':reverse('review:subproject', args=(form['project']['code'],form['subproject']['code'],)), 'title':subpobj[0].title, 'param':['review:subproject',form['project']['code'],form['subproject']['code']]})
            navbar.append({'link':'#', 'title':'New {}'.format(chk.title), 'param':['',]})
            permlevel = permissionCheck(request, 2, prjobj)
            permdict = {'save': (permlevel > 2) and (prjobj.status == 'OP') }
            return render(request, 'review/newselfcheck.html', {'form':form,'initvalue':json.dumps(form),'navbar':navbar, 'navbarinfo':json.dumps(navbar), 'permission':permdict, 'permissioninfo':json.dumps(permdict)})
        else:
            raise Http404("CheckList does not exist")

@login_required
def addsubprj(request, projectcode):
    if request.method == 'POST':
        if 'excel_tab' in request.POST:
            data=request.POST['excel_tab'].splitlines()
            cread = CSVReader(data)
            outlist = []
            for row in cread:
                outlist.append([x.strip() for idx, x in enumerate(row) if idx < 2])
            navbar = []
            prj = getProject(projectcode)
            navbar.append({'link':reverse('review:projectview', args=(projectcode,)), 'title':prj.title, 'param':['review:projectview', projectcode]})
            navbar.append({'link':reverse('review:addsubproject', args=(projectcode,)), 'title':'Add SubProject', 'param':['review:addsubproject', projectcode]})
            navbar.append({'link':'#', 'title':'Preview SubProject', 'param':['',]})
            return render(request, 'review/previewsubprj.html', {'projectcode':projectcode, 'data':outlist,'initial':json.dumps(outlist), 'navbar':navbar})
        elif 'initial' in request.POST:
            data = json.loads(request.POST['initial'])
            for row in data:
                if len(row) > 1:
                    subp = SubProject(project=projectcode, title=row[0], details=row[1])
                    subp.author = request.user
                    subp.setCode('SUBP',SubProject.nextCode('SUBP'))
                    subp.save()
            return HttpResponseRedirect(reverse('review:projectview', args=(projectcode,)))
    else:
        navbar = []
        prj = getProject(projectcode)
        permlevel = permissionCheck(request, 4, prj)
        navbar.append({'link':reverse('review:projectview', args=(projectcode,)), 'title':prj.title, 'param':['review:projectview', projectcode]})
        navbar.append({'link':'#', 'title':'Add SubProject', 'param':['',]})
        return render(request, 'review/addsubprj.html', {'projectcode':projectcode, 'navbar':navbar})

@login_required
def addpeercheck(request, projectcode, subprojectcode, checklistcode):
    form = {}
    # DataStructure for Form
    # {'checklist':checklist-info, 'groups':[ group-info, ... ], 'choice': [], 'bugstatus':[], 'buglevel':[]}
    # group-info: {'group': grpobj, 'items': [ item-info, ... ] }
    # item-info: {'title': title, 'choice': choice, 'bugs': [ bug-info, ... ] }
    # bug-info: {'question':question, 'answer':answer, 'status': status, 'level': bug-level }
    if request.method == 'POST':
        # 整理POST数据
        initvalue = json.loads(request.POST['initvalue'])
        for key in ('project', 'subproject', 'checklist', 'choice', 'bugstatus', 'buglevel'):
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
                        if not form['groups'][-1]['items'][-1]['bugs'][-1]['status'].startswith('D'):
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
            title = '{}[{}]'.format(form['checklist']['title'],timezone.now().strftime("%Y%m%d%H%M%S"))
            chklist = CheckListResult(subproject=form['subproject']['code'], title=title, listcode=form['checklist']['code'], listversion=form['checklist']['version'], groupcount=len(form['groups']))
            chklist.author = request.user
            groupids = []
            for grp in form['groups']:
                choiceresult = []
                buglist = []
                if grp['group']['valid'] == '0':
                    grpobj = CheckGroupResult(groupid=grp['group']['id'],
                            groupcode=grp['group']['code'],
                            groupversion=grp['group']['version'],
                            grouptitle=grp['group']['title'],
                            status='IG')
                    for itm in grp['items']:
                        choiceresult.append(CheckGroupResult.Choice(code=itm['code'],
                            version=itm['version'],
                            id=itm['id'],
                            choice='IG'))
                    grpobj.summary=json.dumps({'IG':len(grp['items']),'OK':0,'NG':0,'BUGA':0,'BUGC':0,'BUGD':0})
                else:
                    count_ok, count_ng, count_ig = 0, 0, 0
                    for itm in grp['items']:
                        choiceresult.append(CheckGroupResult.Choice(code=itm['code'],
                            version=itm['version'],
                            id=itm['id'],
                            choice=itm['choice']))
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
                                bugobj.author = request.user
                                bugobj.itemcode = itm['code']
                                bugobj.itemversion = itm['version']
                                bugobj.setCode('BUG',CheckBugItem.nextCode('BUG'))
                                bugobj.save()
                                buglist.append(CheckGroupResult.Result(code=bugobj.code, version=bugobj.version, status=bugobj.status, level=bugobj.level, id=bugobj.id))
                    if count_ng > 0:
                        group_status = 'NG'
                    else:
                        group_status = 'OK'
                    grpobj = CheckGroupResult(groupid=grp['group']['id'],
                            groupcode=grp['group']['code'],
                            groupversion=grp['group']['version'],
                            grouptitle=grp['group']['title'],
                            status=group_status)
                    bugcounta = len([x for x in buglist if x.status.startswith('A')])
                    bugcountw = len([x for x in buglist if x.status.startswith('C')])
                    bugcountf = len(buglist) - bugcounta - bugcountw
                    grpobj.summary=json.dumps({'IG':count_ig,'OK':count_ok,'NG':count_ng,'BUGA':bugcounta,'BUGC':bugcountw,'BUGD':bugcountf})
                grpobj.choices=json.dumps(choiceresult)
                grpobj.buglist=json.dumps(buglist)
                grpobj.author = request.user
                grpobj.setCode('RGRP', CheckGroupResult.nextCode('RGRP'))
                grpobj.save()
                groupids.append(grpobj.id)
            chklist.groups = json.dumps(groupids)
            chklist.setCode('RLIST',CheckListResult.nextCode('RLIST'))
            chklist.save()
            return HttpResponseRedirect(reverse('review:subproject', args=(form['project']['code'],form['subproject']['code'],)))
        else:
            return render(request, 'review/newpeercheck.html', {'form':form,'initvalue':request.POST['initvalue'],'navbar':json.loads(request.POST['navbarinfo']), 'navbarinfo':request.POST['navbarinfo'], 'permission':json.loads(request.POST['permissioninfo']), 'permissioninfo':request.POST['permissioninfo']})
    else:
        # 初次进入，设置初期值
        chklist = list(CheckList.latest('WHERE code="%s"'%(checklistcode,)))
        if len(chklist) > 0:
            chk = chklist[0]
            form['project'] = {'code':projectcode}
            form['subproject'] = {'code':subprojectcode}
            form['checklist'] = {'code':chk.code,'version':chk.version, 'title':chk.title}
            prjobj = getProject(projectcode)
            permlevel = permissionCheck(request, 2, prjobj)
            permdict = {'save': (permlevel > 2) and (prjobj.status == 'OP') }
            prjsetting = getProjectSetting(prjobj, chk)
            choices_org = prjsetting['choice']
            choices = [(x.value, x.text) for idx,x in enumerate(choices_org) if x.valid]
            bug1_org = prjsetting['bugstatus']
            bug1 = [(x.value, x.text) for idx,x in enumerate(bug1_org) if x.valid]
            bug2_org = prjsetting['buglevel']
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
                    form['groups'][-1]['items'].append({'id':item.id, 'code':item.code, 'version':item.version, 'name':'item{}'.format(item.id),'title':item.title, 'details':item.details, 'choice':'', 'error':'', 'buginitcount':0, 'bugs':[]})
                    form['groups'][-1]['items'][-1]['bugs'].append({'question':'', 'answer':'', 'status':form['bugstatus'][0][0], 'level':form['buglevel'][0][0]})
            subpobj = list(SubProject.latest('WHERE code="%s"'%(subprojectcode,)))
            navbar = []
            navbar.append({'link':reverse('review:projectview', args=(form['project']['code'],)), 'title':prjobj.title, 'param':['review:projectview',form['project']['code']]})
            navbar.append({'link':reverse('review:subproject', args=(form['project']['code'],form['subproject']['code'],)), 'title':subpobj[0].title, 'param':['review:subproject',form['project']['code'],form['subproject']['code']]})
            navbar.append({'link':'#', 'title':'New {}'.format(chk.title), 'param':['',]})
            return render(request, 'review/newpeercheck.html', {'form':form,'initvalue':json.dumps(form),'navbar':navbar,'navbarinfo':json.dumps(navbar),'permission':permdict,'permissioninfo':json.dumps(permdict)})
        else:
            raise Http404("CheckList does not exist")

@login_required
def editpeercheck(request, projectcode, reportid):
    form = {}
    # DataStructure for Form
    # {'checklist':checklist-info, 'groups':[ group-info, ... ], 'choice': [], 'bugstatus':[], 'buglevel':[]}
    # group-info: {'group': grpobj, 'items': [ item-info, ... ] }
    # item-info: {'title': title, 'choice': choice, 'bugs': [ bug-info, ... ] }
    # bug-info: {'question':question, 'answer':answer, 'status': status, 'level': bug-level }
    if request.method == 'POST':
        # 整理POST数据
        initvalue = json.loads(request.POST['initvalue'])
        for key in ('report', 'project', 'subproject', 'checklist', 'choice', 'bugstatus', 'buglevel'):
            form[key] = initvalue[key]
        form['groups'] = []
        flag_changed = False
        for grp in initvalue['groups']:
            form['groups'].append({'group':grp['group'], 'items':[]})
            if grp['group']['valid'] != '1':
                # 允许组无效变成有效，不允许有效变成无效
                form['groups'][-1]['group']['valid'] = request.POST['group-valid-{}'.format(form['groups'][-1]['group']['id'])]
            if form['groups'][-1]['group']['valid'] == '0':
                groupvalid = False
            else:
                groupvalid = True
            form['groups'][-1]['group']['changed'] = False
            if form['groups'][-1]['group']['valid'] != grp['group']['valid']:
                flag_changed = True
                form['groups'][-1]['group']['changed'] = True
            for itm in grp['items']:
                form['groups'][-1]['items'].append(copy.deepcopy(itm))
                #form['groups'][-1]['items'][-1]['bugs'] = []
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
                        if valid_bug < form['groups'][-1]['items'][-1]['buginitcount']:
                            form['groups'][-1]['items'][-1]['bugs'][valid_bug]['status'] = request.POST.get(bugkey1.format(i+1),'')
                            form['groups'][-1]['items'][-1]['bugs'][valid_bug]['level'] = request.POST.get(bugkey2.format(i+1),'')
                            form['groups'][-1]['items'][-1]['bugs'][valid_bug]['question'] = question
                            form['groups'][-1]['items'][-1]['bugs'][valid_bug]['answer'] = request.POST.get(bugkey4.format(i+1),'').strip()
                            if form['groups'][-1]['items'][-1]['bugs'][valid_bug]['status'].startswith('D') and form['report']['actor']:
                                # SubProject的担当者（SelfCheck的作者）不能关闭指摘
                                form['groups'][-1]['items'][-1]['bugs'][valid_bug]['status'] = itm['bugs'][valid_bug]['status']
                            if (form['groups'][-1]['items'][-1]['bugs'][valid_bug]['status'] != itm['bugs'][valid_bug]['status']) or (form['groups'][-1]['items'][-1]['bugs'][valid_bug]['level'] != itm['bugs'][valid_bug]['level']) or (form['groups'][-1]['items'][-1]['bugs'][valid_bug]['answer'] != itm['bugs'][valid_bug]['answer']):
                                form['groups'][-1]['group']['changed'] = True
                                form['groups'][-1]['items'][-1]['bugs'][valid_bug]['changed'] = True
                                flag_changed = True
                            else:
                                form['groups'][-1]['items'][-1]['bugs'][valid_bug]['changed'] = False
                            if not form['groups'][-1]['items'][-1]['bugs'][valid_bug]['status'].startswith('D'):
                                # 只要有一个处理中的指摘，检查项就为NG
                                auto_choice='NG'
                        else:
                            form['groups'][-1]['items'][-1]['bugs'].append({})
                            form['groups'][-1]['items'][-1]['bugs'][-1]['status'] = request.POST.get(bugkey1.format(i+1),'')
                            form['groups'][-1]['items'][-1]['bugs'][-1]['level'] = request.POST.get(bugkey2.format(i+1),'')
                            form['groups'][-1]['items'][-1]['bugs'][-1]['question'] = question
                            form['groups'][-1]['items'][-1]['bugs'][-1]['answer'] = request.POST.get(bugkey4.format(i+1),'').strip()
                            form['groups'][-1]['group']['changed'] = True
                            form['groups'][-1]['items'][-1]['bugs'][-1]['changed'] = True
                            flag_changed = True
                            if not form['groups'][-1]['items'][-1]['bugs'][-1]['status'].startswith('D'):
                                # 只要有一个处理中的指摘，检查项就为NG
                                auto_choice='NG'
                        valid_bug += 1
                if valid_bug > 0:
                    if auto_choice == '':
                        # 所有指摘都处理完成是，检查项为OK
                        auto_choice = 'OK'
                    form['groups'][-1]['items'][-1]['choice'] = auto_choice
                if groupvalid and form['groups'][-1]['items'][-1]['choice'] != itm['choice']:
                    flag_changed = True
                    form['groups'][-1]['group']['changed'] = True
        if flag_changed:
            # 保存数据
            chklist = CheckListResult.objects.get(pk=reportid)
            chklist.author = request.user
            chklist.version += 1
            chklist.id = None
            groupids = []
            for grp in form['groups']:
                if not grp['group']['changed']:
                    groupids.append(int(grp['group']['reportid']))
                else:
                    grpobj = CheckGroupResult.objects.get(pk = grp['group']['reportid'])
                    grpobj.author = request.user
                    grpobj.id = None
                    grpobj.version += 1
                    choiceresult = []
                    buglist = []
                    if grp['group']['valid'] == '0':
                        grpobj.status = 'IG'
                        for itm in grp['items']:
                            choiceresult.append(CheckGroupResult.Choice(code=itm['code'],
                                version=itm['version'],
                                id=itm['id'],
                                choice='IG'))
                        grpobj.summary=json.dumps({'IG':len(grp['items']),'OK':0,'NG':0,'BUGA':0,'BUGC':0,'BUGD':0})
                    else:
                        count_ok, count_ng, count_ig = 0, 0, 0
                        for itm in grp['items']:
                            choiceresult.append(CheckGroupResult.Choice(code=itm['code'],
                                version=itm['version'],
                                id=itm['id'],
                                choice=itm['choice']))
                            if itm['choice'] == 'IG':
                                count_ig += 1
                            elif itm['choice'] == 'OK':
                                count_ok += 1
                            elif itm['choice'] == 'NG':
                                count_ng += 1
                            else:
                                pass
                            for bug in itm['bugs']:
                                if not bug['changed']:
                                    buglist.append(CheckGroupResult.Result(code=bug['code'], version=bug['version'], status=bug['status'], level=bug['level'], id=bug['id']))
                                else:
                                    if 'code' in bug:
                                        # 既存指摘
                                        bugobj = CheckBugItem.objects.get(pk=bug['id'])
                                        bugobj.author = request.user
                                        bugobj.id = None
                                        bugobj.version += 1
                                        bugobj.answer = bug['answer']
                                        bugobj.status = bug['status']
                                        bugobj.level  = bug['level']
                                        bugobj.save()
                                        buglist.append(CheckGroupResult.Result(code=bugobj.code, version=bugobj.version, status=bugobj.status, level=bugobj.level, id=bugobj.id))
                                    else:
                                        # 新指摘
                                        bugobj = CheckBugItem(question=bug['question'], answer=bug['answer'],status=bug['status'],level=bug['level'])
                                        bugobj.author = request.user
                                        bugobj.itemcode = itm['code']
                                        bugobj.itemversion = itm['version']
                                        bugobj.setCode('BUG',CheckBugItem.nextCode('BUG'))
                                        bugobj.save()
                                        buglist.append(CheckGroupResult.Result(code=bugobj.code, version=bugobj.version, status=bugobj.status, level=bugobj.level, id=bugobj.id))
                        if count_ng > 0:
                            group_status = 'NG'
                        else:
                            group_status = 'OK'
                        grpobj.status = group_status
                        bugcounta = len([x for x in buglist if x.status.startswith('A')])
                        bugcountw = len([x for x in buglist if x.status.startswith('C')])
                        bugcountf = len(buglist) - bugcounta - bugcountw
                        grpobj.summary=json.dumps({'IG':count_ig,'OK':count_ok,'NG':count_ng,'BUGA':bugcounta,'BUGC':bugcountw,'BUGD':bugcountf})
                    grpobj.buglist=json.dumps(buglist)
                    grpobj.choices=json.dumps(choiceresult)
                    grpobj.save()
                    groupids.append(grpobj.id)
            chklist.groups = json.dumps(groupids)
            chklist.save()
            return HttpResponseRedirect(reverse('review:subproject', args=(form['project']['code'],form['subproject']['code'],)))
        else:
            return HttpResponseRedirect(reverse('review:subproject', args=(form['project']['code'],form['subproject']['code'],)))
    else:
        prjobj = getProject(projectcode)
        permlevel = permissionCheck(request, 2, prjobj)
        permdict = {'save': (permlevel > 2) and (prjobj.status == 'OP') }
        # 初次进入，设置初期值
        chk = get_object_or_404(CheckListResult, pk=reportid)
        chklist = list(CheckList.latest('WHERE code="%s"'%(chk.listcode,)))
        if len(chklist) > 0:
            form['project'] = {'code':projectcode}
            form['subproject'] = {'code':chk.subproject}
            form['report'] = {'id':reportid}
            form['checklist'] = {'code':chk.listcode,'version':chk.listversion, 'title':chk.title, 'lock':chk.lockstatus}
            authors = getAuthors(chk.subproject)
            if request.user in authors:
                form['report']['actor'] = True
            else:
                form['report']['actor'] = False
            prjsetting = getProjectSetting(prjobj, chklist[0])
            choices_org = prjsetting['choice']
            choices = [(x.value, x.text) for idx,x in enumerate(choices_org) if x.valid]
            bug1_org = prjsetting['bugstatus']
            bug1 = [(x.value, x.text) for idx,x in enumerate(bug1_org) if x.valid]
            bug2_org = prjsetting['buglevel']
            bug2 = [(x.value, x.text) for idx,x in enumerate(bug2_org) if x.valid]
            form['choice']    = tuple(choices)
            form['bugstatus'] = tuple(bug1)
            form['buglevel']  = tuple(bug2)
            form['groups'] = []
            for grp in CheckGroupResult.objects.filter(pk__in = json.loads(chk.groups)).order_by('groupcode'):
                if grp.status == 'IG':
                    form['groups'].append({'group':{'reportid':grp.id, 'id':grp.groupid, 'code':grp.groupcode, 'version':grp.groupversion, 'title':grp.grouptitle, 'summary':json.loads(grp.summary), 'valid':'0'},'items':[]})
                else:
                    form['groups'].append({'group':{'reportid':grp.id, 'id':grp.groupid, 'code':grp.groupcode, 'version':grp.groupversion, 'title':grp.grouptitle, 'summary':json.loads(grp.summary), 'valid':'1'},'items':[]})
                bugs = [CheckGroupResult.Result(*x) for x in json.loads(grp.buglist)]
                bugrecords = list(CheckBugItem.objects.filter(pk__in = [x.id for x in bugs]).order_by('code'))
                items = [CheckGroupResult.Choice(*x) for x in json.loads(grp.choices)]
                for item in items:
                    chkitem = CheckItem.objects.get(pk = item.id)
                    form['groups'][-1]['items'].append({'id':item.id, 'code':item.code, 'version':item.version, 'name':'item{}'.format(item.id),'title':chkitem.title, 'details':chkitem.details, 'choice':item.choice, 'error':'', 'buginitcount':0, 'bugs':[]})
                    bugcount = 0
                    for bugitem in bugrecords:
                        if bugitem.itemcode == item.code:
                            form['groups'][-1]['items'][-1]['bugs'].append({'question':bugitem.question, 'answer':bugitem.answer, 'status':bugitem.status, 'level':bugitem.level, 'code':bugitem.code,'version':bugitem.version,'id':bugitem.id,})
                            bugcount += 1
                    form['groups'][-1]['items'][-1]['buginitcount'] = bugcount
            subpobj = list(SubProject.latest('WHERE code="%s"'%(chk.subproject,)))
            navbar = []
            navbar.append({'link':reverse('review:projectview', args=(form['project']['code'],)), 'title':prjobj.title, 'param':['review:projectview',form['project']['code']]})
            navbar.append({'link':reverse('review:subproject', args=(form['project']['code'],form['subproject']['code'],)), 'title':subpobj[0].title, 'param':['review:subproject',form['project']['code'],form['subproject']['code']]})
            navbar.append({'link':'#', 'title':chk.title, 'param':['',]})
            return render(request, 'review/editpeercheck.html', {'form':form,'initvalue':json.dumps(form),'permission':permdict, 'navbar':navbar})

@login_required
def editproject(request, projectcode):
    if request.method == 'POST':
        form = json.loads(request.POST['initial'])
        form['title'] = request.POST.get('title','').strip()
        form['txtig'] = request.POST.get('txtig','').strip()
        form['txtok'] = request.POST.get('txtok','').strip()
        form['txtng'] = request.POST.get('txtng','').strip()
        form['status'] = request.POST['status']
        key1 = 'bug{}-code-{}'
        key2 = 'bug{}-text-{}'
        # bugstatus
        for bugsts in ('a','c','d'):
            keycount = 'count-bug' + bugsts
            keyform = 'bugsts' + bugsts
            form[keyform] = []
            maxno = 0
            flag_newcode = False
            for i in range(int(request.POST.get(keycount,0))):
                value1 = request.POST.get(key1.format(bugsts,i+1),'').strip()
                value2 = request.POST.get(key2.format(bugsts,i+1),'').strip()
                if len(value1) > 1:
                    curno = int(value1[1:])
                    if curno > maxno:
                        maxno = curno
                else:
                    flag_newcode = True
                form[keyform].append([value1,value2])
            if form['disable']:
                if flag_newcode:
                    for item in form[keyform]:
                        if len(item[0]) <= 1:
                            maxno += 1
                            item[0] += str(maxno)
            else:
                maxno = 0
                for item in form[keyform]:
                    maxno += 1
                    item[0] = item[0][0] + str(maxno)
        # bugcategory
        keycount = 'count-bugcate'
        keyform = 'bugcategory'
        form[keyform] = []
        maxno = {}
        flag_newcode = False
        for i in range(int(request.POST.get(keycount,0))):
            value1 = request.POST.get(key1.format('cate',i+1),'').strip()
            value2 = request.POST.get(key2.format('cate',i+1),'').strip()
            if len(value1) > 1:
                curno = int(value1[1:])
                if curno > maxno.get(value1[0],0):
                    maxno[value1[0]] = curno
            else:
                flag_newcode = True
            form[keyform].append([value1,value2])
        if form['disable']:
            if flag_newcode:
                for item in form[keyform]:
                    if len(item[0]) <= 1:
                        maxno.setdefault(item[0][0],0)
                        maxno[item[0][0]] += 1
                        item[0] += str(maxno[item[0][0]])
        else:
            maxno = {}
            for item in form[keyform]:
                maxno.setdefault(item[0][0],0)
                maxno[item[0][0]] += 1
                item[0] = item[0][0] + str(maxno[item[0][0]])
        flag_valid = True
        if form['title'] == '':
            form['title_error'] = 'Empty Project Name'
            flag_valid = False
        if form['txtig'] == '':
            form['txtig_error'] = 'Empty Ignore Text'
            flag_valid = False
        if form['txtok'] == '':
            form['txtok_error'] = 'Empty OK Text'
            flag_valid = False
        if form['txtng'] == '':
            form['txtng_error'] = 'Empty NG Text'
            flag_valid = False
        if flag_valid:
            initial = json.loads(request.POST['initial'])
            flag_changed = False
            if form['title'] != initial['title']:
                flag_changed = True
            elif form['status'] != initial['status']:
                flag_changed = True
            elif form['txtok'] != initial['txtok']:
                flag_changed = True
            elif form['txtig'] != initial['txtig']:
                flag_changed = True
            elif form['txtng'] != initial['txtng']:
                flag_changed = True
            else:
                for bugsts in ('a','c','d'):
                    keyform = 'bugsts' + bugsts
                    if len(form[keyform]) == len(initial[keyform]):
                        for idx in range(len(form[keyform])):
                            if form[keyform][idx][0] != initial[keyform][idx][0] or form[keyform][idx][1] != initial[keyform][idx][1]:
                                flag_changed = True
                                break
                    else:
                        flag_changed = True
                    if flag_changed:
                        break
                if len(form['bugcategory']) == len(initial['bugcategory']):
                    for idx in range(len(form['bugcategory'])):
                        if form['bugcategory'][idx][0] != initial['bugcategory'][idx][0] or form['bugcategory'][idx][1] != initial['bugcategory'][idx][1]:
                            flag_changed = True
                            break
                else:
                    flag_changed = True
            if flag_changed:
                choices = [Project.ChoiceItem(True, 'IG', form['txtig']),Project.ChoiceItem(True, 'OK', form['txtok']),Project.ChoiceItem(True, 'NG', form['txtng'])]
                bugstatus = [Project.BugStatus(True, x[0], x[1]) for x in form['bugstsa']] + [Project.BugStatus(True, x[0], x[1]) for x in form['bugstsc']] + [Project.BugStatus(True, x[0], x[1]) for x in form['bugstsd']]
                bugcategory = [Project.BugCategory(True, x[0], x[1]) for x in form['bugcategory']]
                if form['code']:
                    prjs = list(Project.objects.filter(code=form['code']).filter(version__gte=form['version']))
                    if len(prjs) > 1:
                        form['version_error'] = 'Someone has updated the project.'
                        return render(request, 'review/projectedit.html', {'projectcode':projectcode,'form':form,'initial':request.POST['initial'],'navbar':json.loads(request.POST['navbarinfo']),'navbarinfo':request.POST['navbarinfo']})
                    else:
                        prj = prjs[0]
                        prj.version += 1
                        prj.title = form['title']
                        prj.status = form['status']
                        prj.author = request.user
                        prj.choices = json.dumps(choices)
                        prj.bugstatus = json.dumps(bugstatus)
                        prj.bugcategory = json.dumps(bugcategory)
                        prj.id = None
                        prj.save()
                else:
                    codeno = Project.nextCode(Project.DefaultCategory)
                    prj = Project(title=form['title'], status=form['status'])
                    prj.author = request.user
                    prj.setCode(Project.DefaultCategory, codeno)
                    prj.choices = json.dumps(choices)
                    prj.bugstatus = json.dumps(bugstatus)
                    prj.bugcategory = json.dumps(bugcategory)
                    prj.save()
                    # create an empty checkgroup and checklist
                    grpobj = CheckGroup(project = prj.code, title = "AnonymousGroup")
                    grpobj.author = request.user
                    grpobj.setCode('GRP', CheckGroup.nextCode('GRP'))
                    grpobj.save()
                    lstobj = CheckList(project = prj.code, title = "AnonymousList", selfcheck = True)
                    lstobj.author = request.user
                    lstobj.setCode('LST', CheckList.nextCode('LST'))
                    lstobj.save()
            return HttpResponseRedirect(reverse('review:projectview', args=(prj.code,)))
        else:
            return render(request, 'review/projectedit.html', {'projectcode':projectcode,'form':form,'initial':request.POST['initial'],'navbar':json.loads(request.POST['navbarinfo']),'navbarinfo':request.POST['navbarinfo']})
    else:
        navbar = []
        if projectcode == '0':
            # add new project
            permlevel = permissionCheck(request, 9)
            initial = {'title':'', 'status':Project.StatusChoice[0][0], 'choices':Project.StatusChoice, 'code':'', 'version':0, 'title_error':'', 'version_error':'', 'disable':False, 'close':False}
            initial['txtig_error'] = ''
            initial['txtok_error'] = ''
            initial['txtng_error'] = ''
            initial['txtig'] = '関係なし'
            initial['txtok'] = 'OK'
            initial['txtng'] = '問題あり'
            initial['bugstsa'] = [['A1','修正中']]
            initial['bugstsc'] = [['C1', '確認待ち']]
            initial['bugstsd'] = [['D1', '完成'], ['D2', '変更不要'], ['D3', '転記']]
            initial['bugcategory'] = [['A1', '機能不具合'], ['E1', '成果物不具合']]
        else:
            # modify project
            permlevel = permissionCheck(request, 4, projectcode)
            prjlist = list(Project.latest('WHERE code="%s"'%(projectcode,)))
            prj = prjlist[0]
            initial = {'title':prj.title, 'status':prj.status, 'choices':Project.StatusChoice, 'code':prj.code, 'version':prj.version, 'title_error':'', 'version_error':'', 'disable':prj.status != Project.StatusInit, 'close':prj.status == Project.StatusClosed}
            choices = [Project.ChoiceItem(*x) for x in json.loads(prj.choices)]
            bugstatus = [Project.BugStatus(*x) for x in json.loads(prj.bugstatus)]
            bugcategory = [Project.BugCategory(*x) for x in json.loads(prj.bugcategory)]
            initial['txtig_error'] = ''
            initial['txtok_error'] = ''
            initial['txtng_error'] = ''
            initial['txtig'] = choices[0].text
            initial['txtok'] = choices[1].text
            initial['txtng'] = choices[2].text
            initial['bugstsa'] = []
            initial['bugstsc'] = []
            initial['bugstsd'] = []
            initial['bugcategory'] = []
            for bsts in bugstatus:
                if bsts.value.startswith('A'):
                    initial['bugstsa'].append([bsts.value, bsts.text])
                elif bsts.value.startswith('C'):
                    initial['bugstsc'].append([bsts.value, bsts.text])
                else:
                    initial['bugstsd'].append([bsts.value, bsts.text])
            for bcate in bugcategory:
                initial['bugcategory'].append([bcate.value, bcate.text])
            navbar.append({'link':reverse('review:projectview', args=(projectcode,)), 'title':prj.title, 'param':['review:projectview', projectcode]})
            navbar.append({'link':'#', 'title':'Edit Project', 'param':['',]})
        initial['init_count_buga'] = len(initial['bugstsa'])
        initial['init_count_bugc'] = len(initial['bugstsc'])
        initial['init_count_bugd'] = len(initial['bugstsd'])
        initial['init_count_bugcate'] = len(initial['bugcategory'])
        return render(request, 'review/projectedit.html', {'projectcode':projectcode,'form':initial,'initial':json.dumps(initial),'navbar':navbar,'navbarinfo':json.dumps(navbar)})

@login_required
def editselfcheck(request, projectcode, reportid):
    form = {}
    # DataStructure for Form
    # {'checklist':checklist-info, 'groups':[ group-info, ... ], 'choice': [], 'bugstatus':[], 'buglevel':[]}
    # group-info: {'group': grpobj, 'items': [ item-info, ... ] }
    # item-info: {'title': title, 'choice': choice, 'bugs': [] }
    if request.method == 'POST':
        # 整理POST数据
        initvalue = json.loads(request.POST['initvalue'])
        for key in ('report', 'project', 'subproject', 'checklist', 'choice'):
            form[key] = initvalue[key]
        form['groups'] = []
        flag_changed = False
        for grp in initvalue['groups']:
            form['groups'].append({'group':grp['group'], 'items':[]})
            if grp['group']['valid'] != '1':
                # 允许组无效变成有效，不允许有效变成无效
                form['groups'][-1]['group']['valid'] = request.POST['group-valid-{}'.format(form['groups'][-1]['group']['id'])]
            if form['groups'][-1]['group']['valid'] == '0':
                groupvalid = False
            else:
                groupvalid = True
            form['groups'][-1]['group']['changed'] = False
            if form['groups'][-1]['group']['valid'] != grp['group']['valid']:
                flag_changed = True
                form['groups'][-1]['group']['changed'] = True
            for itm in grp['items']:
                oldvalue = itm['choice']
                form['groups'][-1]['items'].append(itm)
                form['groups'][-1]['items'][-1]['bugs'] = []
                # read value from POST
                choicekey = form['groups'][-1]['items'][-1]['name']+'-choice'
                form['groups'][-1]['items'][-1]['choice'] = request.POST.get(choicekey, '')
                if groupvalid and form['groups'][-1]['items'][-1]['choice'] != oldvalue:
                    flag_changed = True
                    form['groups'][-1]['group']['changed'] = True
        if flag_changed:
            # 保存数据
            chklist = CheckListResult.objects.get(pk=reportid)
            chklist.author = request.user
            chklist.version += 1
            chklist.id = None
            groupids = []
            for grp in form['groups']:
                if not grp['group']['changed']:
                    groupids.append(int(grp['group']['reportid']))
                else:
                    grpobj = CheckGroupResult.objects.get(pk = grp['group']['reportid'])
                    grpobj.user = request.user
                    grpobj.id = None
                    grpobj.version += 1
                    choiceresult = []
                    if grp['group']['valid'] == '0':
                        grpobj.status = 'IG'
                        for itm in grp['items']:
                            choiceresult.append(CheckGroupResult.Choice(code=itm['code'],
                                version=itm['version'],
                                id=itm['id'],
                                choice='IG'))
                        grpobj.summary=json.dumps({'IG':len(grp['items']),'OK':0,'NG':0,'BUGA':0,'BUGC':0,'BUGD':0})
                    else:
                        count_ok, count_ng, count_ig = 0, 0, 0
                        for itm in grp['items']:
                            choiceresult.append(CheckGroupResult.Choice(code=itm['code'],
                                version=itm['version'],
                                id=itm['id'],
                                choice=itm['choice']))
                            if itm['choice'] == 'IG':
                                count_ig += 1
                            elif itm['choice'] == 'OK':
                                count_ok += 1
                            elif itm['choice'] == 'NG':
                                count_ng += 1
                            else:
                                pass
                        if count_ng > 0:
                            group_status = 'NG'
                        else:
                            group_status = 'OK'
                        grpobj.status = group_status
                        grpobj.summary=json.dumps({'IG':count_ig,'OK':count_ok,'NG':count_ng,'BUGA':0,'BUGC':0,'BUGD':0})
                    grpobj.choices=json.dumps(choiceresult)
                    grpobj.save()
                    groupids.append(grpobj.id)
            chklist.groups = json.dumps(groupids)
            chklist.save()
            return HttpResponseRedirect(reverse('review:subproject', args=(form['project']['code'],form['subproject']['code'],)))
        else:
            return HttpResponseRedirect(reverse('review:subproject', args=(form['project']['code'],form['subproject']['code'],)))
    else:
        prjobj = getProject(projectcode)
        permlevel = permissionCheck(request, 2, prjobj)
        permdict = {'save': (permlevel > 2) and (prjobj.status == 'OP') }
        # 初次进入，设置初期值
        chk = get_object_or_404(CheckListResult, pk=reportid)
        chklist = list(CheckList.latest('WHERE code="%s"'%(chk.listcode,)))
        if len(chklist) > 0:
            form['project'] = {'code':projectcode}
            form['subproject'] = {'code':chk.subproject}
            form['report'] = {'id':reportid}
            form['checklist'] = {'code':chk.listcode,'version':chk.listversion, 'title':chk.title, 'lock':chk.lockstatus}
            prjsetting = getProjectSetting(prjobj, chklist[0])
            choices_org = prjsetting['choice']
            choices = [(x.value, x.text) for idx,x in enumerate(choices_org) if x.valid]
            form['choice']    = tuple(choices)
            form['groups'] = []
            for grp in CheckGroupResult.objects.filter(pk__in = json.loads(chk.groups)).order_by('groupcode'):
                if grp.status == 'IG':
                    form['groups'].append({'group':{'reportid':grp.id, 'id':grp.groupid, 'code':grp.groupcode, 'version':grp.groupversion, 'title':grp.grouptitle, 'summary':json.loads(grp.summary), 'valid':'0'},'items':[]})
                else:
                    form['groups'].append({'group':{'reportid':grp.id, 'id':grp.groupid, 'code':grp.groupcode, 'version':grp.groupversion, 'title':grp.grouptitle, 'summary':json.loads(grp.summary), 'valid':'1'},'items':[]})
                items = [CheckGroupResult.Choice(*x) for x in json.loads(grp.choices)]
                for item in items:
                    chkitem = CheckItem.objects.get(pk = item.id)
                    form['groups'][-1]['items'].append({'id':item.id, 'code':item.code, 'version':item.version, 'name':'item{}'.format(item.id),'title':chkitem.title, 'details':chkitem.details, 'choice':item.choice, 'error':'', 'buginitcount':0, 'bugs':[]})
            subpobj = list(SubProject.latest('WHERE code="%s"'%(chk.subproject,)))
            navbar = []
            navbar.append({'link':reverse('review:projectview', args=(form['project']['code'],)), 'title':prjobj.title, 'param':['review:projectview',form['project']['code']]})
            navbar.append({'link':reverse('review:subproject', args=(form['project']['code'],form['subproject']['code'],)), 'title':subpobj[0].title, 'param':['review:subproject',form['project']['code'],form['subproject']['code']]})
            navbar.append({'link':'#', 'title':chk.title})
            return render(request, 'review/editselfcheck.html', {'form':form,'initvalue':json.dumps(form),'permission':permdict, 'navbar':navbar})

@login_required
def importchkitm(request, projectcode):
    if request.method == 'POST':
        rowlength = 3
        if 'excel_tab' in request.POST:
            data=request.POST['excel_tab'].splitlines()
            cread = CSVReader(data)
            outlist = []
            for row in cread:
                outlist.append([x.strip() for idx, x in enumerate(row) if idx < rowlength])
            for row in outlist:
                row[0]=row[0].replace(' ', '_')
                row.extend([''] * (rowlength - len(row)))
            navbar = []
            prj = getProject(projectcode)
            navbar.append({'link':reverse('review:projectview', args=(projectcode,)), 'title':prj.title, 'param':['review:projectview', projectcode]})
            navbar.append({'link':reverse('review:importcheckitem', args=(projectcode,)), 'title':'Import CheckItem', 'param':['review:importcheckitem', projectcode]})
            navbar.append({'link':'#', 'title':'Preview CheckItem', 'param':['',]})
            return render(request, 'review/previewchkitm.html', {'projectcode':projectcode, 'data':outlist,'initial':json.dumps(outlist),'navbar':navbar})
        elif 'initial' in request.POST:
            data = json.loads(request.POST['initial'])
            for row in data:
                if len(row) >= rowlength:
                    item = CheckItem(project=projectcode, title=row[1], details=row[2])
                    item.author = request.user
                    item.setCode(row[0],CheckItem.nextCode(row[0]))
                    item.save()
            return HttpResponseRedirect(reverse('review:projectview', args=(projectcode,)))
    else:
        navbar = []
        prj = getProject(projectcode)
        permlevel = permissionCheck(request, 4, prj)
        navbar.append({'link':reverse('review:projectview', args=(projectcode,)), 'title':prj.title, 'param':['review:projectview', projectcode]})
        navbar.append({'link':'#', 'title':'Import CheckItem', 'param':['',]})
        return render(request, 'review/importchkitm.html', {'projectcode':projectcode, 'navbar':navbar})

@login_required
def importusr(request):
    permlevel = permissionCheck(request, 9)
    if request.method == 'POST':
        if 'excel_tab' in request.POST:
            data=request.POST['excel_tab'].splitlines()
            cread = CSVReader(data)
            outlist = []
            for row in cread:
                outlist.append([x.strip() for idx, x in enumerate(row) if idx < 4])
            return render(request, 'review/previewusr.html', {'data':outlist,'initial':json.dumps(outlist)})
        elif 'initial' in request.POST:
            data = json.loads(request.POST['initial'])
            grp = list(Group.objects.filter(name='ProjectUser'))[0]
            for row in data:
                if len(row) > 3 and row[2]!='' and row[3]!='':
                    usr = User(first_name = row[1],
                               last_name  = row[0],
                               username   = row[2],
                               email      = row[2]+'@dev.kotei.co')
                    usr.set_password(row[3])
                    usr.save()
                    usr.groups.add(grp)
                    usr.save()
            return HttpResponseRedirect(reverse('review:index', args=()))
    return render(request, 'review/importusr.html', {})

@login_required
def lockreport(request, projectcode, reportcode):
    permlevel = permissionCheck(request, 3, projectcode)
    report = list(CheckListResult.latest('WHERE code="%s"'%(reportcode,)))[0]
    if report.lockstatus:
        report.lockstatus = False
        report.version += 1
        report.id = None
        report.save()
    else:
        status = getReportStatus(report)
        if status['status'] != 'NG':
            report.lockstatus = True
            report.version += 1
            report.id = None
            report.save()
    return HttpResponseRedirect(reverse('review:subproject', args=(projectcode, report.subproject)))

@login_required
def managechartgrp(request, projectcode):
    if request.method == 'POST':
        initial = json.loads(request.POST['initial'])
        chartidx = int(request.POST['chartindex'])
        basedata = initial[chartidx]['data']
        flag_changed = False
        newgroup = []
        newdata = []
        if request.POST.get('valid','').strip() == '':
            valid = False
        else:
            valid = True
        if request.POST.get('allowall','').strip() == '':
            allowall = False
        else:
            allowall = True
        if valid != initial[chartidx]['valid'] or allowall != initial[chartidx]['allowall']:
            flag_changed = True
        for idx in range(len(initial[chartidx]['groups'])):
            newval = request.POST.get('group-{}-{}'.format(chartidx, idx),'').strip()
            newgroup.append(newval)
            if newval != initial[chartidx]['groups'][idx]:
                flag_changed = True
        for i in range(len(basedata)):
            newdata.append([basedata[i][0]['code']])
            for j in range(1, len(basedata[i])):
                if j == len(basedata[i]) - 1 and newgroup[j - 1] == '':
                    # the last empty group
                    newval = False
                else:
                    # user append an subgroup
                    checked = request.POST.get(basedata[i][j]['id'],False)
                    if basedata[i][j]['checked']:
                        if checked=='on':
                            # both True
                            newval = True
                        else:
                            # remove
                            newval = False
                            flag_changed = True
                    else:
                        if checked=='on':
                            # add
                            newval = True
                            flag_changed = True
                        else:
                            # both True
                            newval = False
                newdata[i].append(newval)
        if flag_changed:
            chartlist = list(ChartGroup.latest('WHERE code="%s"'%(initial[chartidx]['code'],)))
            if len(chartlist) > 0:
                chartobj = chartlist[0]
                details = []
                for idx,grp in enumerate(newgroup):
                    if grp:
                        subcodes = []
                        for subj in range(len(newdata)):
                            if newdata[subj][idx+1]:
                                subcodes.append(newdata[subj][0])
                        details.append(ChartGroup.Group(grp, subcodes))
                chartobj.details = json.dumps(details)
                chartobj.author = request.user
                chartobj.valid = valid
                chartobj.allowall = allowall
                chartobj.id = None
                chartobj.version += 1
                chartobj.save()
        return HttpResponseRedirect(reverse('review:projectview', args=(projectcode,)))
    else:
        prj = getProject(projectcode)
        permlevel = permissionCheck(request, 3, prj)
        subprjs = getSubProjects(projectcode)
        subprjinfo = []
        for subprj in subprjs:
            subprjinfo.append([subprj.code, subprj.title])
        charts = list(ChartGroup.latest('WHERE project="%s"'%(projectcode,)))
        data = []
        # value: {'title':'...', 'code':'...', 'valid':T/F, 'allowall':T/F, 'savable':T/F,
        #         'groups':[group-title,...], 'data':...}
        #   data: switchInfo[i][j] i=0..count_subprjs-1, j=0..count_subgrps
        #     switchInfo(j=0): {'code':subproject-code 'title':subproject-title }
        #     switchInfo(j>0): {'id':'...', 'checked':T/F }
        for chart in charts:
            data.append({'title':chart.title, 'code':chart.code, 'valid':chart.valid, 'allowall':chart.allowall, 'groups':[], 'data':[]})
            # set 'savable' for every chart
            if permlevel > 3:
                # project administrators
                savable = True
            else:
                if chart.valid:
                    if chart.allowall:
                        # allow everyone to modify
                        savable = True
                    else:
                        savable = False
                else:
                    savable = False
            if not savable:
                # check whether current author is the author of the chartgroup
                testchart = list(ChartGroup.objects.filter(code=chart.code).filter(version=1))[0]
                if request.user == testchart.author:
                    savable = True
            data[-1]['savable'] = savable
            subgroups = [ChartGroup.Group(*x) for x in json.loads(chart.details)]
            subgroups.append(ChartGroup.Group('',[]))
            for subgrp in subgroups:
                data[-1]['groups'].append(subgrp.subtitle)
            for subcode in subprjinfo:
                data[-1]['data'].append([{'code':subcode[0],'title':subcode[1]}])
                for idx,subgrp in enumerate(subgroups):
                    if subcode[0] in subgrp.subprjs:
                        checked = True
                    else:
                        checked = False
                    data[-1]['data'][-1].append({'id':'chk-{}-{}-{}'.format(chart.code,subcode[0],idx),'checked':checked})
        navbar = []
        navbar.append({'link':reverse('review:projectview', args=(projectcode,)), 'title':prj.title, 'param':['review:projectview', projectcode]})
        navbar.append({'link':'#', 'title':'Manage ChartGroup', 'param':['',]})
        return render(request, 'review/managechartgrp.html', {'projectcode':projectcode, 'data':data, 'navbar':navbar, 'initial':json.dumps(data)})

@login_required
def managechkgrp(request, projectcode):
    if request.method == 'POST':
        groups = json.loads(request.POST['groupinfo'])
        initial = json.loads(request.POST['initial'])
        for idx,grp in enumerate(groups):
            orgdata = [x['groups'][idx] for x in initial]
            newdata = [request.POST.get('chk-{}-{}'.format(initial[x]['item']['id'],idx+1),False) for x in range(len(initial))]
            flag_same = True
            details = []
            for idx2 in range(len(orgdata)):
                if orgdata[idx2]:
                    if newdata[idx2]=='on':
                        # both True
                        details.append(CheckGroup.GroupDetailItem(True,initial[idx2]['item']['code'],initial[idx2]['item']['version'],initial[idx2]['item']['id']))
                    else:
                        # remove
                        flag_same = False
                else:
                    if newdata[idx2]=='on':
                        flag_same = False
                        details.append(CheckGroup.GroupDetailItem(True,initial[idx2]['item']['code'],initial[idx2]['item']['version'],initial[idx2]['item']['id']))
                    else:
                        # both False
                        pass
            if not flag_same:
                grplist = list(CheckGroup.latest('WHERE code="%s"'%(grp['code'],)))
                if len(grplist) > 0:
                    grpobj = grplist[0]
                    grpobj.details=CheckGroup.packDetails(details)
                    grpobj.version += 1
                    grpobj.author = request.user
                    grpobj.id = None
                    grpobj.save()
        return HttpResponseRedirect(reverse('review:projectview', args=(projectcode,)))
    else:
        itmlist = list(CheckItem.latest('WHERE project="%s"'%(projectcode,)))
        grplist = list(CheckGroup.latest('WHERE project="%s"'%(projectcode,)))
        groups = [{'id':x.id, 'title':x.title, 'code':x.code} for x in grplist if x.valid]
        data = []
        for item in itmlist:
            if item.valid:
                data.append({'item':{'id':item.id,'code':item.code,'version':item.version,'title':item.title},'groups':[]})
                for grp in grplist:
                    if grp.valid:
                        contains = grp.contains(item.code)
                        if contains:
                            data[-1]['groups'].append(contains.valid)
                        else:
                            data[-1]['groups'].append(False)
        navbar = []
        prj = getProject(projectcode)
        permlevel = permissionCheck(request, 4, prj)
        navbar.append({'link':reverse('review:projectview', args=(projectcode,)), 'title':prj.title, 'param':['review:projectview', projectcode]})
        navbar.append({'link':'#', 'title':'Manage CheckGroup', 'param':['',]})
        return render(request, 'review/managechkgrp.html', {'projectcode':projectcode, 'groups':groups, 'data':data, 'groupinfo':json.dumps(groups), 'initial':json.dumps(data), 'navbar':navbar})

@login_required
def managechklst(request, projectcode):
    if request.method == 'POST':
        lists = json.loads(request.POST['listinfo'])
        initial = json.loads(request.POST['initial'])
        for idx,lst in enumerate(lists):
            orgdata = [x['lists'][idx] for x in initial]
            newdata = [request.POST.get('chk-{}-{}'.format(initial[x]['group']['id'],idx+1),False) for x in range(len(initial))]
            flag_same = True
            details = []
            for idx2 in range(len(orgdata)):
                if orgdata[idx2]:
                    if newdata[idx2]=='on':
                        # both True
                        details.append(CheckList.GroupItem(True,initial[idx2]['group']['code'],initial[idx2]['group']['version'],initial[idx2]['group']['id']))
                    else:
                        # remove
                        flag_same = False
                else:
                    if newdata[idx2]=='on':
                        flag_same = False
                        details.append(CheckList.GroupItem(True,initial[idx2]['group']['code'],initial[idx2]['group']['version'],initial[idx2]['group']['id']))
                    else:
                        # both False
                        pass
            if not flag_same:
                lstlist = list(CheckList.latest('WHERE code="%s"'%(lst['code'],)))
                if len(lstlist) > 0:
                    lstobj = lstlist[0]
                    lstobj.groups = json.dumps(details)
                    lstobj.version += 1
                    lstobj.author = request.user
                    lstobj.id = None
                    lstobj.save()
        return HttpResponseRedirect(reverse('review:projectview', args=(projectcode,)))
    else:
        lstlist = list(CheckList.latest('WHERE project="%s"'%(projectcode,)))
        grplist = list(CheckGroup.latest('WHERE project="%s"'%(projectcode,)))
        lists = [{'id':x.id, 'title':x.title, 'code':x.code} for x in lstlist if x.valid]
        data = []
        for item in grplist:
            if item.valid:
                data.append({'group':{'id':item.id,'code':item.code,'version':item.version,'title':item.title},'lists':[]})
                for lst in lstlist:
                    if lst.valid:
                        groups = [CheckList.GroupItem(*x) for x in json.loads(lst.groups)]
                        finds = [x for x in groups if x.code == item.code]
                        if len(finds) > 0:
                            data[-1]['lists'].append(finds[0].valid)
                        else:
                            data[-1]['lists'].append(False)
        navbar = []
        prj = getProject(projectcode)
        permlevel = permissionCheck(request, 4, prj)
        navbar.append({'link':reverse('review:projectview', args=(projectcode,)), 'title':prj.title, 'param':['review:projectview', projectcode]})
        navbar.append({'link':'#', 'title':'Manage CheckList', 'param':['',]})
        return render(request, 'review/managechklst.html', {'projectcode':projectcode, 'lists':lists, 'data':data, 'listinfo':json.dumps(lists), 'initial':json.dumps(data), 'navbar':navbar})

@login_required
def manageusr(request, projectcode):
    if request.method == 'POST':
        prjlist = list(Project.latest('WHERE code="%s"'%(projectcode,)))
        if len(prjlist) > 0:
            prjobj = prjlist[0]
            initusers = json.loads(request.POST['userinfo'])
            initgroups = json.loads(request.POST['groupinfo'])
            key1 = 'chk-{}-0'
            key2 = 'chk-{}-1'
            set1 = set()
            set2 = set()
            for user in initusers:
                if request.POST.get(key1.format(user['id']),"off") == "on":
                    set1.add(user['id'])
                    set2.add(user['id'])
                if request.POST.get(key2.format(user['id']),"off") == "on":
                    set2.add(user['id'])
            orgset1 = set(initgroups[0])
            orgset2 = set(initgroups[1])
            diffset1 = orgset1 ^ set1
            diffset2 = orgset2 ^ set2
            if len(diffset1) > 0 or len(diffset2) > 0:
                prjobj.id = None
                prjobj.author = request.user
                prjobj.users_admin = json.dumps(list(set1))
                prjobj.users = json.dumps(list(set2))
                prjobj.version += 1
                prjobj.save()
            return HttpResponseRedirect(reverse('review:projectview', args=(projectcode,)))
        else:
            return HttpResponse('Project Code Error')
    else:
        prjlist = list(Project.latest('WHERE code="%s"'%(projectcode,)))
        if len(prjlist) > 0:
            prjobj = prjlist[0]
            permlevel = permissionCheck(request, 4, prjobj)
            permdict = {'projectadmin':prjobj.status != Project.StatusClosed }
            groups = [json.loads(prjobj.users_admin),json.loads(prjobj.users)]
            grp = Group.objects.get(name='ProjectUser')
            users = [{'id':x.id,'firstname':x.first_name,'lastname':x.last_name,'username':x.username} for x in grp.user_set.all()]
            navbar = []
            navbar.append({'link':reverse('review:projectview', args=(projectcode,)), 'title':prjobj.title, 'param':['review:projectview', projectcode]})
            navbar.append({'link':'#', 'title':'Manage User', 'param':['',]})
            return render(request, 'review/manageusr.html', {'projectcode':projectcode, 'groups':groups, 'users':users, 'groupinfo':json.dumps(groups), 'userinfo':json.dumps(users), 'navbar':navbar, 'permission':permdict})
        else:
            return HttpResponse('Project Code Error')

@login_required
def modifychkgrp(request, projectcode, groupcode):
    if request.method == 'POST':
        items = json.loads(request.POST['initial'])
        form = {}
        form['title'] = request.POST.get('title','').strip()
        if request.POST.get('valid','').strip() == '':
            form['valid'] = False
        else:
            form['valid'] = True
        if form['title'] == '':
            form['title_error'] = 'Empty Title'
            return render(request, 'review/modifychkgrp.html', {'projectcode':projectcode, 'groupcode':groupcode, 'form':form, 'items':items, 'navbar':json.loads(request.POST['navbarinfo']), 'navbarinfo':request.POST['navbarinfo'], 'initial':request.POST['initial']})
        else:
            if form['title'] != items[-1]['title'] or form['valid'] != items[-1]['valid']:
                # form changed
                chkgroup = CheckGroup.objects.get(pk = items[-1]['id'])
                chkgroup.id = None
                chkgroup.title = form['title']
                chkgroup.valid = form['valid']
                chkgroup.version += 1
                chkgroup.author = request.user
                chkgroup.save()
                if chkgroup.valid:
                    verupCheckGroup(request.user, projectcode, chkgroup)
                else:
                    invalidCheckGroup(request.user, projectcode, chkgroup)
            else:
                # form unchanged
                pass
            return HttpResponseRedirect(reverse('review:managecheckgroup', args=(projectcode,)))
    else:
        navbar = []
        prj = getProject(projectcode)
        permlevel = permissionCheck(request, 4, prj)
        items = []
        for group in list(CheckGroup.objects.filter(code=groupcode).filter(project=projectcode).order_by('version')):
            items.append({'title':group.title, 'valid':group.valid, 'version':group.version, 'author':getUserName(group.author), 'id':group.id, 'update_time':localTime(group.update_time), 'details':[CheckGroup.GroupDetailItem(*x)._asdict() for x in json.loads(group.details)]})
        form  = {}
        if len(items) > 0:
            navbar.append({'link':reverse('review:projectview', args=(projectcode,)), 'title':prj.title, 'param':['review:projectview', projectcode]})
            navbar.append({'link':reverse('review:managecheckgroup', args=(projectcode,)), 'title':'Manage CheckGroup', 'param':['review:managecheckgroup', projectcode]})
            navbar.append({'link':'#', 'title':'Modify CheckGroup', 'param':['',]})
            form['title'] = items[-1]['title']
            form['valid'] = items[-1]['valid']
            form['disable'] = (prj.status != Project.StatusInit)
            return render(request, 'review/modifychkgrp.html', {'projectcode':projectcode, 'groupcode':groupcode, 'form':form, 'items':items, 'navbar':navbar, 'navbarinfo':json.dumps(navbar), 'initial':json.dumps(items)})
        else:
            raise Http404('No Checkgroup.')

@login_required
def modifychkitm(request, projectcode, itemcode):
    if request.method == 'POST':
        items = json.loads(request.POST['initial'])
        form = {}
        form['title'] = request.POST.get('title','').strip()
        form['details'] = request.POST.get('details','').strip()
        if request.POST.get('valid','').strip() == '':
            form['valid'] = False
        else:
            form['valid'] = True
        if form['title'] == '':
            form['title_error'] = 'Empty Title'
            return render(request, 'review/modifychkitm.html', {'projectcode':projectcode, 'itemcode':itemcode, 'form':form, 'items':items, 'navbar':json.loads(request.POST['navbarinfo']), 'navbarinfo':request.POST['navbarinfo'], 'initial':request.POST['initial']})
        else:
            if form['title'] != items[-1]['title'] or form['details'] != items[-1]['details'] or form['valid'] != items[-1]['valid']:
                # form changed
                chkitem = CheckItem.objects.get(pk = items[-1]['id'])
                chkitem.id = None
                chkitem.title = form['title']
                chkitem.details = form['details']
                chkitem.valid = form['valid']
                chkitem.version += 1
                chkitem.author = request.user
                chkitem.save()
                if chkitem.valid:
                    verupCheckItem(request.user, projectcode, chkitem)
                else:
                    invalidCheckItem(request.user, projectcode, chkitem)
            else:
                # form unchanged
                pass
            return HttpResponseRedirect(reverse('review:managecheckgroup', args=(projectcode,)))
    else:
        navbar = []
        prj = getProject(projectcode)
        permlevel = permissionCheck(request, 4, prj)
        items = []
        for item in list(CheckItem.objects.filter(code=itemcode).filter(project=projectcode).order_by('version')):
            items.append({'title':item.title, 'details':item.details, 'valid':item.valid, 'version':item.version, 'author':getUserName(item.author), 'id':item.id, 'update_time':localTime(item.update_time)})
        form  = {}
        if len(items) > 0:
            navbar.append({'link':reverse('review:projectview', args=(projectcode,)), 'title':prj.title, 'param':['review:projectview', projectcode]})
            navbar.append({'link':reverse('review:managecheckgroup', args=(projectcode,)), 'title':'Manage CheckGroup', 'param':['review:managecheckgroup', projectcode]})
            navbar.append({'link':'#', 'title':'Modify CheckItem', 'param':['',]})
            form['title'] = items[-1]['title']
            form['details'] = items[-1]['details']
            form['valid'] = items[-1]['valid']
            form['disable'] = (prj.status != Project.StatusInit)
            return render(request, 'review/modifychkitm.html', {'projectcode':projectcode, 'itemcode':itemcode, 'form':form, 'items':items, 'navbar':navbar, 'navbarinfo':json.dumps(navbar), 'initial':json.dumps(items)})
        else:
            raise Http404('No Checkitem.')

@login_required
def modifychklst(request, projectcode, listcode):
    if request.method == 'POST':
        items = json.loads(request.POST['initial'])
        form = {}
        form['title'] = request.POST.get('title','').strip()
        if request.POST.get('selfcheck','').strip() == '':
            form['selfcheck'] = False
        else:
            form['selfcheck'] = True
        if request.POST.get('valid','').strip() == '':
            form['valid'] = False
        else:
            form['valid'] = True
        if form['title'] == '':
            form['title_error'] = 'Empty Title'
            return render(request, 'review/modifychklst.html', {'projectcode':projectcode, 'listcode':listcode, 'form':form, 'items':items, 'navbar':json.loads(request.POST['navbarinfo']), 'navbarinfo':request.POST['navbarinfo'], 'initial':request.POST['initial']})
        else:
            if form['title'] != items[-1]['title'] or form['selfcheck'] != items[-1]['selfcheck'] or form['valid'] != items[-1]['valid']:
                # form changed
                chklist = CheckList.objects.get(pk = items[-1]['id'])
                chklist.id = None
                chklist.title = form['title']
                chklist.valid = form['valid']
                chklist.version += 1
                chklist.author = request.user
                chklist.selfcheck = form['selfcheck']
                chklist.save()
            else:
                # form unchanged
                pass
            return HttpResponseRedirect(reverse('review:managechecklist', args=(projectcode,)))
    else:
        navbar = []
        prj = getProject(projectcode)
        permlevel = permissionCheck(request, 4, prj)
        items = []
        for item in list(CheckList.objects.filter(code=listcode).filter(project=projectcode).order_by('version')):
            items.append({'title':item.title, 'valid':item.valid, 'version':item.version, 'author':getUserName(item.author), 'id':item.id, 'update_time':localTime(item.update_time), 'details':[CheckList.GroupItem(*x)._asdict() for x in json.loads(item.groups)], 'selfcheck':item.selfcheck})
        form  = {}
        if len(items) > 0:
            navbar.append({'link':reverse('review:projectview', args=(projectcode,)), 'title':prj.title, 'param':['review:projectview', projectcode]})
            navbar.append({'link':reverse('review:managechecklist', args=(projectcode,)), 'title':'Manage CheckList', 'param':['review:managechecklist', projectcode]})
            navbar.append({'link':'#', 'title':'Modify CheckList', 'param':['',]})
            form['title'] = items[-1]['title']
            form['valid'] = items[-1]['valid']
            form['selfcheck'] = items[-1]['selfcheck']
            form['disable'] = (prj.status != Project.StatusInit)
            return render(request, 'review/modifychklst.html', {'projectcode':projectcode, 'listcode':listcode, 'form':form, 'items':items, 'navbar':navbar, 'navbarinfo':json.dumps(navbar), 'initial':json.dumps(items)})
        else:
            raise Http404('No Checklist.')

@login_required
def modifysubprj(request, projectcode, subprojectcode):
    if request.method == 'POST':
        items = json.loads(request.POST['initial'])
        form = {}
        form['title'] = request.POST.get('title','').strip()
        form['details'] = request.POST.get('details','').strip()
        if request.POST.get('valid','').strip() == '':
            form['valid'] = False
        else:
            form['valid'] = True
        if form['title'] == '':
            form['title_error'] = 'Empty Title'
            return render(request, 'review/modifysubprj.html', {'projectcode':projectcode, 'subprojectcode':subprojectcode, 'form':form, 'items':items, 'navbar':json.loads(request.POST['navbarinfo']), 'navbarinfo':request.POST['navbarinfo'], 'initial':request.POST['initial']})
        else:
            if form['title'] != items[-1]['title'] or form['details'] != items[-1]['details'] or form['valid'] != items[-1]['valid']:
                # form changed
                subprj = SubProject.objects.get(pk = items[-1]['id'])
                subprj.id = None
                subprj.title = form['title']
                subprj.details = form['details']
                subprj.valid = form['valid']
                subprj.version += 1
                subprj.author = request.user
                subprj.save()
            else:
                # form unchanged
                pass
            return HttpResponseRedirect(reverse('review:projectview', args=(projectcode,)))
    else:
        navbar = []
        prj = getProject(projectcode)
        permlevel = permissionCheck(request, 4, prj)
        items = []
        for item in list(SubProject.objects.filter(code=subprojectcode).filter(project=projectcode).order_by('version')):
            items.append({'title':item.title, 'details':item.details, 'valid':item.valid, 'version':item.version, 'author':getUserName(item.author), 'id':item.id, 'update_time':localTime(item.update_time)})
        form  = {}
        if len(items) > 0:
            navbar.append({'link':reverse('review:projectview', args=(projectcode,)), 'title':prj.title, 'param':['review:projectview', projectcode]})
            navbar.append({'link':'#', 'title':'Modify SubProject', 'param':['',]})
            form['title'] = items[-1]['title']
            form['details'] = items[-1]['details']
            form['valid'] = items[-1]['valid']
            form['disable'] = (prj.status != Project.StatusInit)
            return render(request, 'review/modifysubprj.html', {'projectcode':projectcode, 'subprojectcode':subprojectcode, 'form':form, 'items':items, 'navbar':navbar, 'navbarinfo':json.dumps(navbar), 'initial':json.dumps(items)})
        else:
            raise Http404('No Subproject.')

def viewproject(request, projectcode):
    prjlist = list(Project.latest('WHERE code="%s"'%(projectcode,)))
    if len(prjlist) > 0:
        prj = prjlist[0]
        getProjectDailyInfo(prj)
        chks = CheckList.latest('WHERE project="%s"' % (prj.code,))
        grps = CheckGroup.latest('WHERE project="%s"' % (prj.code,))
        grpmap = {}
        for grp in grps:
            grpmap[grp.code] = grp.title
        data = []
        for chk in chks:
            groups = [CheckList.GroupItem(*x) for x in json.loads(chk.groups)]
            data.append({'title':chk.title, 'id':chk.id, 'code':chk.code, 'version':chk.version, 'selfcheck':chk.selfcheck,
                'groups':[{'title':grpmap[x.code], 'id':x.id, 'code':x.code, 'version':x.version} for x in groups]})
        subps = getSubProjects(prj)
        prjinfo = getProjectInfo(prj)
        subps_filter = []
        for subp in subps:
            details = ''
            for chklst in sorted(prjinfo.keys()):
                details += '* **Locked**:{:>02} **Ok**:{:>02} **Ng**:{:>02} `{}` \n'.format(prjinfo[chklst]['subproject'][subp.code]['c_locked'],
                    prjinfo[chklst]['subproject'][subp.code]['c_ok'],
                    prjinfo[chklst]['subproject'][subp.code]['c_ng'],
                    prjinfo[chklst]['checklist'].title)
            subps_filter.append({'code':subp.code, 'title':subp.title, 'details':details})
        permlevel = permissionCheck(request, 0, projectcode)
        permdict = {}
        if prj.status == Project.StatusInit:
            # 项目状态修改权限
            permdict['project'] = (permlevel > 3)
            # 管理类权限设置
            permdict['manage'] = (permlevel > 3)
        elif prj.status == Project.StatusOpen:
            # 项目状态修改权限
            permdict['project'] = (permlevel > 3)
            # 管理类权限设置
            permdict['manage'] = (permlevel > 3)
        else:
            # 项目状态修改权限
            permdict['project'] = (permlevel > 3)
            # 项目关闭，不可修改
            permdict['manage'] = False
        navbar = []
        navbar.append({'link':'#', 'title':prj.title, 'param':['',projectcode]})
        return render(request, 'review/project.html', {'project':prj, 'checklists':data, 'subprojects':subps_filter, 'permission':permdict, 'navbar':navbar})
    else:
        raise Http404("Project does not exist")

def viewsubproject(request, projectcode, subprojectcode):
    subplist = list(SubProject.latest('WHERE code="%s"' % (subprojectcode,)))
    if len(subplist) > 0:
        subp = subplist[0]
        chks = CheckList.latest('WHERE project="%s"' % (subp.project,))
        data = []
        reports = [{'title':x.title, 'id':x.id, 'code':x.code, 'listcode':x.listcode,'lock':x.lockstatus,'status':getReportStatus(x)} for x in CheckListResult.latest('WHERE subproject="%s"' % (subp.code,))]
        sccount = 0
        for chk in chks:
            if len(json.loads(chk.groups)) > 0:
                clickable = True
            else:
                clickable = False
            data.append({'title':chk.title, 'id':chk.id, 'code':chk.code, 'version':chk.version, 'selfcheck':chk.selfcheck, 'clickable':clickable, 'reports':[x for x in reports if x['listcode']==chk.code]})
            if chk.selfcheck:
                sccount += len(data[-1]['reports'])
        projectobj = getProject(subp.project)
        permlevel = permissionCheck(request, 2, projectobj)
        permdict = {'projectuser':permlevel>2}
        navbar = []
        navbar.append({'link':reverse('review:projectview', args=(subp.project,)), 'title':projectobj.title, 'param':['review:projectview', subp.project]})
        navbar.append({'link':'#', 'title':subp.title, 'param':['',]})
        return render(request, 'review/subproject.html', {'subproject':subp, 'checklists':data, 'selfcheck':(sccount>0), 'permission':permdict, 'navbar':navbar})
    else:
        raise Http404("Project does not exist")

@login_required
def setup(request):
    CheckItem.objects.all().delete()
    CheckGroup.objects.all().delete()
    CheckList.objects.all().delete()
    CheckBugItem.objects.all().delete()
    CheckGroupResult.objects.all().delete()
    CheckListResult.objects.all().delete()
    SubProject.objects.all().delete()
    Project.objects.all().delete()
    return HttpResponseRedirect(reverse('review:index', args=()))

@login_required
def dashusr(request, projectcode):
    actions = getNextAction(request, projectcode)
    prj = getProject(projectcode)
    permlevel = permissionCheck(request, 3, prj)
    navbar = []
    navbar.append({'link':reverse('review:projectview', args=(projectcode,)), 'title':prj.title, 'param':['review:projectview', projectcode]})
    navbar.append({'link':'#', 'title':'Dashboard', 'param':['',]})
    return render(request, 'review/dashusr.html', {'reports':actions, 'navbar':navbar})

@login_required
def projectdash(request, projectcode):
    prj = getProject(projectcode)
    permlevel = permissionCheck(request, 2, prj)
    prjinfo = getProjectInfo(prj)
    chartgroups = [x.code for x in ChartGroup.latest('WHERE project="%s"'%(prj.code,)) if x.valid]
    chartinfo = getChartInfo(prjinfo, *chartgroups)
    navbar = []
    navbar.append({'link':reverse('review:projectview', args=(projectcode,)), 'title':prj.title, 'param':['review:projectview', projectcode]})
    navbar.append({'link':'#', 'title':'Dashboard', 'param':['',]})
    return render(request, 'review/dashproject.html', {'chartinfo':chartinfo, 'navbar':navbar})

