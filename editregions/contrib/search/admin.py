# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging
from django.contrib import admin
from django.template.loader import render_to_string
from haystack.exceptions import NotHandled

try:
    from django.utils.encoding import force_text
except ImportError:  # < Django 1.5
    from django.utils.encoding import force_unicode as force_text
from haystack.query import SearchQuerySet
from editregions.admin.modeladmins import ChunkAdmin
from editregions.contrib.search.models import MoreLikeThis, SearchResults
from editregions.contrib.search.forms import MoreLikeThisForm, SearchResultsForm
from editregions.contrib.search.text import advanced_options_label

logger = logging.getLogger(__name__)


class MoreLikeThisAdmin(ChunkAdmin, admin.ModelAdmin):
    form = MoreLikeThisForm
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
        if obj.request_objects:
            sqs = sqs.load_all()
        try:
            mlt = sqs.more_like_this(obj.content_object)[0:obj.max_num]
            context.update({'more_like_this': tuple(mlt)})
        except NotHandled:
            logger.exception("Haystack hasn't been configured to handle this "
                             "object type.")
            context.update({'more_like_this': ()})
        return render_to_string('editregions/search/mlt.html',
                                context_instance=context)

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
    form = SearchResultsForm
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
        results = sqs.auto_query(obj.query)

        # and now, in advanced usage, we allow for boosting words in the results
        actual_boosts = obj.get_boosts()
        if actual_boosts:
            for boost_word, boost_value in actual_boosts:
                results = results.boost(boost_word, boost_value)

        # we may want to efficiently load all model instances, if the template
        # requires them.
        if obj.request_objects:
            results = results.load_all()
        context.update({'search_results': results[0:obj.max_num]})
        return render_to_string('editregions/search/query_results.html',
                                context_instance=context)

    def render_into_summary(self, obj, context):
        return force_text(obj)
admin.site.register(SearchResults, SearchResultsAdmin)
