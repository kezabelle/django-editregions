# -*- coding: utf-8 -*-
from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.forms import Media
from django.template.defaultfilters import striptags
from django.template.loader import render_to_string
from editregions.admin.modeladmins import ChunkAdmin
from editregions.contrib.text.forms import WYMEditorForm, MCEEditorForm
from editregions.contrib.text.models import WYM, MCE


class WYMAdmin(ChunkAdmin, ModelAdmin):
    form = WYMEditorForm
    list_display = ['content', 'created', 'modified']
    fields = [
        'content',
    ]

    def render_into_region(self, obj, context):
        return render_to_string('editregions/text/html.html', context)

    def render_into_summary(self, obj, context):
        return striptags(obj.content)
admin.site.register(WYM, WYMAdmin)


class MCEAdmin(ChunkAdmin, ModelAdmin):
    form = MCEEditorForm
    list_display = ['content', 'created', 'modified']
    fields = [
        'content',
    ]

    def render_into_region(self, obj, context):
        return render_to_string('editregions/text/html.html', context)

    def render_into_summary(self, obj, context):
        return striptags(obj.content)

    @property
    def media(self):
        media_instance = super(MCEAdmin, self).media
        return media_instance + Media(css={'screen': [
            'editregions/css/text.css'
        ]})

admin.site.register(MCE, MCEAdmin)
