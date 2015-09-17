import json
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
                            joblist[-1]['reportid'] = report.id
                            joblist[-1]['reportcode'] = report.code
                            joblist[-1]['reportversion'] = report.version
                            joblist[-1]['reporttitle'] = report.title
                        elif (status['BUGA'] == 0 and status['BUGC'] == 0):
                            # 没有指摘（selfcheck）
                            joblist.append(dict(status))
                            joblist[-1]['selfcheck'] = True
                            joblist[-1]['project'] = prjcode
                            joblist[-1]['subproject'] = subp
                            joblist[-1]['reportid'] = report.id
                            joblist[-1]['reportcode'] = report.code
                            joblist[-1]['reportversion'] = report.version
                            joblist[-1]['reporttitle'] = report.title
                    elif isReviewer:
                        if status['BUGC'] > 0:
                            # 存在需要确认的修改
                            joblist.append(dict(status))
                            joblist[-1]['selfcheck'] = False
                            joblist[-1]['project'] = prjcode
                            joblist[-1]['subproject'] = subp
                            joblist[-1]['reportid'] = report.id
                            joblist[-1]['reportcode'] = report.code
                            joblist[-1]['reportversion'] = report.version
                            joblist[-1]['reporttitle'] = report.title
                    else:
                        pass
    return joblist
