# -*- coding: utf-8 -*-
from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.template.defaultfilters import striptags
from django.template.loader import render_to_string
from editregions.admin.modeladmins import ChunkAdmin
from .models import MetaElement
from .forms import MetaElementForm


class MetaElementAdmin(ChunkAdmin, ModelAdmin):
    form = MetaElementForm
    list_display = ['name', 'content', 'created', 'modified']

    def render_into_region(self, obj, context, **kwargs):
        return render_to_string('editregions/html/metatag.html',
                                context_instance=context)

    def render_into_summary(self, obj, context, **kwargs):
        return striptags(obj.content).strip()

    def render_editregions_subclass_type(self, obj, context, **kwargs):
        return obj._meta.verbose_name
admin.site.register(MetaElement, MetaElementAdmin)
