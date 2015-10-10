from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Project)
admin.site.register(SubProject)
admin.site.register(CheckList)
admin.site.register(CheckGroup)
admin.site.register(CheckItem)
admin.site.register(CheckListResult)
admin.site.register(CheckGroupResult)
admin.site.register(CheckBugItem)
admin.site.register(ChartGroup)
