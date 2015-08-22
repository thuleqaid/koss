from django.contrib import admin
from .models import CheckItem

# Register your models here.
class CheckItemAdmin(admin.ModelAdmin):
	fields = ['title', 'code', 'version', 'update_time']

admin.site.register(CheckItem, CheckItemAdmin)
