from django import forms
from .models import *

class ProjectForm(forms.Form):
    title   = forms.CharField(max_length=240, widget=forms.TextInput(attrs={'class':'form-control',}))
    status  = forms.ChoiceField(choices=Project.StatusChoice, widget=forms.RadioSelect())
    code    = forms.CharField(max_length=CONST_CODE_LEN, required=False, widget=forms.HiddenInput())
    version = forms.IntegerField(widget=forms.HiddenInput())

