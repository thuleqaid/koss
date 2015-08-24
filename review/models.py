import json
import collections
import logging
from django.db import models
from django.db.models import Max
from django.contrib.auth.models import User
from django.utils.encoding import python_2_unicode_compatible

logger = logging.getLogger('review')
# Create your models here.
CONST_CODE_LEN = 63
class BaseVersionTable(models.Model):
    code        = models.CharField(max_length=CONST_CODE_LEN)
    version     = models.PositiveIntegerField(default=1)
    update_time = models.DateTimeField(auto_now_add=True)
    def splitCode(self):
        idx = self.code.index('#')
        return self.code[0:idx], int(self.code[idx+1:])
    def setCode(self,category,no):
        self.code = '%s#%08d'%(category,no)
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
        codes = cls.objects.filter(code__startswith='%s#'%(category,)).order_by('-code')[:1]
        if len(codes) > 0:
            code1, code2 = codes[0].splitCode()
            code2 += 1
        else:
            code2 = 1
        return code2
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
    #author = models.ForeignKey(User)
    DefaultCategory = 'PRJ'
    StatusOpen   = 'OP'
    StatusClosed = 'ED'
    StatusChoice = ((StatusOpen, 'Open'), (StatusClosed, 'Closed'),)
    title = models.CharField(max_length=240)
    status = models.CharField(max_length=2, choices=StatusChoice, default=StatusOpen)
    def __str__(self):
        return self.strPrefix()+self.title
    class Meta:
        unique_together = [['code', 'version'],]

@python_2_unicode_compatible
class CheckGroup(BaseVersionTable):
    GroupDetailItem = collections.namedtuple('GroupDetailItem', ['valid','code','version'])
    #author = models.ForeignKey(User)
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
    def staticContains(detailstr, itemcode):
        return [x for x in unpackDetails(detailstr) if x.code == itemcode]
    @staticmethod
    def packDetails(detaillist):
        return json.dumps(detaillist)
    @staticmethod
    def unpackDetails(detailstr):
        return [GroupDetailItem(*x) for x in json.loads(detailstr)]
    def __str__(self):
        return self.strPrefix()+self.title
    class Meta:
        unique_together = [['code', 'version'],]

@python_2_unicode_compatible
class CheckItem(BaseVersionTable):
    ScopeGlobal= 'G'
    ScopeLocal = 'L'
    ScopeChoice = ((ScopeGlobal, 'Global'), (ScopeLocal, 'Local'),)
    #author = models.ForeignKey(User)
    title = models.CharField(max_length=240)
    details = models.TextField(default='')
    scope = models.CharField(max_length=1, choices=ScopeChoice, default=ScopeGlobal)
    def __str__(self):
        return self.strPrefix()+self.title
    class Meta:
        unique_together = [['code', 'version'],]

