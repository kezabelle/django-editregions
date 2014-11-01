# -*- coding: utf-8 -*-
from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.template.defaultfilters import striptags
from django.template.loader import render_to_string
from editregions.admin.modeladmins import ChunkAdmin
from .models import Markdown
from .forms import MarkdownSelectionForm


class MarkdownAdmin(ChunkAdmin, ModelAdmin):
    form = MarkdownSelectionForm
    list_display = ['filepath', 'created', 'modified']
    fields = [
        'filepath',
    ]

    def render_into_region(self, obj, context, **kwargs):
        return render_to_string('editregions/textfiles/markdown.html',
                                context_instance=context)

    def render_into_summary(self, obj, context, **kwargs):
        return striptags(obj.rendered_content).strip()
admin.site.register(Markdown, MarkdownAdmin)
