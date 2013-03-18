# -*- coding: utf-8 -*-
from functools import update_wrapper
from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.contrib.admin.options import BaseModelAdmin, InlineModelAdmin, ModelAdmin
from django.contrib.admin.util import unquote
from django.contrib.contenttypes.generic import GenericInlineModelAdmin
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db.models import BLANK_CHOICE_DASH
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
from editregions.utils.regions import get_enabled_chunks_for_region, validate_region_name, get_pretty_region_name


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
        'position',
        'modified'
    ]
    list_display_links = [
        'region_name',
        'subclass_label',
        'subclass_summary',
    ]
    list_filter = [
        'region',
    ]
    # list_editable = [
    #     'position',
    # ]


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

    def changelist_view(self, request, extra_context=None):
        region_filter = request.GET.get(REQUEST_VAR_REGION, None)
        ct_filter = request.GET.get(REQUEST_VAR_CT, None)
        id_filter = request.GET.get(REQUEST_VAR_ID, None)
        if region_filter is not None:
            extra_context = extra_context or {}
            extra_context['available_chunks'] = [AdminChunkWrapper(**{
                'opts': x._meta,
                'namespace': self.admin_site.app_name,
                'region': region_filter,
                'content_type': ct_filter,
                'content_id': id_filter,
            }) for x in get_enabled_chunks_for_region(region_filter)]
        return super(EditRegionAdmin, self).changelist_view(request, extra_context)


    def get_model_perms(self, request):
        return {
            'add': True,
            'change': True,
            'delete': True,
        }

    # def urls(self):
    #     """Sets up the required urlconf for the admin views."""
    #     from django.conf.urls.defaults import patterns, url
    #
    #     def wrap(view):
    #         def wrapper(*args, **kwargs):
    #             return self.admin_site.admin_view(view)(*args, **kwargs)
    #         return update_wrapper(wrapper, view)
    #     return patterns('',
    #         url(regex=r'^(?P<content_type>.+)/(?P<pk>.+)/(?P<region_name>.+)/$',
    #             view=wrap(self.indexw),
    #             name='%s_%s_change' % (self.model._meta.app_label,
    #                                    self.model._meta.module_name)
    #         ),
    #         url(regex=r'^(?P<content_type>.+)/(?P<pk>.+)/$',
    #             view=wrap(self.index),
    #             name='%s_%s_change' % (self.model._meta.app_label,
    #                                    self.model._meta.module_name)
    #         ),
    #         url(regex=r'^(?P<content_type>.+)/$',
    #             view=wrap(self.index),
    #             name='%s_%s_change' % (self.model._meta.app_label,
    #                                    self.model._meta.module_name)
    #         ),
    #         url(regex=r'^$',
    #             view=self.index,
    #             name='%s_%s_changelist' % (self.model._meta.app_label,
    #                                        self.model._meta.module_name)
    #         ),
    #     )
    # urls = property(urls)
    #
    # def index(self, *a, **kw):
    #     return 1

admin.site.register(EditRegionChunk, EditRegionAdmin)

class EditRegionInline(GenericInlineModelAdmin):
    model = EditRegionChunk
    #form = EditRegionChunkForm
    formset = EditRegionChunkFormSet
    exclude = EditRegionChunkForm._meta.exclude

    can_delete = False
    extra = 0
    ct_field = "content_type"
    ct_fk_field = "content_id"
    template = 'admin/editregions/edit_inline/none.html'
#    template = 'admin/editregions/widgets/chunk_list.html'

    # need to create a formset, one form for each region
    # can probably access data on inline_admin_formset or inline_admin_form

    def get_region_widget(self, obj, region):
        """
        Overridable display of the widget for editing chunks in a region.
        Note that while this is a form Widget, it really just renders a template,
        because the way Django widgets work is really horrid, and no-one should
        have to put up with it.

        .. testcase: TODO
        """
        content_id = obj.pk

        content_type = getattr(obj, self.ct_field)
        return {
            'available_chunks': self.get_enabled_chunks(content_id, content_type, region),
            'region': {
                'name': region,
                'verbose_name': self.get_region_name(region)
            },
            'existing_chunks': self.get_existing_chunks(content_id, content_type, region),
            'page_id': content_id,
            'page_type_id': content_type,
            'blank_choice': BLANK_CHOICE_DASH[0],
            'show_add': True,
            'show_plugins': True,
            }

    def get_enabled_chunks(self, pk, content_type, region):
        """
        .. testcase: TODO
        """
        klass = self.get_admin_wrapper_class()
        return [klass(**{
            'opts': x._meta,
            'namespace': self.admin_site.app_name,
            'region': region,
            'content_type': content_type,
            'content_id': pk,
            }) for x in get_enabled_chunks_for_region(region)]

    def get_region_name(self, region):
        """
        .. testcase: TODO
        """
        validate_region_name(region)
        return get_pretty_region_name(region)

    def get_existing_chunks(self, pk, content_type, region):
        """
        .. testcase: TODO
        """
        klass = self.get_admin_wrapper_class()
        return [klass(**{
            # Using get_for_id to ensure that proxy models etc are handled nicely.
            # Even under Django < 1.5
            'opts': ContentType.objects.get_for_id(x.chunk_content_type_id).model_class()._meta,
            'namespace': self.admin_site.app_name,
            'region': region,
            'content_type': content_type,
            'content_id': pk,
            'obj': x,
            }) for x in get_chunks_for_region(content_id=pk, region=region)]

    def get_admin_wrapper_class(self):
        """
        .. testcase: TODO
        """
        return AdminChunkWrapper
