# -*- coding: utf-8 -*-
from functools import update_wrapper
from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.contrib.admin.options import BaseModelAdmin, InlineModelAdmin, ModelAdmin
from django.contrib.admin.util import unquote
from django.contrib.contenttypes.generic import GenericInlineModelAdmin
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied, ImproperlyConfigured
from django.db.models import BLANK_CHOICE_DASH
from django.forms import Media
from django.http import Http404
from django.utils.encoding import force_unicode
from django.utils.html import escape
from django.utils.text import truncate_words
from django.utils.translation import ugettext_lazy as _
from editregions.constants import REQUEST_VAR_REGION, REQUEST_VAR_CT, REQUEST_VAR_ID
from editregions.text import render_label
from editregions.utils.rendering import render_one_summary
from editregions.admin.forms import EditRegionChunkForm, EditRegionChunkFormSet
from editregions.admin.utils import AdminChunkWrapper
from editregions.admin.widgets import ChunkList
from editregions.models import EditRegionChunk
from editregions.utils.chunks import get_chunks_for_region
from editregions.utils.regions import (get_enabled_chunks_for_region,
                                       validate_region_name, sorted_regions,
                                       get_pretty_region_name,
                                       scan_template_for_named_regions)


class EditRegionAdmin(ModelAdmin):
    frontend_editing = True
    fields = None
    fieldsets = None
    exclude = None
    date_hierarchy = None
    ordering = None
    list_select_related = False
    save_as = False
    save_on_top = False
    actions = None

    list_display = [
        'region_name',
        'subclass_label',
        'subclass_summary',
        'subclass_position',
        'subclass_modified'
    ]
    list_display_links = [
        'region_name',
        'subclass_label',
        'subclass_summary',
    ]
    list_filter = [
        'region',
    ]

    # The following methods, all prefixed with `subclass_` all have to be on
    # this object

    def subclass_label(self, obj):
        return obj._meta.verbose_name
    # TODO: export to .text
    subclass_label.short_description = 'Type'

    def subclass_summary(self, obj):
        context = {
            'admin_summary': True,
            }
        return truncate_words(render_one_summary(context, obj), 20)
    subclass_summary.allow_tags = True
    # TODO: export to .text
    subclass_summary.short_description = 'Summary'

    def subclass_position(self, obj):
        return obj.position
    # TODO: export to .text
    subclass_position.short_description = '#'

    def subclass_modified(self, obj):
        return obj.modified
    # TODO: export to .text
    subclass_modified.short_description = 'last changed'

    # We're finished our list_display fields here.


    def queryset(self, *args, **kwargs):
        qs = self.model.polymorphs.select_subclasses()
        ordering = self.get_ordering(*args, **kwargs)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs

    def get_object(self, request, object_id):
        queryset = self.queryset(request)
        try:
            return queryset.get(pk=object_id)
        except ObjectDoesNotExist:
            return None

    def change_view(self, request, object_id, form_url='', extra_context=None):

        obj = self.get_object(request, unquote(object_id))
        opts = obj._meta

        if not self.has_change_permission(request, obj):
            raise PermissionDenied

        if obj is None:
            raise Http404(_('%(name)s object with primary key %(key)r does not exist.') % {'name': force_unicode(opts.verbose_name), 'key': escape(object_id)})

        try:
            klass = self.admin_site._registry[obj.__class__]
            return klass.change_view(request, object_id, form_url, extra_context)
        except KeyError:
            raise Http404(_('SOMETHING BAD'))

    def get_changelist_filters(self, request_querydict):
        """
        Get the list of chunks for the changelist sidebar.

        :return: list of available chunk types
        """
        region_filter = request_querydict.get(REQUEST_VAR_REGION, None)
        ct_filter = request_querydict.get(REQUEST_VAR_CT, None)
        id_filter = request_querydict.get(REQUEST_VAR_ID, None)
        filters = []
        if region_filter is not None:
            filters = [AdminChunkWrapper(**{
                'opts': x._meta,
                'namespace': self.admin_site.app_name,
                'region': region_filter,
                'content_type': ct_filter,
                'content_id': id_filter,
            }) for x in get_enabled_chunks_for_region(region_filter)]
        return filters

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['available_chunks'] = self.get_changelist_filters(request.GET)
        return super(EditRegionAdmin, self).changelist_view(request, extra_context)


    def get_model_perms(self, request):
        return {
            'add': True,
            'change': True,
            'delete': True,
        }
admin.site.register(EditRegionChunk, EditRegionAdmin)

class FakedForm(object):
    # TODO: move this somewhere else
    media = Media()


class FakedFormSet(object):
    # TODO: move this somewhere else
    initial_forms = []
    extra_forms = []
    media = Media(css={
        'screen': [
            'admin/css/editregions.css',
        ]
    })
    empty_form = FakedForm()

    @classmethod
    def get_default_prefix(cls):
        return 'edit_region_chunk_formset'

    def __init__(self, instance, prefix, queryset):
        self.instance = instance
        self.prefix = prefix
        self.queryset = queryset


    def get_queryset(self, *args, **kwargs):
        return self.queryset


class EditRegionInline(GenericInlineModelAdmin):
    model = EditRegionChunk
    exclude = EditRegionChunkForm._meta.exclude

    can_delete = False
    extra = 0
    ct_field = "content_type"
    ct_fk_field = "content_id"
    template = 'admin/editregions/edit_inline/none.html'

    # only methods to use are get_formset and get_fieldsets

    def get_formset(self, request, obj=None, **kwargs):
        # sidestep validation which wants to inherit from BaseModelFormSet
        self.formset = FakedFormSet
        changelists = []

        # only do all this clever stuff if we're editing
        if obj is not None:
            # from here on out, we heavily reuse the other modeladmin
            klass = ContentType.objects.get_for_model(self.model).model_class()
            modeladmin = self.admin_site._registry[klass]

            # mutate the querystring and set some data onto it, which will
            # be passed to the get_changelist_filters method, as well as
            # being used to filter the ChangeList correctly.
            new_get = request.GET.copy()
            new_get[REQUEST_VAR_CT] = ContentType.objects.get_for_model(obj).pk
            new_get[REQUEST_VAR_ID] = obj.pk

            for region in self.get_regions(request, obj):
                new_get[REQUEST_VAR_REGION] = region
                ChangeList = modeladmin.get_changelist(request, **kwargs)
                request.GET = new_get
                cl = ChangeList(request=request, model=self.model,
                                list_display=modeladmin.list_display,
                                list_display_links=modeladmin.list_display_links,
                                list_filter=modeladmin.list_filter,
                                date_hierarchy=None, search_fields=None,
                                list_select_related=None, list_per_page=100,
                                list_max_show_all=100, list_editable=None,
                                model_admin=modeladmin)

                cl.available_chunks = modeladmin.get_changelist_filters(new_get)
                # mirror what the changelist_view does.
                cl.formset = None
                changelists.append(cl)
        formset = super(EditRegionInline, self).get_formset(request, obj, **kwargs)
        formset.region_changelists = changelists
        return formset

    def get_regions(self, request, obj=None):
        """
        We only want to get regions once an object has been initially saved, so
        that we can access the appropriate ContentType and Object ID pair.

        If editing an existing object, regions found by scanning a template
        will be returned, and sorted into a unique list in the order they appear
        in the compiled template.
        """
        if obj is None:
            return []
        try:
            templates = obj.get_edit_template_names()
        except AttributeError as e:
            raise ImproperlyConfigured(u'%(obj)r must have a `get_template` '
                                       u'method to be used with %(cls)r' % {
                                        'obj': obj.__class__,
                                        'cls': EditRegionInline
                                       })
        regions = scan_template_for_named_regions(templates)
        return sorted_regions(regions)
