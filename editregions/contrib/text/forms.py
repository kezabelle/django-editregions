# -*- coding: utf-8 -*-
from django.forms import ModelForm
from tinymce.widgets import TinyMCE
from wymeditor.widgets import WYMEditorArea
from editregions.contrib.text.models import WYM, MCE


class WYMEditorForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(WYMEditorForm, self).__init__(*args, **kwargs)
        self.fields['content'].widget = WYMEditorArea()

    class Meta:
        model = WYM
        fields = ['content']


class MCEEditorForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(MCEEditorForm, self).__init__(*args, **kwargs)
        self.fields['content'].widget = TinyMCE()

    class Meta:
        model = MCE
        fields = ['content']
