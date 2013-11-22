# -*- coding: utf-8 -*-
from django.forms import ModelForm
from django_ace import AceWidget


class JavaScriptEditorForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(JavaScriptEditorForm, self).__init__(*args, **kwargs)
        self.fields['content'].widget = AceWidget(mode='javascript',
                                                  theme='chrome')
