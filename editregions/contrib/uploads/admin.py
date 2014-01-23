# -*- coding: utf-8 -*-
from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.template.loader import render_to_string
from editregions.contrib.uploads.models import File
try:
    from django.utils.encoding import force_text
except ImportError:  # pragma: no cover ... < 1.4?
    from django.utils.encoding import force_unicode as force_text
from editregions.admin.modeladmins import ChunkAdmin


class FileAdmin(ChunkAdmin, ModelAdmin):
    list_display = ['title', 'data', 'created', 'modified']
    fields = [
        'data',
        'title',
    ]

    def render_into_region(self, obj, context):
        templates = []
        # try the extension specific one first ...
        if obj.data:
            templates.append(
                'editregions/uploads/file_{0}.html'.format(obj.get_filetype())
            )
        templates.append('editregions/uploads/file.html')
        return render_to_string(templates, context_instance=context)

    def render_into_summary(self, obj, context):
        if obj.title and obj.data:
            return force_text('{obj.title} ({filename})'.format(
                obj=obj, filename=obj.get_filename()))
        return force_text(obj)
admin.site.register(File, FileAdmin)
