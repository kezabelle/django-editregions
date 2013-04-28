# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from functools import update_wrapper
import logging
from adminlinks.admin import AdminlinksMixin
from adminlinks.constants import POPUP_QS_VAR
from django.contrib import admin
from django.contrib.admin.options import ModelAdmin
from django.contrib.admin.util import unquote, display_for_field
from django.contrib.contenttypes.generic import GenericInlineModelAdmin
from django.core.exceptions import (ObjectDoesNotExist, PermissionDenied,
                                    ImproperlyConfigured)
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse, HttpResponseBadRequest, QueryDict
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils import simplejson
from django.utils.encoding import force_unicode
from django.utils.html import escape, strip_tags
from django.utils.text import truncate_words
from django.utils.translation import ugettext_lazy as _

from editregions.constants import (REQUEST_VAR_REGION, REQUEST_VAR_CT,
                                   REQUEST_VAR_ID)
from editregions.utils.chunks import get_chunks_for_region
from editregions.utils.data import get_modeladmin, get_content_type
from editregions.utils.rendering import render_one_summary
from editregions.admin.changelist import EditRegionChangeList
from editregions.admin.forms import EditRegionInlineFormSet, MovementForm
from editregions.admin.utils import (AdminChunkWrapper, shared_media,
                                     guard_querystring_m)
from editregions.models import EditRegionChunk
from editregions.utils.regions import (get_enabled_chunks_for_region,
                                       get_pretty_region_name,
                                       scan_template_for_named_regions,
                                       validate_region_name)
from editregions.text import (admin_chunktype_label, admin_summary_label,
                              admin_position_label, admin_modified_label,
                              region_v)

logger = logging.getLogger(__name__)


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
        'get_position',
        'get_region_name',
        'get_subclass_type',
        'get_subclass_summary',
        'get_last_modified',
        # this should always be last, and not be in the list_display_links
        'get_object_tools',
    ]
    list_display_links = [
        'get_region_name',
        'get_subclass_type',
        'get_subclass_summary',
        'get_last_modified',
    ]
    list_filter = [
        'region',
    ]

    def get_region_name(self, obj):
        """
        get the prettified name of this region, if possible.
        :return: the region name
        :rtype: string
        """
        pboj = obj.content_object.get_edit_template_names()[0]
        return get_pretty_region_name(pboj, obj.region)
    get_region_name.short_description = region_v

    def get_subclass_type(self, obj):
        """
        get the verbose name of the given object, which is likely a subclass

        .. note::
            By using this callable, we avoid the problem of being able to
            sort by headers in the changelists (including on the change form)

        :return: the subclass object's verbose name
        :rtype: string
        """
        return obj._meta.verbose_name
    get_subclass_type.short_description = admin_chunktype_label

    def get_subclass_summary(self, obj):
        """
        show a brief, HTML aware summary of the content.

        .. note::
            By using this callable, we avoid the problem of being able to
            sort by headers in the changelists (including on the change form)

        :return: short representation of the data, HTML included.
        :rtype: string
        """
        context = {'admin_summary': True}
        content = strip_tags(render_one_summary(context, obj))
        return truncate_words(content, 20)
    get_subclass_summary.allow_tags = True
    get_subclass_summary.short_description = admin_summary_label

    def get_position(self, obj):
        """
        Show the position of the object when it is rendered on the frontend.

        .. note::
            By using this callable, we avoid the problem of being able to
            sort by headers in the changelists (including on the change form)

        :return: the order this will be shown in.
        :rtype: integer
        """
        return obj.position
    get_position.short_description = admin_position_label

    def get_last_modified(self, obj):
        """
        Show when this was last changed.

        .. note::
            By using this callable, we avoid the problem of being able to
            sort by headers in the changelists (including on the change form)

        :return: the date and time this was last changed, formatted in the
                 standard admin style
        :rtype: string
        """
        fld = obj._meta.get_field_by_name('modified')[0]
        return display_for_field(obj.modified, fld)
    get_last_modified.short_description = admin_modified_label

    def get_object_tools(self, obj):
        """
        Show the modifiers for this object. Currently just implements the
        drag handle as per `django-treeadmin`_.

        :return: the list of actions or tools available for this object
        :rtype: string
        """
        url_to_move = '%(admin)s:%(app)s_%(chunkhandler)s_move' % {
            'admin': self.admin_site.name,
            'app': self.model._meta.app_label,
            'chunkhandler': self.model._meta.module_name,
        }
        url_to_move2 = reverse(url_to_move)
        html = ('<div class="drag_handle" data-pk="%(pk)s" data-href="%(url)s">'
                '</div>' % {
                    'pk': obj.pk,
                    'url': url_to_move2,
                })
        return html
    get_object_tools.allow_tags = True
    get_object_tools.short_description = ''

    # We're finished our list_display fields here.

    def get_custom_urls(self):
        # why this isn't a separate method in Django, I don't know.
        from django.conf.urls import patterns, url

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.module_name
        urlpatterns = patterns('',
                               url(r'^move/$',
                                   wrap(self.move_view),
                                   name='%s_%s_move' % info))
        return urlpatterns + self.get_urls()

    urls = property(get_custom_urls)

    def move_view(self, request):
        """
        Allows us to move a Chunk from one place to another.
        Yes, it accepts request.GET, because I can't be bothered to monkey
        patch the jQuery ajax sending to send a CSRF token. Screw it.

        Data received in the request should be:
            * `pk`
            * `position`
            * `region`

        The form then handles moving everything in .save()
        """
        form = MovementForm(data=request.GET, files=None, initial=None)
        if form.is_valid() and self.has_change_permission(request, form.cleaned_data['pk']):
            form.save()
            html = self.render_changelists_for_object(request, form.cleaned_data['pk'].content_object)
            json_data = {
                'action': 'move',
                'primary_key': form.cleaned_data['pk'].pk,
                'html': html,
            }
            self.log_change(request, *form.change_message())
            self.log_change(request, *form.parent_change_message())
            return HttpResponse(simplejson.dumps(json_data),
                                mimetype='application/json')
        return HttpResponseBadRequest(simplejson.dumps(form.errors),
                                      mimetype='application/json')

    def queryset(self, *args, **kwargs):

        # # try to find the request in the arguments.
        # request = None
        # if len(args) > 0:
        #     request = args[0]
        # elif 'request' in kwargs:
        #     request = kwargs['request']
        #
        # # try to pull the region out of the request
        # region = None
        # if request is not None:
        #     region = request.GET.get(REQUEST_VAR_REGION, None)
        #
        # # try and limit the number of LEFT OUTER JOINs we do using the
        # # inheritance query manager. This is going to be problematic post 1.6
        # # probably, if using grandchildren.
        # filtered_subclasses = ()
        # if region is not None:
        #     available_chunks = get_enabled_chunks_for_region('pages/default.html', region)
        #     filtered_subclasses = (x._meta.module_name
        #                            for x in available_chunks.keys())

        # this is the important part, where we get the real queryset.
        qs = get_chunks_for_region()
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

    def get_changelist(self, *args, **kwargs):
        return EditRegionChangeList

    def change_view(self, request, object_id, form_url='', extra_context=None):

        obj = self.get_object(request, unquote(object_id))
        opts = obj._meta

        if not self.has_change_permission(request, obj):
            raise PermissionDenied

        if obj is None:
            raise Http404(_('%(name)s object with primary key %(key)r does not exist.') % {'name': force_unicode(opts.verbose_name), 'key': escape(object_id)})

        try:
            klass = get_modeladmin(obj, self.admin_site.name)
            return klass.change_view(request, object_id, form_url, extra_context)
        except KeyError:
            raise Http404(_('SOMETHING BAD'))

    def get_changelist_filters(self, request_querydict):
        """
        Get the list of chunks for the changelist sidebar.
        Should only get called with a decent querydict, hopefully.

        :return: list of available chunk types
        """
        region = request_querydict[REQUEST_VAR_REGION]
        ct = request_querydict[REQUEST_VAR_CT]
        pk = request_querydict[REQUEST_VAR_ID]
        try:
            parent_obj = get_content_type(ct).model_class().objects.get(pk=pk)
        except ObjectDoesNotExist as e:
            return HttpResponseBadRequest('something went wrong')

        template_name = parent_obj.get_edit_template_names()[0]
        ChunkWrapper = self.get_admin_wrapper_class()
        filters = (ChunkWrapper(**{
            'opts': x._meta,
            'namespace': self.admin_site.app_name,
            'region': region,
            'content_type': ct,
            'content_id': pk,
        }) for x in get_enabled_chunks_for_region(template_name, region))
        return filters

    def get_admin_wrapper_class(self):
        return AdminChunkWrapper

    @guard_querystring_m
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

    def get_regions_for_object(self, request, obj, **kwargs):
        """
        We only want to get regions once an object has been initially saved, so
        that we can access the appropriate ContentType and Object ID pair.

        If editing an existing object, regions found by scanning a template
        will be returned, and sorted into a unique list in the order they appear
        in the compiled template.
        """
        try:
            templates = obj.get_edit_template_names()
        except AttributeError as e:
            raise ImproperlyConfigured('%(obj)r must have a '
                                       '`get_edit_template_names` method to '
                                       'be used with %(cls)r' % {
                                           'obj': obj.__class__,
                                           'cls': EditRegionInline
                                       })
        return scan_template_for_named_regions(templates)

    def get_changelists_for_object(self, request, obj, **kwargs):
        changelists = []

        # only do all this clever stuff if we're editing
        if obj is not None:
            # from here on out, we heavily reuse the other modeladmin
            # self.model should be EditRegionChunk
            modeladmin = get_modeladmin(self.model, self.admin_site.name)

            # mutate the querystring and set some data onto it, which will
            # be passed to the get_changelist_filters method, as well as
            # being used to filter the ChangeList correctly.
            # new_get = request.GET.copy()
            new_get = QueryDict('', mutable=True)
            new_get[REQUEST_VAR_CT] = get_content_type(obj).pk
            new_get[REQUEST_VAR_ID] = obj.pk

            for region in self.get_regions_for_object(request, obj):
                new_get[REQUEST_VAR_REGION] = region
                request.GET = new_get

                # we don't want the region name displayed here, because we're
                # already displaying it in the template.
                our_list_display = self.list_display[:]
                our_list_links = self.list_display_links[:]
                try:
                    our_list_display.remove('get_region_name')
                    our_list_links.remove('get_region_name')
                except ValueError as e:
                    pass
                ChangeList = self.get_changelist(request, **kwargs)
                cl = ChangeList(request=request, model=self.model,
                                list_display=our_list_display,
                                list_display_links=our_list_links,
                                list_filter=self.list_filter,
                                date_hierarchy=None, search_fields=None,
                                list_select_related=None, list_per_page=100,
                                list_max_show_all=100, list_editable=None,
                                model_admin=self)
                changelists.append(cl)
        return changelists

    def render_changelists_for_object(self, request, obj):
        return render_to_string(EditRegionInline.template, {
            'inline_admin_formset': {
                'formset': {
                    'region_changelists': self.get_changelists_for_object(request,
                                                                          obj)
                },
            },
        })

    @property
    def media(self):
        base_media = super(EditRegionAdmin, self).media
        return base_media + shared_media
admin.site.register(EditRegionChunk, EditRegionAdmin)


class EditRegionInline(GenericInlineModelAdmin):
    model = EditRegionChunk
    can_delete = False
    extra = 0
    max_num = 0
    ct_field = "content_type"
    ct_fk_field = "content_id"
    template = 'admin/editregions/edit_inline/none.html'

    def get_formset(self, request, obj=None, **kwargs):
        # sidestep validation which wants to inherit from BaseModelFormSet
        self.formset = EditRegionInlineFormSet
        formset = super(EditRegionInline, self).get_formset(request, obj, **kwargs)
        # dependency on adminlinks here to see if we're in a popup.
        # if we are, don't show any of these.
        if POPUP_QS_VAR not in request.REQUEST:
            modeladmin = get_modeladmin(EditRegionChunk, self.admin_site.name)
            formset.region_changelists = modeladmin.get_changelists_for_object(request, obj)
        return formset


class ChunkAdmin(AdminlinksMixin):
    actions = None
    actions_on_top = False
    actions_on_bottom = False
    save_as = False
    save_on_top = False
    exclude = ['content_type', 'content_id', 'region', 'position']

    def get_model_perms(self, request, *args, **kwargs):
        """
        Shadow method for the default ModelAdmin. Allows us to hide chunks.
        By using an empty dictionary, permissions still work, but chunk administration
        views are hidden from the default AdminSite index.

        :param request: The WSGIRequest.
        :return: Empty dictionary
        """
        return {}

    def save_model(self, request, obj, form, change):
        """
        Adds extra fields to the object so it's saved against the correct
        content type etc.
        """
        validate_region_name(request.GET.get('region'))
        obj.content_type = get_content_type(request.GET.get('content_type'))
        obj.content_id = int(request.GET.get('content_id'))
        obj.region = str(request.GET.get('region'))
        #obj.subcontent_type = self.get_chunk_renderer_content_type()

        # If the position is not set,
        # it's easiest to assume it's going on the end of the chunk list.
        if obj.position is None:
            new_position = get_last_chunk_position(content_id=obj.content_id,
                                                   content_type=obj.content_type, region_name=obj.region)
            obj.position = new_position + 1
        super(ChunkAdmin, self).save_model(request, obj, form, change)

    def response_max(self, request, limit, found):
        """
        If a chunk limit has been reached,
        adding a new one via `add_view` will instead return this view.
        """
        possible_templates = [
            'admin/editregions/limit_reached.html'
        ]
        context = {
            'is_popup': POPUP_QS_VAR in request.REQUEST,
            'found': found,
            'limit': limit,
        }
        return render_to_response(possible_templates, context,
                                  context_instance=RequestContext(request))

    @guard_querystring_m
    def add_view(self, request, *args, **kwargs):
        """
        At this point, our querystring should be 'safe', and we can discover
        if we need to stop early because of a chunk limit being reached.

        """
        available_chunks = get_enabled_chunks_for_region(str(request.GET.get('region')))
        limit = available_chunks[self.model]
        # if there's a limit (no infinity set) ensure we haven't it it yet.
        if limit is not None:
            already_created = self.model.objects.filter(**self._guarded).count()
            if already_created >= limit:
                return self.response_max(request, limit, already_created)
        return super(ChunkAdmin, self).add_view(request, *args, **kwargs)

    @guard_querystring_m
    def change_view(self, request, *args, **kwargs):
        """
        This override only exists because I have no idea how to forceably guard
        the super() change_view without doing so.
        """
        return super(ChunkAdmin, self).change_view(request, *args, **kwargs)

    @guard_querystring_m
    def delete_view(self, request, *args, **kwargs):
        """
        This override only exists because I have no idea how to forceably guard
        the super() change_view without doing so.
        """
        return super(ChunkAdmin, self).delete_view(request, *args, **kwargs)

    def get_success_templates(self, request):
        """Override the AdminlinksMixin equivalent, to provide per-model template lookups.

        Forces the attempted loading of the following:
            - a template for this model.
            - a template for this app.
            - a template for any parent model.
            - a template for any parent app.
            - a guaranteed to exist template (the editregions success file)

        :param request: The WSGIRequest
        :return: list of strings representing templates to look for.
        """
        app_label = self.model._meta.app_label
        model_name = self.model._meta.object_name.lower()
        any_parents = self.model._meta.parents.keys()
        templates = [
            "admin/editregions/%s/%s/success.html" % (app_label, model_name),
            "admin/editregions/%s/success.html" % app_label,
        ]
        for parent in any_parents:
            app_label = parent._meta.app_label
            model_name = parent._meta.object_name.lower()
            templates.extend([
                "admin/editregions/%s/%s/success.html" % (app_label, model_name),
                "admin/editregions/%s/success.html" % app_label,
            ])
        templates.extend(['admin/editregions/success.html'])
        templates.extend(super(ChunkAdmin, self).get_success_templates(request))
        return templates

    def get_response_extra_context(self, request, obj, action):
        """
        This method allows us to add custom data to any success template displayed
        because we're in our admin popup.
        """
        modeladmin = get_modeladmin(EditRegionChunk, self.admin_site.name)
        json_data = {
            'action': action,
            'primary_key': obj.pk,
            'html': modeladmin.render_changelists_for_object(request, obj)
        }
        return simplejson.dumps(json_data)

    def get_response_add_context(self, request, obj):
        return self.get_response_extra_context(request, obj, 'add')

    def get_response_add_context(self, request, obj):
        return self.get_response_extra_context(request, obj, 'change')

    def get_response_delete_context(self, request, obj_id):

        # we have to use a fake object to simulate the original, as it no longer
        # can be guaranteed to exist. We expose only the very specific values we
        # need for get_response_extra_context to work.
        class FakeObj(object):
            def __init__(self, obj_id):
                self.pk = obj_id
                self.id = obj_id

        fake_obj = FakeObj(obj_id)
        return self.get_response_extra_context(request, fake_obj, 'delete')
