from django.contrib import admin
from .models import CheckItem

# Register your models here.
class CheckItemAdmin(admin.ModelAdmin):
	fields = ['title', 'update_time', 'relid']

admin.site.register(CheckItem, CheckItemAdmin)
