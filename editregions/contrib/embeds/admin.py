# -*- coding: utf-8 -*-
from urlparse import urlparse
from django.contrib import admin
from django.contrib.admin.options import ModelAdmin
from django.forms import Media
from django.template.loader import render_to_string
from editregions.admin.modeladmins import ChunkAdmin
from editregions.contrib.embeds.forms import JavaScriptEditorForm
from editregions.contrib.embeds.models import Iframe, Feed, JavaScript
from editregions.contrib.embeds.text import (dimensions_fieldset_label,
                                             iframe_details_fieldset_label,
                                             feed_cache_fieldset_label)


class IframeAdmin(ChunkAdmin, ModelAdmin):
    list_display = ['url', 'created', 'modified']
    fieldsets = [
        (iframe_details_fieldset_label, {
            'fields': ['url', 'name'],
        }),
        (dimensions_fieldset_label, {
            'fields': ['width', 'height'],
            'classes': ('collapse',),
        }),
    ]

    def render_into_region(self, obj, context):
        return render_to_string('editregions/embeds/iframe.html', context)

    def render_into_summary(self, obj, context):
        summary = str(obj)
        if len(summary) > 50:
            return '{uri.netloc}'.format(uri=urlparse(summary))
        return summary
admin.site.register(Iframe, IframeAdmin)


class FeedAdmin(ChunkAdmin, ModelAdmin):
    list_display = ['url', 'created', 'modified']
    fieldsets = [
        (None, {
            'fields': ['url']
        }),
        (feed_cache_fieldset_label, {
            'fields': ['cache_for'],
            'classes': ('collapse',),
        }),
    ]

    def save_model(self, request, obj, *args, **kwargs):
        """
        Cache immeidiately if possible.
        """
        super(FeedAdmin, self).save_model(request, obj, *args, **kwargs)
        obj.get_from_cache()

    def render_into_region(self, obj, context):
        context.update({'feed': obj.get_from_cache()})
        return render_to_string('editregions/embeds/feed.html', context)

    def render_into_summary(self, obj, context):
        feed = obj.get_from_cache()
        return feed.feed.title
admin.site.register(Feed, FeedAdmin)


class JavaScriptAdmin(ChunkAdmin, ModelAdmin):
    form = JavaScriptEditorForm
    list_display = ['content', 'created', 'modified']
    fields = [
        'content',
    ]

    def render_into_region(self, obj, context):
        return render_to_string('editregions/embeds/javascript.html', context)

    def render_into_summary(self, obj, context):
        return obj.content

    @property
    def media(self):
        media_instance = super(JavaScriptAdmin, self).media
        return media_instance + Media(css={'screen': [
            'editregions/css/embeds.css'
        ]})


admin.site.register(JavaScript, JavaScriptAdmin)
