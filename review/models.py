from django.db import models
from django.db.models import F
from django.utils import timezone
from django.contrib.auth.models import User
from django.utils.encoding import python_2_unicode_compatible

# Create your models here.
class HistoryTable(models.Model):
	update_time = models.DateTimeField()
	relid = models.PositiveIntegerField(null=True)
	def history_save(self):
		ret = False
		if self.id:
			# make an modification to an existing record
			if self.id == self.relid:
				# current record is the first and the only record for a serial of history
				self.id = None
				self.update_time = timezone.now()
				self.save()
				oobj = self.__class__.objects.get(pk=self.relid)
				oobj.relid = self.id
				oobj.save()
				ret = True
			else:
				# current record is not the first record in the serial of history
				oobj = self.__class__.objects.get(pk=self.relid)
				if oobj.relid != self.id:
					# current record is not the latest record
					ret = False
				else:
					self.id = None
					self.update_time = timezone.now()
					self.save()
					oobj.relid = self.id
					oobj.save()
					ret = True
		else:
			# a new record
			self.update_time = timezone.now()
			self.save()
			self.relid = self.id
			self.save()
			ret = True
		return ret
	@classmethod
	def oldest(cls):
		return cls.objects.filter(pk__lte=F('relid'))
	@classmethod
	def latest(cls):
		latestid = [x.relid for x in cls.oldest()]
		return cls.objects.filter(pk__in=latestid)
	class Meta:
		abstract = True

@python_2_unicode_compatible
class CheckItem(HistoryTable):
	author = models.ForeignKey(User)
	title = models.CharField(max_length=240)
	valid = models.BooleanField(default=True)
	def __str__(self):
		return str(self.id) + ": " + self.title

@python_2_unicode_compatible
class CheckItemDetail(HistoryTable):
	author  = models.ForeignKey(User)
	item    = models.ForeignKey(CheckItem)
	details = models.TextField()
	def __str__(self):
		return str(self.id) + ":" + str(self.item.id)

@python_2_unicode_compatible
class CheckGroup(HistoryTable):
	author = models.ForeignKey(User)
	title  = models.CharField(max_length = 240)
	valid  = models.BooleanField(default = True)
	def __str__(self):
		return str(self.id) + ": " + self.title

@python_2_unicode_compatible
class CheckGroupDetail(HistoryTable):
	author = models.ForeignKey(User)
	group  = models.ForeignKey(CheckGroup)
	item   = models.ForeignKey(CheckItem)
	def __str__(self):
		return str(self.id) + ": " + self.title
