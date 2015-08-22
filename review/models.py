from django.db import models
from django.db.models import Max
from django.contrib.auth.models import User
from django.utils.encoding import python_2_unicode_compatible

# Create your models here.
class BaseVersionTable(models.Model):
	code        = models.CharField(max_length=20)
	version     = models.PositiveIntegerField(default=1)
	update_time = models.DateTimeField(auto_now_add=True)
	def splitCode(self):
		idx = self.code.index('#')
		return self.code[0:idx], self.code[idx+1:]
	def setCode(self,category,no):
		self.code = '%s#%d'%(category,no)
	def strPrefix(self):
		return '[%d][%s][%d]'%(self.id,self.code,self.version)
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
		#unique_together = [['code', 'version'],]

@python_2_unicode_compatible
class CheckItem(BaseVersionTable):
	author = models.ForeignKey(User)
	title = models.CharField(max_length=240)
	details = models.TextField(default='')
	def __str__(self):
		return self.strPrefix()+self.title
	class Meta:
		unique_together = [['code', 'version'],]

