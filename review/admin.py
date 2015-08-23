from django.contrib import admin
from .models import *

# Register your models here.
class CheckItemAdmin(admin.ModelAdmin):
	fields = ['title', 'code', 'version', 'update_time']

admin.site.register(Project)
admin.site.register(CheckItem, CheckItemAdmin)
