# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib import admin
from django.template.loader import render_to_string
from editregions.contrib.search.text import advanced_options_label

try:
    from django.utils.encoding import force_text
except ImportError:  # < Django 1.5
    from django.utils.encoding import force_unicode as force_text
from haystack.query import SearchQuerySet
from editregions.admin.modeladmins import ChunkAdmin
from editregions.contrib.search.models import MoreLikeThis, SearchResults


class MoreLikeThisAdmin(ChunkAdmin, admin.ModelAdmin):
    list_display = ['max_num', 'connection', 'created', 'modified']
    fieldsets = [
        (None, {
            'fields': ['max_num'],
        }),
        (advanced_options_label, {
            'fields': ['connection', 'request_objects'],
            'classes': ('collapse',),
        }),
    ]

    def render_into_region(self, obj, context):
        sqs = SearchQuerySet().using(obj.connection)
        mlt = sqs.more_like_this(obj.content_object)[0:obj.max_num]
        if obj.request_objects:
            mlt = mlt.load_all()
        context.update(more_like_this=tuple(mlt))
        return render_to_string('editregions/search/mlt.html', context)

    def render_into_summary(self, obj, context):
        if obj.max_num < 1:
            return None
        bits = ['Up to']
        if obj.max_num > 0:
            bits.append(force_text(obj.max_num))
        bits.append('similar items')
        if obj.connection != 'default':
            bits.append('from "{0}"'.format(obj.connection))
        return ' '.join(bits)
admin.site.register(MoreLikeThis, MoreLikeThisAdmin)


class SearchResultsAdmin(ChunkAdmin, admin.ModelAdmin):
    list_display = ['query', 'max_num', 'connection', 'created', 'modified']
    fieldsets = [
        (None, {
            'fields': ['query', 'max_num', 'boost'],
        }),
        (advanced_options_label, {
            'fields': ['connection', 'request_objects'],
            'classes': ('collapse',),
        }),
    ]

    def render_into_region(self, obj, context):
        sqs = SearchQuerySet().using(obj.connection)
        results = sqs.auto_query(obj.query)[0:obj.max_num]

        # and now, in advanced usage, we allow for boosting words in the results
        actual_boosts = obj.get_boosts()
        if actual_boosts:
            for boost_word, boost_value in actual_boosts:
                results = results.boost(boost_word, boost_value)

        # we may want to efficiently load all model instances, if the template
        # requires them.
        if obj.request_objects:
            results = results.load_all()
        context.update(search_results=tuple(results))
        return render_to_string('editregions/search/query_results.html',
                                context)

    def render_into_summary(self, obj, context):
        return force_text(obj)
admin.site.register(SearchResults, SearchResultsAdmin)
