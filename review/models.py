# -*- coding:utf-8 -*-
import json
import collections
import logging
from django.db import models
from django.db.models import Max, Min
from django.contrib.auth.models import User
from django.utils.encoding import python_2_unicode_compatible

logger = logging.getLogger('review')
# Create your models here.
CONST_CODE_LEN = 63
CONST_CODE_NUMBER_LEN = 8
class BaseVersionTable(models.Model):
    code        = models.CharField(max_length=CONST_CODE_LEN)
    version     = models.PositiveIntegerField(default=1)
    update_time = models.DateTimeField(auto_now_add=True)
    def splitCode(self):
        #idx = self.code.index('#')
        idx = len(self.code) - CONST_CODE_NUMBER_LEN - 1
        return self.code[0:idx+1], int(self.code[idx+1:])
    def setCode(self,category,no):
        #fmt = '%s%#0'+str(CONST_CODE_NUMBER_LEN)+'d'
        fmt = '%s%0'+str(CONST_CODE_NUMBER_LEN)+'d'
        self.code = fmt%(category,no)
    def strPrefix(self):
        return '[%d][%s][%d]'%(self.id,self.code,self.version)
    def isEqual(self, other, *excludeFields):
        excludes = ('id','update_time')+excludeFields
        same = True
        for key in self.__dict__.keys():
            if not key.startswith('_') and key not in excludes:
                if self.__dict__[key] != other.__dict__.get(key,None):
                    same = False
                    break
        return same
    @classmethod
    def nextCode(cls, category):
        codes = cls.objects.filter(code__startswith='%s'%(category,)).order_by('-code')[:1]
        if len(codes) > 0:
            code1, code2 = codes[0].splitCode()
            code2 += 1
        else:
            code2 = 1
        return code2
    @classmethod
    def oldest(cls, where=''):
        return cls.objects.raw('SELECT *, Min(version) FROM %s %s GROUP BY code'%(cls.getTableName(), where))
    @classmethod
    def latest(cls, where=''):
        return cls.objects.raw('SELECT *, Max(version) FROM %s %s GROUP BY code'%(cls.getTableName(), where))
    @classmethod
    def getTableName(cls):
        appname = cls.__module__[0:cls.__module__.index('.')]
        clsname = cls.__name__
        tablename = '%s_%s'%(appname,clsname)
        return tablename.lower()
    class Meta:
        abstract = True

@python_2_unicode_compatible
class Project(BaseVersionTable):
    DefaultCategory = 'PRJ'
    StatusOpen   = 'OP'
    StatusClosed = 'ED'
    StatusChoice = ((StatusOpen, 'Open'), (StatusClosed, 'Closed'),)
    ChoiceItem = collections.namedtuple('ChoiceItem', ['valid','value','text'])
    BugStatus = collections.namedtuple('BugStatus', ['valid','value','text'])
    BugCategory = collections.namedtuple('BugCategory', ['valid','value','text'])
    author = models.ForeignKey(User)
    title = models.CharField(max_length=240)
    status = models.CharField(max_length=2, choices=StatusChoice, default=StatusOpen)
    choices = models.TextField(default=json.dumps([ChoiceItem(True,'IG','関係なし'), ChoiceItem(True, 'OK', 'OK'), ChoiceItem(True, 'NG', '問題あり')])) # check item choices
    bugstatus = models.TextField(default=json.dumps([BugStatus(True, 'A1', '修正中'), BugStatus(True, 'C1', '確認待ち'), BugStatus(True, 'D1', '完成'), BugStatus(True, 'D2', '変更不要'), BugStatus(True, 'D3', '転記')]))
    bugcategory= models.TextField(default=json.dumps([BugCategory(True, 'A1', '機能不具合'), BugCategory(True, 'E1', '成果物不具合'),]))
    users_admin = models.TextField(default=json.dumps([]))
    users = models.TextField(default=json.dumps([]))
    def __str__(self):
        return self.strPrefix()+self.title
    class Meta:
        unique_together = [['code', 'version'],]

@python_2_unicode_compatible
class SubProject(BaseVersionTable):
    author = models.ForeignKey(User)
    project = models.CharField(max_length=CONST_CODE_LEN, default='')
    title = models.CharField(max_length=240)
    details = models.TextField(default='')
    def __str__(self):
        return self.strPrefix()+self.title
    class Meta:
        unique_together = [['code', 'version'],]

@python_2_unicode_compatible
class CheckList(BaseVersionTable):
    GroupItem = collections.namedtuple('GroupItem', ['valid','code','version','id'])
    author = models.ForeignKey(User)
    project = models.CharField(max_length=CONST_CODE_LEN)
    title = models.CharField(max_length=240)
    selfcheck = models.BooleanField(default=False)
    groups = models.TextField(default=json.dumps([])) # list of GroupItem
    choices = models.TextField(default=json.dumps([]))
    bugstatus = models.TextField(default=json.dumps([]))
    bugcategory= models.TextField(default=json.dumps([]))
    def __str__(self):
        return self.strPrefix()+self.title
    class Meta:
        unique_together = [['code', 'version'],]

@python_2_unicode_compatible
class CheckGroup(BaseVersionTable):
    GroupDetailItem = collections.namedtuple('GroupDetailItem', ['valid','code','version','id'])
    author = models.ForeignKey(User)
    project = models.CharField(max_length=CONST_CODE_LEN)
    title = models.CharField(max_length=240)
    details = models.TextField(default=json.dumps([]))
    def contains(self, itemcode):
        validlist = self.staticContains(self.details, itemcode)
        listlen = len(validlist)
        if listlen == 1:
            return validlist[0]
        elif listlen < 1:
            return None
        elif listlen > 1:
            logger.error('CheckGroup[%s] contains multiple item[%s]'%(self.strPrefix(), itemcode))
            return validlist[0]
    @staticmethod
    def uniqueDetails(detaillist):
        outdict = collections.OrderedDict()
        for item in detaillist:
            if item.code in outdict:
                if item.version > outdict[item.code].version:
                    outdict[item.code] = item
            else:
                outdict[item.code] = item
        return [x[1] for x in sorted(outdict.items(), key=lambda t:t[0])]
    @staticmethod
    def staticContains(detailstr, itemcode):
        return [x for x in CheckGroup.unpackDetails(detailstr) if x.code == itemcode]
    @staticmethod
    def packDetails(detaillist):
        return json.dumps(CheckGroup.uniqueDetails(detaillist))
    @staticmethod
    def unpackDetails(detailstr):
        return [CheckGroup.GroupDetailItem(*x) for x in json.loads(detailstr)]
    def __str__(self):
        return self.strPrefix()+self.title
    class Meta:
        unique_together = [['code', 'version'],]

@python_2_unicode_compatible
class CheckItem(BaseVersionTable):
    author = models.ForeignKey(User)
    project = models.CharField(max_length=CONST_CODE_LEN, default='')
    title = models.CharField(max_length=240)
    details = models.TextField(default='')
    def __str__(self):
        return self.strPrefix()+self.title
    class Meta:
        unique_together = [['code', 'version'],]

@python_2_unicode_compatible
class CheckListResult(BaseVersionTable):
    author = models.ForeignKey(User)
    subproject = models.CharField(max_length=CONST_CODE_LEN, default='')
    title = models.CharField(max_length=240)
    listcode = models.CharField(max_length=CONST_CODE_LEN)
    listversion = models.PositiveIntegerField()
    groupcount = models.PositiveIntegerField()
    groups     = models.TextField(default=json.dumps([]))
    lockstatus = models.BooleanField(default=False)
    def __str__(self):
        return self.strPrefix()+self.title
    class Meta:
        unique_together = [['code', 'version'],]

@python_2_unicode_compatible
class CheckGroupResult(BaseVersionTable):
    Result = collections.namedtuple('Result', ['code','version','id','status','level'])
    Choice = collections.namedtuple('Choice', ['code','version','id','choice'])
    author = models.ForeignKey(User)
    groupid = models.PositiveIntegerField()
    groupcode = models.CharField(max_length=CONST_CODE_LEN)
    groupversion = models.PositiveIntegerField()
    grouptitle = models.CharField(max_length=240)
    status = models.CharField(max_length=CONST_CODE_LEN)
    summary = models.TextField(default=json.dumps([])) # count of each choice
    choices = models.TextField(default=json.dumps([])) # list of Choice
    buglist = models.TextField(default=json.dumps([])) # list of Result
    def __str__(self):
        return self.strPrefix()+self.status
    class Meta:
        unique_together = [['code', 'version'],]

@python_2_unicode_compatible
class CheckBugItem(BaseVersionTable):
    author = models.ForeignKey(User)
    itemcode = models.CharField(max_length=CONST_CODE_LEN)
    itemversion = models.PositiveIntegerField()
    question = models.TextField()
    answer = models.TextField(default = '')
    status = models.CharField(max_length=CONST_CODE_LEN)
    level = models.CharField(max_length=CONST_CODE_LEN)
    def __str__(self):
        return self.strPrefix()+self.status
    class Meta:
        unique_together = [['code', 'version'],]
