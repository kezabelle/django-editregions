# -*- coding: utf-8 -*-
from urlparse import urlparse
from django.contrib import admin
from django.contrib.admin.options import ModelAdmin
from django.template.loader import render_to_string
from django.template.loader_tags import ConstantIncludeNode
from editregions.admin.modeladmins import ChunkAdmin
from editregions.contrib.embeds.models import Iframe, Feed
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

    def render_into_region(self, obj, context):
        context.update({'feed': obj.get_from_cache()})
        return render_to_string('editregions/embeds/feed.html', context)

    def render_into_summary(self, obj, context):
        feed = obj.get_from_cache()
        return feed.feed.title

admin.site.register(Feed, FeedAdmin)
