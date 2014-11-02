# -*- coding: utf-8 -*-
from functools import update_wrapper
from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.core.exceptions import ValidationError, PermissionDenied
from django.http import HttpResponse
from django.template.defaultfilters import striptags
from django.template.loader import render_to_string
from editregions.admin.modeladmins import ChunkAdmin
from editregions.contrib.textfiles.utils import valid_md_file
from .models import Markdown
from .forms import MarkdownSelectionForm


class MarkdownAdmin(ChunkAdmin, ModelAdmin):
    form = MarkdownSelectionForm
    list_display = ['filepath', 'created', 'modified']
    add_form_template = 'admin/editregions/markdown/change_form.html'
    change_form_template = 'admin/editregions/markdown/change_form.html'

    def render_into_region(self, obj, context, **kwargs):
        return render_to_string('editregions/textfiles/markdown.html',
                                context_instance=context)

    def render_into_summary(self, obj, context, **kwargs):
        data = striptags(obj.rendered_content).strip()
        if data:
            return data
        return '[missing content]'

    def get_urls(self):
        default_urls = super(MarkdownAdmin, self).get_urls()
        from django.conf.urls import patterns, url

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.model_name

        urlpatterns = patterns('',
            url(r'^preview/(.+)$', wrap(self.preview), name='%s_%s_preview' % info),
        )
        return urlpatterns + default_urls

    def preview(self, request, target_file, extra_context=None):
        if not self.has_add_permission(request):
            raise PermissionDenied("Need add permission")
        try:
            valid_md_file(target_file)
        except ValidationError:
            raise PermissionDenied("Invalid file")
        fake_obj = self.model(filepath=target_file)
        return HttpResponse(fake_obj.rendered_content)
admin.site.register(Markdown, MarkdownAdmin)
