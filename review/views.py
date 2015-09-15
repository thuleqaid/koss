import json
from django.shortcuts import render, get_object_or_404
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

def importchkitm(request, projectcode):
    if request.method == 'POST':
        if 'excel_tab' in request.POST:
            data=request.POST['excel_tab'].splitlines()
            cread = CSVReader(data)
            outlist = []
            for row in cread:
                outlist.append([x.strip() for idx, x in enumerate(row) if idx < 3])
            return render(request, 'review/previewchkitm.html', {'projectcode':projectcode, 'data':outlist,'initial':json.dumps(outlist)})
        elif 'initial' in request.POST:
            data = json.loads(request.POST['initial'])
            for row in data:
                if len(row) > 2:
                    item = CheckItem(project=projectcode, title=row[1], details=row[2])
                    item.setCode(row[0],CheckItem.nextCode(row[0]))
                    item.save()
            return HttpResponseRedirect(reverse('review:projectview', args=(projectcode,)))
    return render(request, 'review/importchkitm.html', {'projectcode':projectcode})

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
                    grpobj.id = None
                    grpobj.save()
        return HttpResponseRedirect(reverse('review:projectview', args=(projectcode,)))
    else:
        itmlist = list(CheckItem.latest('WHERE project="%s"'%(projectcode,)))
        grplist = list(CheckGroup.latest('WHERE project="%s"'%(projectcode,)))
        groups = [{'id':x.id, 'title':x.title, 'code':x.code} for x in grplist]
        data = []
        for item in itmlist:
            data.append({'item':{'id':item.id,'code':item.code,'version':item.version,'title':item.title},'groups':[]})
            for grp in grplist:
                contains = grp.contains(item.code)
                if contains:
                    data[-1]['groups'].append(contains.valid)
                else:
                    data[-1]['groups'].append(False)
        return render(request, 'review/managechkgrp.html', {'projectcode':projectcode, 'groups':groups, 'data':data, 'groupinfo':json.dumps(groups), 'initial':json.dumps(data)})

def addchkgrp(request):
    if request.method == 'POST':
        projectcode = request.POST['projectcode']
        grptitle    = request.POST['title'].strip()
        if grptitle:
            grpobj      = CheckGroup(project = projectcode, title = grptitle)
            grpobj.setCode('GRP', CheckGroup.nextCode('GRP'))
            grpobj.save()
        return HttpResponseRedirect(reverse('review:managecheckgroup', args=(projectcode,)))

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
                    lstobj.id = None
                    lstobj.save()
        return HttpResponseRedirect(reverse('review:projectview', args=(projectcode,)))
    else:
        lstlist = list(CheckList.latest('WHERE project="%s"'%(projectcode,)))
        grplist = list(CheckGroup.latest('WHERE project="%s"'%(projectcode,)))
        lists = [{'id':x.id, 'title':x.title, 'code':x.code} for x in lstlist]
        data = []
        for item in grplist:
            data.append({'group':{'id':item.id,'code':item.code,'version':item.version,'title':item.title},'lists':[]})
            for lst in lstlist:
                groups = [CheckList.GroupItem(*x) for x in json.loads(lst.groups)]
                finds = [x for x in groups if x.code == item.code]
                if len(finds) > 0:
                    data[-1]['lists'].append(finds[0].valid)
                else:
                    data[-1]['lists'].append(False)
        return render(request, 'review/managechklst.html', {'projectcode':projectcode, 'lists':lists, 'data':data, 'listinfo':json.dumps(lists), 'initial':json.dumps(data)})

def addchklst(request):
    if request.method == 'POST':
        projectcode = request.POST['projectcode']
        lsttitle    = request.POST['title'].strip()
        if lsttitle:
            if 'selfcheck' in request.POST:
                lsttype = True
            else:
                lsttype = False
            lstobj = CheckList(project = projectcode, title = lsttitle, selfcheck = lsttype)
            lstobj.setCode('LST', CheckList.nextCode('LST'))
            lstobj.save()
        return HttpResponseRedirect(reverse('review:managechecklist', args=(projectcode,)))

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
        subps = SubProject.latest('WHERE project="%s"' % (prj.code,))
        return render(request, 'review/project.html', {'project':prj, 'checklists':data, 'subprojects':subps})
    else:
        raise Http404("Project does not exist")

def subproject(request, subprojectcode):
    subplist = list(SubProject.latest('WHERE code="%s"' % (subprojectcode,)))
    if len(subplist) > 0:
        subp = subplist[0]
        chks = CheckList.latest('WHERE project="%s"' % (subp.project,))
        data = []
        reports = [{'title':x.title, 'id':x.id, 'listcode':x.listcode} for x in CheckListResult.latest('WHERE subproject="%s"' % (subp.code,))]
        for chk in chks:
            data.append({'title':chk.title, 'id':chk.id, 'code':chk.code, 'version':chk.version, 'selfcheck':chk.selfcheck,'reports':[x for x in reports if x['listcode']==chk.code]})
        return render(request, 'review/subproject.html', {'subproject':subp, 'checklists':data, })
    else:
        raise Http404("Project does not exist")

def addsubprj(request, projectcode):
    if request.method == 'POST':
        if 'excel_tab' in request.POST:
            data=request.POST['excel_tab'].splitlines()
            cread = CSVReader(data)
            outlist = []
            for row in cread:
                outlist.append([x.strip() for idx, x in enumerate(row) if idx < 2])
            return render(request, 'review/previewsubprj.html', {'projectcode':projectcode, 'data':outlist,'initial':json.dumps(outlist)})
        elif 'initial' in request.POST:
            data = json.loads(request.POST['initial'])
            for row in data:
                if len(row) > 1:
                    subp = SubProject(project=projectcode, title=row[0], details=row[1])
                    subp.setCode('SUBP',SubProject.nextCode('SUBP'))
                    subp.save()
            return HttpResponseRedirect(reverse('review:projectview', args=(projectcode,)))
    else:
        return render(request, 'review/addsubprj.html', {'projectcode':projectcode, })

def selfchecknew(request, subprojectcode, checklistcode):
    form = {}
    # DataStructure for Form
    # {'checklist':checklist-info, 'groups':[ group-info, ... ], 'choice': [], 'bugstatus':[], 'buglevel':[]}
    # group-info: {'group': grpobj, 'items': [ item-info, ... ] }
    # item-info: {'title': title, 'choice': choice, 'bugs': [] }
    if request.method == 'POST':
        # 整理POST数据
        initvalue = json.loads(request.POST['initvalue'])
        for key in ('subproject', 'checklist', 'choice'):
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
            title = '{}[{}]'.format(form['checklist']['title'],timezone.now())
            chklist = CheckListResult(subproject=form['subproject']['code'], title=title, listcode=form['checklist']['code'], listversion=form['checklist']['version'], groupcount=len(form['groups']))
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
                    grpobj.summary=json.dumps([('IG',len(grp['items'])),('OK',0),('NG',0)])
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
                    grpobj.summary=json.dumps([('IG',count_ig),('OK',count_ok),('NG',count_ng)])
                grpobj.choices=json.dumps(choiceresult)
                grpobj.setCode('RGRP', CheckGroupResult.nextCode('RGRP'))
                grpobj.save()
                groupids.append(grpobj.id)
            chklist.groups = json.dumps(groupids)
            chklist.setCode('RLIST',CheckListResult.nextCode('RLIST'))
            chklist.save()
            return HttpResponseRedirect(reverse('review:subproject', args=(form['subproject']['code'],)))
        else:
            return render(request, 'review/newselfcheck.html', {'form':form,'initvalue':request.POST['initvalue'],})
    else:
        # 初次进入，设置初期值
        chklist = list(CheckList.latest('WHERE code="%s"'%(checklistcode,)))
        if len(chklist) > 0:
            chk = chklist[0]
            form['subproject'] = {'code':subprojectcode}
            form['checklist'] = {'code':chk.code,'version':chk.version, 'title':chk.title}
            choices_org = [CheckList.ChoiceItem(*x) for x in json.loads(chk.choices)]
            choices = [(x.value, x.text) for idx,x in enumerate(choices_org) if x.valid]
            form['choice']    = tuple(choices)
            groups = [CheckList.GroupItem(*x) for x in json.loads(chk.groups)]
            grpobjs = CheckGroup.objects.filter(pk__in = [x.id for x in groups if x.valid]).order_by('code')
            form['groups'] = []
            for grp in grpobjs:
                form['groups'].append({'group':{'id':grp.id, 'code':grp.code, 'version':grp.version, 'title':grp.title, 'valid':'1'},'items':[]})
                items = [CheckGroup.GroupDetailItem(*x) for x in json.loads(grp.details)]
                for item in CheckItem.objects.filter(pk__in = [x.id for x in items if x.valid]).order_by('code'):
                    form['groups'][-1]['items'].append({'id':item.id, 'code':item.code, 'version':item.version, 'name':'item{}'.format(item.id),'title':item.title, 'choice':'', 'error':'', 'buginitcount':0, 'bugs':[]})
            return render(request, 'review/newselfcheck.html', {'form':form,'initvalue':json.dumps(form),})
        else:
            raise Http404("CheckList does not exist")

def selfcheckedit(request, reportid):
    form = {}
    # DataStructure for Form
    # {'checklist':checklist-info, 'groups':[ group-info, ... ], 'choice': [], 'bugstatus':[], 'buglevel':[]}
    # group-info: {'group': grpobj, 'items': [ item-info, ... ] }
    # item-info: {'title': title, 'choice': choice, 'bugs': [] }
    if request.method == 'POST':
        # 整理POST数据
        initvalue = json.loads(request.POST['initvalue'])
        for key in ('report', 'subproject', 'checklist', 'choice'):
            form[key] = initvalue[key]
        form['groups'] = []
        flag_changed = False
        for grp in initvalue['groups']:
            form['groups'].append({'group':grp['group'], 'items':[]})
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
            # 全部检查项已经check过，保存数据
            chklist = CheckListResult.objects.get(pk=reportid)
            chklist.version += 1
            chklist.id = None
            groupids = []
            for grp in form['groups']:
                if not grp['group']['changed']:
                    groupids.append(int(grp['group']['reportid']))
                else:
                    grpobj = CheckGroupResult.objects.get(pk = grp['group']['reportid'])
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
                        grpobj.summary=json.dumps([('IG',len(grp['items'])),('OK',0),('NG',0)])
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
                        grpobj.summary=json.dumps([('IG',count_ig),('OK',count_ok),('NG',count_ng)])
                    grpobj.choices=json.dumps(choiceresult)
                    grpobj.save()
                    groupids.append(grpobj.id)
            chklist.groups = json.dumps(groupids)
            chklist.save()
            return HttpResponseRedirect(reverse('review:subproject', args=(form['subproject']['code'],)))
        else:
            return HttpResponseRedirect(reverse('review:subproject', args=(form['subproject']['code'],)))
    else:
        # 初次进入，设置初期值
        chk = get_object_or_404(CheckListResult, pk=reportid)
        chklist = list(CheckList.latest('WHERE code="%s"'%(chk.listcode,)))
        if len(chklist) > 0:
            form['subproject'] = {'code':chk.subproject}
            form['report'] = {'id':reportid}
            form['checklist'] = {'code':chk.listcode,'version':chk.listversion, 'title':chk.title}
            choices_org = [CheckList.ChoiceItem(*x) for x in json.loads(chklist[0].choices)]
            choices = [(x.value, x.text) for idx,x in enumerate(choices_org) if x.valid]
            form['choice']    = tuple(choices)
            form['groups'] = []
            for grp in CheckGroupResult.objects.filter(pk__in = json.loads(chk.groups)).order_by('groupcode'):
                if grp.status == 'IG':
                    form['groups'].append({'group':{'reportid':grp.id, 'id':grp.groupid, 'code':grp.groupcode, 'version':grp.groupversion, 'title':grp.grouptitle, 'valid':'0'},'items':[]})
                else:
                    form['groups'].append({'group':{'reportid':grp.id, 'id':grp.groupid, 'code':grp.groupcode, 'version':grp.groupversion, 'title':grp.grouptitle, 'valid':'1'},'items':[]})
                items = [CheckGroupResult.Choice(*x) for x in json.loads(grp.choices)]
                for item in items:
                    itemtitle = CheckItem.objects.get(pk = item.id).title
                    form['groups'][-1]['items'].append({'id':item.id, 'code':item.code, 'version':item.version, 'name':'item{}'.format(item.id),'title':itemtitle, 'choice':item.choice, 'error':'', 'buginitcount':0, 'bugs':[]})
            return render(request, 'review/editselfcheck.html', {'form':form,'initvalue':json.dumps(form),})

def peerchecknew(request, subprojectcode, checklistcode):
    form = {}
    # DataStructure for Form
    # {'checklist':checklist-info, 'groups':[ group-info, ... ], 'choice': [], 'bugstatus':[], 'buglevel':[]}
    # group-info: {'group': grpobj, 'items': [ item-info, ... ] }
    # item-info: {'title': title, 'choice': choice, 'bugs': [ bug-info, ... ] }
    # bug-info: {'question':question, 'answer':answer, 'status': status, 'level': bug-level }
    if request.method == 'POST':
        # 整理POST数据
        initvalue = json.loads(request.POST['initvalue'])
        for key in ('subproject', 'checklist', 'choice', 'bugstatus', 'buglevel'):
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
            chklist = CheckListResult(subproject=form['subproject']['code'], title=title, listcode=form['checklist']['code'], listversion=form['checklist']['version'], groupcount=len(form['groups']))
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
                    grpobj.summary=json.dumps([('IG',len(grp['items'])),('OK',0),('NG',0)])
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
                                bugobj.itemcode = itm['code']
                                bugobj.itemversion = itm['version']
                                bugobj.setCode('BUG',CheckBugItem.nextCode('BUG'))
                                bugobj.save()
                                buglist.append(CheckGroupResult.Result(code=bugobj.code, version=bugobj.version, status=bugobj.status, level=bugobj.level, itemcode=itm['code']))
                    if count_ng > 0:
                        group_status = 'NG'
                    else:
                        group_status = 'OK'
                    grpobj = CheckGroupResult(groupid=grp['group']['id'],
                            groupcode=grp['group']['code'],
                            groupversion=grp['group']['version'],
                            grouptitle=grp['group']['title'],
                            status=group_status)
                    grpobj.summary=json.dumps([('IG',count_ig),('OK',count_ok),('NG',count_ng)])
                grpobj.choices=json.dumps(choiceresult)
                grpobj.setCode('RGRP', CheckGroupResult.nextCode('RGRP'))
                grpobj.save()
                groupids.append(grpobj.id)
            chklist.groups = json.dumps(groupids)
            chklist.setCode('RLIST',CheckListResult.nextCode('RLIST'))
            chklist.save()
            return HttpResponseRedirect(reverse('review:subproject', args=(form['subproject']['code'],)))
        else:
            return render(request, 'review/newpeercheck.html', {'form':form,'initvalue':request.POST['initvalue'],})
    else:
        # 初次进入，设置初期值
        chklist = list(CheckList.latest('WHERE code="%s"'%(checklistcode,)))
        if len(chklist) > 0:
            chk = chklist[0]
            form['subproject'] = {'code':subprojectcode}
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
                    form['groups'][-1]['items'].append({'id':item.id, 'code':item.code, 'version':item.version, 'name':'item{}'.format(item.id),'title':item.title, 'choice':'', 'error':'', 'buginitcount':0, 'bugs':[]})
                    form['groups'][-1]['items'][-1]['bugs'].append({'question':'', 'answer':'', 'status':form['bugstatus'][0][0], 'level':form['buglevel'][0][0]})
            return render(request, 'review/newpeercheck.html', {'form':form,'initvalue':json.dumps(form),})
        else:
            raise Http404("CheckList does not exist")

def peercheckedit(request, reportid):
    form = {}
    # DataStructure for Form
    # {'checklist':checklist-info, 'groups':[ group-info, ... ], 'choice': [], 'bugstatus':[], 'buglevel':[]}
    # group-info: {'group': grpobj, 'items': [ item-info, ... ] }
    # item-info: {'title': title, 'choice': choice, 'bugs': [] }
    if request.method == 'POST':
        # 整理POST数据
        initvalue = json.loads(request.POST['initvalue'])
        for key in ('report', 'subproject', 'checklist', 'choice'):
            form[key] = initvalue[key]
        form['groups'] = []
        flag_changed = False
        for grp in initvalue['groups']:
            form['groups'].append({'group':grp['group'], 'items':[]})
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
            # 全部检查项已经check过，保存数据
            chklist = CheckListResult.objects.get(pk=reportid)
            chklist.version += 1
            chklist.id = None
            groupids = []
            for grp in form['groups']:
                if not grp['group']['changed']:
                    groupids.append(int(grp['group']['reportid']))
                else:
                    grpobj = CheckGroupResult.objects.get(pk = grp['group']['reportid'])
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
                        grpobj.summary=json.dumps([('IG',len(grp['items'])),('OK',0),('NG',0)])
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
                        grpobj.summary=json.dumps([('IG',count_ig),('OK',count_ok),('NG',count_ng)])
                    grpobj.choices=json.dumps(choiceresult)
                    grpobj.save()
                    groupids.append(grpobj.id)
            chklist.groups = json.dumps(groupids)
            chklist.save()
            return HttpResponseRedirect(reverse('review:subproject', args=(form['subproject']['code'],)))
        else:
            return HttpResponseRedirect(reverse('review:subproject', args=(form['subproject']['code'],)))
    else:
        # 初次进入，设置初期值
        chk = get_object_or_404(CheckListResult, pk=reportid)
        chklist = list(CheckList.latest('WHERE code="%s"'%(chk.listcode,)))
        if len(chklist) > 0:
            form['subproject'] = {'code':chk.subproject}
            form['report'] = {'id':reportid}
            form['checklist'] = {'code':chk.listcode,'version':chk.listversion, 'title':chk.title}
            choices_org = [CheckList.ChoiceItem(*x) for x in json.loads(chklist[0].choices)]
            choices = [(x.value, x.text) for idx,x in enumerate(choices_org) if x.valid]
            bug1_org = [CheckList.BugStatus(*x) for x in json.loads(chklist[0].bugstatus)]
            bug1 = [(x.value, x.text) for idx,x in enumerate(bug1_org) if x.valid]
            bug2_org = [CheckList.BugCategory(*x) for x in json.loads(chklist[0].bugcategory)]
            bug2 = [(x.value, x.text) for idx,x in enumerate(bug2_org) if x.valid]
            form['choice']    = tuple(choices)
            form['bugstatus'] = tuple(bug1)
            form['buglevel']  = tuple(bug2)
            form['groups'] = []
            for grp in CheckGroupResult.objects.filter(pk__in = json.loads(chk.groups)).order_by('groupcode'):
                if grp.status == 'IG':
                    form['groups'].append({'group':{'reportid':grp.id, 'id':grp.groupid, 'code':grp.groupcode, 'version':grp.groupversion, 'title':grp.grouptitle, 'valid':'0'},'items':[]})
                else:
                    form['groups'].append({'group':{'reportid':grp.id, 'id':grp.groupid, 'code':grp.groupcode, 'version':grp.groupversion, 'title':grp.grouptitle, 'valid':'1'},'items':[]})
                items = [CheckGroupResult.Choice(*x) for x in json.loads(grp.choices)]
                for item in items:
                    itemtitle = CheckItem.objects.get(pk = item.id).title
                    form['groups'][-1]['items'].append({'id':item.id, 'code':item.code, 'version':item.version, 'name':'item{}'.format(item.id),'title':itemtitle, 'choice':item.choice, 'error':'', 'buginitcount':0, 'bugs':[]})
            return render(request, 'review/editpeercheck.html', {'form':form,'initvalue':json.dumps(form),})

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
    CheckItem.objects.all().delete()
    CheckGroup.objects.all().delete()
    CheckList.objects.all().delete()
    CheckBugItem.objects.all().delete()
    CheckGroupResult.objects.all().delete()
    CheckListResult.objects.all().delete()
    SubProject.objects.all().delete()
    Project.objects.all().delete()
    return HttpResponseRedirect(reverse('review:index', args=()))
