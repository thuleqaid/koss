# -*- coding:utf-8 -*-
import json
import datetime
from django.contrib.auth.models import User, Group
from django.http import Http404
from .models import *

class CSVReader(object):
    CONST_LINETERMINATOR_STRIP = chr(10) + chr(13)
    CONST_LINETERMINATOR_INSERT = "\n"
    def __init__(self, lines):
        self._data=[]
        flag_cell = False
        cell_data = ''
        for line in lines:
            parts=line.rstrip(self.CONST_LINETERMINATOR_STRIP).split("\t")
            if len(parts) > 0:
                if flag_cell:
                    # last cell of the last line startswith a "
                    if len(parts) > 1:
                        # unfinished cell will be finished
                        if parts[0].endswith('"'):
                            cell_data = cell_data+self.CONST_LINETERMINATOR_INSERT+parts[0]
                            self._data[-1].append(cell_data[1:-1])
                        else:
                            self._data[-1].append(cell_data[1:])
                            self._data.append([])
                            self._data[-1].append(parts[0])
                        flag_cell = False
                        cell_data=''
                        self._data[-1].extend(parts[1:])
                    else:
                        if parts[0].endswith('"'):
                            cell_data = cell_data+self.CONST_LINETERMINATOR_INSERT+parts[0]
                            self._data[-1].append(cell_data[1:-1])
                            flag_cell = False
                            cell_data=''
                        else:
                            # unfinished cell continues
                            cell_data=cell_data+self.CONST_LINETERMINATOR_INSERT+parts[0]
                else:
                    self._data.append([])
                    self._data[-1].extend(parts[:-1])
                    if parts[-1].startswith('"'):
                        if len(parts[-1]) > 1 and parts[-1].endswith('"'):
                            self._data[-1].append(parts[-1][1:-1])
                        else:
                            flag_cell = True
                            cell_data = parts[-1]
                    else:
                        self._data[-1].append(parts[-1])
        else:
            if flag_cell:
                cell_data = cell_data+self.CONST_LINETERMINATOR_INSERT
        if flag_cell:
            self._data[-1].append(cell_data)
    def __len__(self):
        return len(self._data)
    def __getitem__(self, idx):
        return self._data[idx]

def permission(request, project=None):
    ''' return permission level
        0: anonymous user
        1: user
        2: review system user
        3: current project's user
        4: current project's admin-user
        9: super-user
    '''
    user = request.user
    ret = 0
    if user.is_active:
        ret = 1
        if user.is_superuser:
            ret = 9
        else:
            group = Group.objects.get(name='ProjectUser')
            if group in user.groups.all():
                ret = 2
                if project:
                    prjobj = getProject(project)
                    if prjobj:
                        users = json.loads(prjobj.users_admin)
                        if user.id in users:
                            ret = 4
                        else:
                            users = json.loads(prjobj.users)
                            if user.id in users:
                                ret = 3
    return ret

def permissionCheck(request, minlevel, project=None):
    ''' check whether permlevel >= minlevel '''
    permlevel = permission(request, project)
    if permlevel >= minlevel:
        return permlevel
    else:
        raise Http404('No Permission.')

def getProject(project):
    if isinstance(project, Project):
        prjobj = project
    else:
        prjlist = list(Project.latest('WHERE code="%s"'%(project,)))
        if len(prjlist) > 0:
            prjobj = prjlist[0]
        else:
            prjobj = None
    return prjobj

def getProjectSetting(project, checklist=None):
    prjobj = getProject(project)
    outdict = { }
    outdict['choice'] = [Project.ChoiceItem(*x) for x in json.loads(prjobj.choices)]
    outdict['bugstatus'] = [Project.BugStatus(*x) for x in json.loads(prjobj.bugstatus)]
    outdict['buglevel'] = [Project.BugCategory(*x) for x in json.loads(prjobj.bugcategory)]
    return outdict

def getReportStatus(report):
    firstver = list(CheckListResult.objects.filter(code = report.code).filter(version = 1))[0]
    grouplist = list(CheckGroupResult.objects.filter(pk__in=json.loads(report.groups)))
    status = 'IG'
    keylist = ('IG', 'OK', 'NG', 'BUGA', 'BUGC', 'BUGD')
    count = dict(zip(keylist,[0]*len(keylist)))
    for group in grouplist:
        summary = json.loads(group.summary)
        for key in keylist:
            count[key] += summary[key]
        if group.status == 'NG':
            status = 'NG'
        elif group.status == 'OK':
            if status == 'IG':
                status = 'OK'
    count['status']=status
    count['author']=firstver.author
    return count

def getAuthors(subproject):
    subplist = list(SubProject.latest('WHERE code="%s"' % (subproject,)))
    if len(subplist) > 0:
        subp = subplist[0]
        chks = [x.code for x in CheckList.latest('WHERE project="%s"' % (subp.project,)) if x.selfcheck]
        reports = list(CheckListResult.objects.filter(subproject = subp.code).filter(listcode__in = chks).filter(version = 1))
        authors = [x.author for x in reports]
    else:
        authors = []
    return authors

def getNextAction(request, project):
    if isinstance(project, Project):
        prjcode = project.code
    else:
        prjcode = project
    # 取得所有selfcheck的checklist code
    selfchks = [x.code for x in CheckList.latest('WHERE project="%s"' % (prjcode,)) if x.selfcheck]
    # 取得所有subproject的code
    subplist = [x.code for x in SubProject.latest('WHERE project="%s"' % (prjcode,))]
    joblist = []
    for subp in subplist:
        # 取得subproject的所有report
        reports = list(CheckListResult.objects.filter(subproject = subp))
        # 取得修改过peercheck report的用户
        modifiers = set([x.author for x in reports if x.listcode not in selfchks])
        # 取得selfcheck report的作者
        authors = set([x.author for x in reports if x.listcode in selfchks and x.version == 1])
        # 取得peercheck的检查者
        reviewer = modifiers - authors
        if request.user in authors:
            isAuthor = True
        else:
            isAuthor = False
        if request.user in reviewer:
            isReviewer = True
        else:
            isReviewer = False
        if len(reviewer) < 1:
            noreviewer = True
        else:
            noreviewer = False
        if isAuthor or isReviewer:
            latest = {}
            for report in reports:
                if report.code not in latest:
                    latest[report.code] = report
                else:
                    if report.version > latest[report.code].version:
                        latest[report.code] = report
            for code, report in latest.items():
                status = getReportStatus(report)
                if status['status'] == 'NG':
                    if isAuthor:
                        if status['BUGA'] > 0:
                            # 存在修改的指摘
                            joblist.append(dict(status))
                            joblist[-1]['selfcheck'] = False
                            joblist[-1]['project'] = prjcode
                            joblist[-1]['subproject'] = subp
                            joblist[-1]['reportauthor'] = report.author
                            joblist[-1]['reportid'] = report.id
                            joblist[-1]['reportcode'] = report.code
                            joblist[-1]['reportversion'] = report.version
                            joblist[-1]['reporttitle'] = report.title
                            joblist[-1]['isAuthor'] = isAuthor
                            joblist[-1]['noReviewer'] = False
                        elif (status['BUGA'] == 0 and status['BUGC'] == 0):
                            # 没有指摘（selfcheck）
                            joblist.append(dict(status))
                            joblist[-1]['selfcheck'] = True
                            joblist[-1]['project'] = prjcode
                            joblist[-1]['subproject'] = subp
                            joblist[-1]['reportauthor'] = report.author
                            joblist[-1]['reportid'] = report.id
                            joblist[-1]['reportcode'] = report.code
                            joblist[-1]['reportversion'] = report.version
                            joblist[-1]['reporttitle'] = report.title
                            joblist[-1]['isAuthor'] = isAuthor
                            joblist[-1]['noReviewer'] = False
                        elif noreviewer:
                            # 没有确认人
                            joblist.append(dict(status))
                            joblist[-1]['selfcheck'] = False
                            joblist[-1]['project'] = prjcode
                            joblist[-1]['subproject'] = subp
                            joblist[-1]['reportauthor'] = report.author
                            joblist[-1]['reportid'] = report.id
                            joblist[-1]['reportcode'] = report.code
                            joblist[-1]['reportversion'] = report.version
                            joblist[-1]['reporttitle'] = report.title
                            joblist[-1]['isAuthor'] = isAuthor
                            joblist[-1]['noReviewer'] = True
                    elif isReviewer:
                        if status['BUGC'] > 0:
                            # 存在需要确认的修改
                            joblist.append(dict(status))
                            joblist[-1]['selfcheck'] = False
                            joblist[-1]['project'] = prjcode
                            joblist[-1]['subproject'] = subp
                            joblist[-1]['reportauthor'] = report.author
                            joblist[-1]['reportid'] = report.id
                            joblist[-1]['reportcode'] = report.code
                            joblist[-1]['reportversion'] = report.version
                            joblist[-1]['reporttitle'] = report.title
                            joblist[-1]['isAuthor'] = False
                            joblist[-1]['noReviewer'] = False
                    else:
                        pass
    return joblist

def getProjectInfo(project):
    if isinstance(project, Project):
        prjcode = project.code
    else:
        prjcode = project
    subprjlist = list(SubProject.latest('WHERE project="%s"'%(prjcode,)))
    chklist = list(CheckList.latest('WHERE project="%s"'%(prjcode,)))
    reports = list(CheckListResult.latest())
    outinfo = {}
    # key: checklist-code
    # value:{'checklist':checklist-obj,'subproject':dict1, 'c_locked':N1, 'c_ok':N2, 'c_ng':N3}
    #   dict1:
    #      key:subproject-code
    #      value:{'subproject':subproject-obj, 'report':[(report-obj,report-status),...], 'c_locked':N1, 'c_ok':N2, 'c_ng':N3}
    for chk in chklist:
        outinfo[chk.code] = {'checklist': chk, 'subproject':{}}
        chkreports = [x for x in reports if x.listcode == chk.code]
        count0_lock = 0
        count0_lockable = 0
        count0_unlockable = 0
        for subp in subprjlist:
            outinfo[chk.code]['subproject'][subp.code] = {'subproject':subp, 'report':[]}
            count_lock = 0
            count_lockable = 0
            count_unlockable = 0
            for subreport in [x for x in chkreports if x.subproject == subp.code]:
                outinfo[chk.code]['subproject'][subp.code]['report'].append((subreport, getReportStatus(subreport)))
                if subreport.lockstatus:
                    count_lock += 1
                else:
                    if outinfo[chk.code]['subproject'][subp.code]['report'][-1][1]['status'] == 'NG':
                        count_unlockable +=1
                    else:
                        count_lockable += 1
            outinfo[chk.code]['subproject'][subp.code]['c_locked'] = count_lock
            outinfo[chk.code]['subproject'][subp.code]['c_ok'] = count_lockable
            outinfo[chk.code]['subproject'][subp.code]['c_ng'] = count_unlockable
            if count_lockable + count_unlockable + count_lock > 0:
                if count_lockable + count_unlockable == 0:
                    count0_lock += 1
                elif count_unlockable > 0:
                    count0_unlockable += 1
                else:
                    count0_lockable += 1
        outinfo[chk.code]['c_locked'] = count0_lock
        outinfo[chk.code]['c_ok'] = count0_lockable
        outinfo[chk.code]['c_ng'] = count0_unlockable
    return outinfo

def getUserName(user):
    if isinstance(user, User):
        if user.last_name:
            retname = user.last_name + user.first_name
        else:
            retname = user.username
    else:
        retname = ''
    return retname

def verupCheckItem(user, projectcode, chkitem):
    grplist = list(CheckGroup.latest('WHERE project="%s"'%(projectcode,)))
    for grp in grplist:
        details = grp.unpackDetails(grp.details)
        for idx,detail in enumerate(details):
            if detail.code == chkitem.code:
                details[idx] = CheckGroup.GroupDetailItem(valid=True, code=chkitem.code, version=chkitem.version, id=chkitem.id)
                break
        else:
            continue
        grp.details = json.dumps(details)
        grp.id = None
        grp.version += 1
        grp.author = user
        grp.save()
        verupCheckGroup(user, projectcode, grp)

def verupCheckGroup(user, projectcode, chkgrp):
    chklist = list(CheckList.latest('WHERE project="%s"'%(projectcode,)))
    for chk in chklist:
        groups = [CheckList.GroupItem(*x) for x in json.loads(chk.groups)]
        for idx,group in enumerate(groups):
            if group.code == chkgrp.code:
                groups[idx] = CheckList.GroupItem(valid=True, code=chkgrp.code, version=chkgrp.version, id=chkgrp.id)
                break
        else:
            continue
        chk.groups = json.dumps(groups)
        chk.id = None
        chk.version += 1
        chk.author = user
        chk.save()

def localTime(dt, offset=8):
    newdt = dt + datetime.timedelta(hours=offset)
    return newdt.strftime("%Y/%m/%d %H:%M:%S")
