# -*- coding: utf-8 -*-
from django.forms import ModelForm
from editregions.contrib.htmlmeta.models import MetaElement


class MetaElementForm(ModelForm):

    class Meta:
        model = MetaElement
        fields = ['name', 'content']
