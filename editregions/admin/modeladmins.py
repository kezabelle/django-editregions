# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from functools import update_wrapper
import logging
from django.conf import settings

try:
    from django.utils.six.moves import urllib_parse
    urlsplit = urllib_parse.urlsplit
    urlunsplit = urllib_parse.urlunsplit
except (ImportError, AttributeError) as e:  # Python 2, < Django 1.5
    from urlparse import urlsplit, urlunsplit
import warnings
from django.forms import Media
from django.template.response import TemplateResponse
from adminlinks.admin import AdminlinksMixin
from django.contrib.admin.options import ModelAdmin
try:
    from django.contrib.admin.utils import display_for_field, unquote
except ImportError:
    from django.contrib.admin.util import display_for_field, unquote
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse, resolve
from django.http import HttpResponse, HttpResponseBadRequest, QueryDict
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.loader import render_to_string
from editregions.utils.db import get_chunks_in_region_count

try:
    import json
except ImportError:  # pragma: no cover ... some older Python2 version.
    from django.utils import simplejson as json
try:
    from django.utils.encoding import force_text
except ImportError:  # pragma: no cover ... < Django 1.5
    from django.utils.encoding import force_unicode as force_text
from django.utils.translation import ugettext_lazy as _
from adminlinks.templatetags.utils import _add_link_to_context
from editregions.admin.inlines import EditRegionInline
from editregions.constants import (REQUEST_VAR_REGION, REQUEST_VAR_CT,
                                   REQUEST_VAR_ID)
from editregions.utils.data import (get_modeladmin, get_content_type,
                                    get_model_class)
from editregions.templatetags.editregion import EditRegionTag
from editregions.admin.changelist import EditRegionChangeList
from editregions.admin.forms import MovementForm
from editregions.admin.utils import (AdminChunkWrapper, shared_media,
                                     guard_querystring_m)
from editregions.models import EditRegionChunk, EditRegionConfiguration
from editregions.text import (admin_chunktype_label, admin_summary_label,
                              admin_position_label, admin_modified_label,
                              region_v)

try:
    from django.utils.text import Truncator
    def truncate_words(s, num):
        return Truncator(s).words(num, truncate='...')
except ImportError as e:  # pragma: no cover
    from django.utils.text import truncate_words

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
    change_list_template = 'admin/editregions/change_list.html'

    list_display = [
        'get_position',
        # 'get_region_name',
        'get_subclass_type',
        'get_subclass_summary',
        'get_last_modified',
        # this should always be last, and not be in the list_display_links
        'get_object_tools',
    ]
    list_display_links = ()
    list_filter = [
        'region',
    ]

    def __init__(self, *args, **kwargs):
        super(EditRegionAdmin, self).__init__(*args, **kwargs)
        # disables the built in link building using
        # EditRegionChangeList.url_for_result so that we can have useful
        # links that we can customise.
        self.list_display_links = self.get_list_display_links(
            request=None, list_display=self.list_display,
        )

    def get_list_display_links(self, request, list_display):
        """
        Disable the built in link building so we can have customised links
        in the changelist.
        """
        return (None,)

    def get_list_display(self, request):
        """
        A copy of the standard one, hard-copying the fields ...
        """
        return self.list_display[:]

    def get_changelist_link_html(self, obj, **kwargs):
        AdminChunkWrapper = self.get_admin_wrapper_class()
        wrapped_obj = AdminChunkWrapper(opts=obj._meta, obj=obj,
                                        namespace=self.admin_site.name,
                                        content_id=obj.content_id,
                                        content_type=obj.content_type,
                                        region=obj.region)
        return ('<a href="{url}" data-adminlinks="autoclose" data-no-turbolink>'
                '{data}</a>').format(url=wrapped_obj.get_absolute_url(), **kwargs)

    def get_region_name(self, obj):
        """
        get the prettified name of this region, if possible.
        :return: the region name
        :rtype: string
        """
        erc = EditRegionConfiguration(obj.content_object)
        region_name = erc.config[obj.region]['name']
        return self.get_changelist_link_html(obj, data=region_name)
    get_region_name.allow_tags = True
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
        return self.get_changelist_link_html(obj, data=obj._meta.verbose_name)
    get_subclass_type.allow_tags = True
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
        iterdata = EditRegionTag.chunk_iteration_context(
            index=0, value=obj, iterable=(obj,))['chunkloop']
        content = EditRegionTag.render_one_summary(context, obj, extra=iterdata)
        return self.get_changelist_link_html(obj, data=truncate_words(content,
                                                                      20))
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
        return self.get_changelist_link_html(obj, data=obj.position)
    get_position.allow_tags = True
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
        if hasattr(self.model._meta, 'model_name'):
            model_name = self.model._meta.model_name
        else:
            model_name = self.model._meta.module_name
        url_to_move = '%(admin)s:%(app)s_%(chunkhandler)s_move' % {
            'admin': self.admin_site.name,
            'app': self.model._meta.app_label,
            'chunkhandler': model_name,
        }
        url_to_move2 = reverse(url_to_move)
        AdminChunkWrapper = self.get_admin_wrapper_class()
        delete_url = AdminChunkWrapper(opts=obj._meta,
                                       namespace=self.admin_site.name,
                                       obj=obj).get_delete_url()
        html = ('<div class="drag_handle" data-pk="%(pk)s" data-href="%(url)s">'
                '</div>&nbsp;<a class="delete_handle" href="%(delete_url)s" '
                'data-adminlinks="autoclose" data-no-turbolink>'
                '%(delete)s</a>' % {
                    'pk': obj.pk,
                    'url': url_to_move2,
                    'delete_url': delete_url,
                    'delete': _('Delete'),
                })
        return html
    get_object_tools.allow_tags = True
    get_object_tools.short_description = ''

    # We're finished our list_display fields here.

    def get_model_perms(self, request, *args, **kwargs):
        """
        Shadow method for the default ModelAdmin. Allows us to hide stufff.
        By using an empty dictionary, permissions still work, but chunk administration
        views are hidden from the default AdminSite index.

        :param request: The WSGIRequest.
        :return: Empty dictionary
        """
        return {}

    def get_urls(self):
        # why this isn't a separate method in Django, I don't know.
        from django.conf.urls import patterns, url

        def wrap(view):  # pragma: no cover this is from the Django admin
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            return update_wrapper(wrapper, view)

        app_label = self.model._meta.app_label
        if hasattr(self.model._meta, 'model_name'):
            model_name = self.model._meta.model_name
        else:
            model_name = self.model._meta.module_name
        info = (app_label, model_name)
        urlpatterns = patterns('',
                               # parent_ct is the Django ContentType PK for
                               # the object the EditRegionChunks are bound to
                               # eg: a page, a blog post, a project.
                               # parent_id is the PK of the parent object in
                               # question. We don't know what format the PK takes
                               # so we accept anything.
                               #url(r'^(?P<parent_ct>\d+)/(?P<parent_id>.+)/$',
                               url(r'^$',
                                   wrap(self.changelist_view),
                                   name='%s_%s_changelist' % info),
                               # moving an object from one position to another
                               # potentially across regions.
                               url(r'^move/$',
                                   wrap(self.move_view),
                                   name='%s_%s_move' % info),
                               # this thing is needed, unfortunately, to enable
                               # the delete screen to work on EditRegionChunk
                               # subclasses.
                               # see https://code.djangoproject.com/ticket/20640
                               # As I'm not thrilled with the idea of finding
                               # the wrong edit screen ... we're going to
                               # re-point it at the history view.
                               url(r'^(.+)/$',
                                   wrap(self.history_view),
                                   name='%s_%s_change' % info),
                               )

        return urlpatterns
    urls = property(get_urls)

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
            html = self.render_changelists_for_object(
                request=request, obj=form.cleaned_data['pk'].content_object)
            json_data = {
                'action': 'move', 'html': html,
                'primary_key': form.cleaned_data['pk'].pk,
            }
            self.log_change(request, *form.change_message())
            self.log_change(request, *form.parent_change_message())
            return HttpResponse(json.dumps(json_data),
                                content_type='application/json')
        return HttpResponseBadRequest(json.dumps(form.errors),
                                      content_type='application/json')

    def get_queryset(self, *args, **kwargs):
        """
        Don't use the default queryset/manager, as it won't be our interface
        to polymorphic (downcast) EditRegionChunk subclasses.

        :param args: Stuff to pass through to
               :meth:`~django.contrib.admin.options.BaseModelAdmin.get_ordering`
        :param kwargs: Stuff to pass through to
               :meth:`~django.contrib.admin.options.BaseModelAdmin.get_ordering`
        :return: our EditRegionChunks, but already downcast to their final form.
        :rtype: :class:`~django.db.models.query.QuerySet`
        """
        qs = self.model.polymorphs.all().select_subclasses()
        ordering = self.get_ordering(*args, **kwargs)
        if ordering:  # pragma: no cover ... I don't care, this should be fine.
            qs = qs.order_by(*ordering)
        return qs

    queryset = get_queryset

    def get_object(self, request, object_id):
        """
        This overrides the default, to catch ObjectDoesNotExist, because we
        can't guarantee what model is being referenced, as it's polymorphic.
        """
        queryset = self.queryset(request)
        try:
            return queryset.get(pk=object_id)
        except ObjectDoesNotExist:
            return None

    def get_changelist(self, *args, **kwargs):
        return EditRegionChangeList

    def get_admin_wrapper_class(self):
        return AdminChunkWrapper

    def changelist_view(self, request, extra_context=None):
        parent_ct = request.GET[REQUEST_VAR_CT]
        parent_id = request.GET[REQUEST_VAR_ID]
        obj = get_model_class(parent_ct).objects.get(pk=parent_id)
        extra_context = extra_context or {}
        context = self.changelists_as_context_data(request, obj)
        opts = self.model._meta
        app_label = opts.app_label
        context.update({
            'module_name': force_text(opts.verbose_name_plural),
            'title': _('Select %s to change') % force_text(opts.verbose_name),
            'media': self.media,
            'app_label': app_label,
            'cl': {
                'opts': {
                    'app_label': app_label,
                    'verbose_name_plural': opts.verbose_name_plural,
                }
            }
        })
        context.update(extra_context or {})
        return TemplateResponse(request, self.change_list_template,
                                context, current_app=self.admin_site.name)

    def get_changelists_for_object(self, request, obj, config=None, **kwargs):
        changelists = []

        if obj is not None:
            logger.debug('Editing an object, so do `get_changelists_for_object`')
            # store the old get here, because it gets changed inside the region
            # loops, which is a lossy process.
            old_get = request.GET
            # mutate the querystring and set some data onto it, which will
            # be passed to the get_changelist_filters method, as well as
            # being used to filter the ChangeList correctly.
            # new_get = request.GET.copy()
            new_get = QueryDict('', mutable=True)
            new_get[REQUEST_VAR_CT] = get_content_type(obj).pk
            new_get[REQUEST_VAR_ID] = obj.pk
            if config is None:
                config = EditRegionConfiguration(obj)
            for region in config.config:
                new_get[REQUEST_VAR_REGION] = region
                request.GET = new_get
                our_list_display = self.list_display[:]
                our_list_links = self.get_list_display_links(request,
                                                             our_list_display)
                ChangeList = self.get_changelist(request, **kwargs)
                cl = ChangeList(request=request, model=self.model,
                                list_display=our_list_display,
                                list_display_links=our_list_links,
                                list_filter=self.list_filter,
                                date_hierarchy=None, search_fields=None,
                                list_select_related=None, list_per_page=100,
                                list_max_show_all=100, list_editable=None,
                                model_admin=self, parent_obj=obj,
                                parent_conf=config)
                changelists.append(cl)
            # as the internal request.GET may be lossy, we restore the original
            # data here.
            request.GET = old_get
        return changelists

    def changelists_as_context_data(self, request, obj):
        """
        Sets up a context which is understood by the `changelist_view` template
        and EditRegionInline for displaying *the changelists only*

        Also used by the move view and ChunkAdmin subclasses for rendering
        out those changelists to the browser.
        """
        return {
            'inline_admin_formset': {
                'formset': {
                    'region_changelists': self.get_changelists_for_object(request,
                                                                          obj)
                },
            },
        }

    def render_changelists_for_object(self, request, obj):
        """
        Used by the move view, and ChunkAdmin subclasses to render *just the
        changelists*, for returning as JSON to be rendered on the client
        browser.
        """
        context = self.changelists_as_context_data(request, obj)
        return render_to_string(EditRegionInline.template, context)

    @property
    def media(self):
        base_media = super(EditRegionAdmin, self).media
        return base_media + shared_media

    def render_into_region(self, obj, context, **kwargs):
        msg = ("`render_into_region` called because the requested "
               "chunk wasn't cast down - likely the model is no longer "
               "enabled in the configuration.")
        if settings.DEBUG:
            raise NotImplementedError(msg)
        logger.warning(msg)
        return None

    def render_into_summary(self, obj, context, **kwargs):
        msg = ("`render_into_summary` called because the requested "
               "chunk wasn't cast down - likely the model is no longer "
               "enabled in the configuration.")
        if settings.DEBUG:
            raise NotImplementedError(msg)
        logger.warning(msg)
        return force_text(obj)


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

    def log_addition(self, request, object):
        """
        Log's against the Chunk, and it's parent object.
        """
        super(ChunkAdmin, self).log_addition(request, object)
        super(ChunkAdmin, self).log_addition(request, object.content_object)

    def log_change(self, request, object, message):
        """
        Log's against the Chunk, and it's parent object.
        """
        super(ChunkAdmin, self).log_change(request, object, message)
        super(ChunkAdmin, self).log_change(request, object.content_object,
                                           message)

    def log_deletion(self, request, object, object_repr):
        """
        Log's against the Chunk, and it's parent object.
        """
        super(ChunkAdmin, self).log_deletion(request, object, object_repr)
        super(ChunkAdmin, self).log_deletion(request, object.content_object,
                                             object_repr)

    @guard_querystring_m
    def save_model(self, request, obj, form, change):
        """
        Adds extra fields to the object so it's saved against the correct
        content type etc.
        """
        obj.content_type_id = request.GET[REQUEST_VAR_CT]
        obj.content_id = request.GET[REQUEST_VAR_ID]
        obj.region = request.GET[REQUEST_VAR_REGION]
        # if obj.position is None:
        #     found = get_chunks_in_region_count(EditRegionChunk,
        #                                        content_type=obj.content_type,
        #                                        obj_id=obj.content_id,
        #                                        region=obj.region)
        #     found2 = max(0, found)
        #     obj.position = found2 + 1
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
        parent_id = request.GET[REQUEST_VAR_ID]
        parent_ct = request.GET[REQUEST_VAR_CT]
        region = request.GET[REQUEST_VAR_REGION]

        # the following is all just about discovering chunk limits
        parent_class = get_content_type(parent_ct).model_class()
        parent_obj = parent_class.objects.get(pk=parent_id)
        erc = EditRegionConfiguration(parent_obj)
        available_chunks = erc.config[region]['models']
        limit = available_chunks[self.model]
        # now we have our possible limit, if there's a limit
        # (no infinity set via None) ensure we haven't hit it yet.
        if limit is not None:
            logger.debug('Limit of %(limit)d found for %(cls)r in region '
                         '"%(region)s"' % {
                             'limit': limit,
                             'cls': self.model,
                             'region': region,
                         })
            already_created = get_chunks_in_region_count(self.model,
                                                         content_type=parent_ct,
                                                         obj_id=parent_id,
                                                         region=region)
            if already_created >= limit:
                logger.info('Already hit limit of %(limit)d, found %(exists)d '
                            'objects in the database' % {
                                'limit': limit,
                                'exists': already_created,
                            })
                return self.response_max(request, limit, already_created)
        # we haven't got a limit for this chunk type, so carry on as normal.
        return super(ChunkAdmin, self).add_view(request, *args, **kwargs)

    @guard_querystring_m
    def change_view(self, request, *args, **kwargs):
        """
        This override only exists because I have no idea how to forceably guard
        the super() change_view without doing so.
        """
        return super(ChunkAdmin, self).change_view(request, *args, **kwargs)

    def maybe_fix_redirection(self, request, response, obj=None):
        """
        This is basically a middleware for admin responses from add/edit
        screens.

        Inspect's a URL, and adds in our required fields if they're not there.
        eg: if a URL has no querystring, or the querystring does not contain
        `content_id`, `content_type` and `region` it will attempt to insert
        them, and if `_autoclose` was in the requesting URL, it should be
        maintained.
        """
        resp = super(ChunkAdmin, self).maybe_fix_redirection(request,
                                                             response, obj)
        return_early = (
            not resp.has_header('location'),
            not hasattr(resp, 'redirect_parts'),
            hasattr(resp, 'canonical'),  # something wants to be *final*
            obj is None,
        )
        if any(return_early):
            return resp

        # get the modeladmin in question, from the URL provided.
        func = resolve(resp.redirect_parts[2]).func
        # python 3
        if hasattr(func, '__closure__'):
            func = func.__closure__
        else:  # python 2
            func = func.func_closure
        func = func[0].cell_contents

        # it doesn't look like a chunk admin, so we can't know we need to
        # redirect back to the parent.
        if (not hasattr(func, 'response_max')
                and not hasattr(func, 'render_into_region')):
            return resp

        # set up reasons to go back to the parent object's edit view.
        redirect_to_parent_if = (
            not self.wants_to_autoclose(request),
            not self.wants_to_continue_editing(request)
        )
        # we don't want to autoclose, and we don't want to save a new
        # or add another, so we're hopefully inside a bare add/change view
        # so we probably ought to go back to the parent object's edit view.
        if all(redirect_to_parent_if):
            abuse_adminlink = _add_link_to_context(
                admin_site=self.admin_site.name, request=request,
                opts=obj.content_object._meta, permname='change',
                url_params=[obj.content_id], query=resp.redirect_parts[3])
            resp.redirect_parts = list(urlsplit(abuse_adminlink['link']))
            resp['Location'] = urlunsplit(resp.redirect_parts)
            return resp

        # we either wanted to autoclose, or we wanted to continue/add another
        # etc, so we don't want to redirect elsewhere, we just want to
        # update the querystring with fields required by the ChunkAdmin
        querystring = QueryDict(resp.redirect_parts[3], mutable=True)

        # delete any values which could be wrong [but shouldn't be!]
        for x in (REQUEST_VAR_REGION, REQUEST_VAR_CT, REQUEST_VAR_ID):
            if x in querystring:
                del querystring[x]
        querystring.update({REQUEST_VAR_ID: obj.content_id,
                            REQUEST_VAR_CT: obj.content_type_id,
                            REQUEST_VAR_REGION: obj.region})
        resp.redirect_parts[3] = querystring.urlencode()
        resp['Location'] = urlunsplit(resp.redirect_parts)
        return resp

    @guard_querystring_m
    def delete_view(self, request, object_id, extra_context=None):
        """
        This override exists to guard the querystring, but also to provide
        *needed data* to the available context. This is mostly used for ferrying
        the parent object details to `get_response_delete_context` so that it
        can render the changelists back to the client.
        """
        obj = self.get_object(request, unquote(object_id))
        needed_data = extra_context or {}
        # Django has deprecated request.REQUEST. Sigh
        found_popup_in_request = (
            "_popup" in request.GET,
            "_popup" in request.POST,
        )
        # emulate the behaviour of add/change_view
        needed_data.update(is_popup=any(found_popup_in_request))
        if obj is not None:
            needed_data.update(gfk={'content_id': obj.content_id,
                                    'content_type': obj.content_type,
                                    'content_object': obj.content_object})
        return super(ChunkAdmin, self).delete_view(request, object_id,
                                                   extra_context=needed_data)

    def get_response_add_context(self, request, obj):
        """
        Override the default contexts generated by AdminlinksMixin to add our
        HTML.
        """
        modeladmin = get_modeladmin(EditRegionChunk, self.admin_site.name)
        changelists = modeladmin.render_changelists_for_object(
            request=request, obj=obj.content_object)
        context = super(ChunkAdmin, self).get_response_add_context(request, obj)
        context.update(html=changelists)
        return context

    def get_response_change_context(self, request, obj):
        """
        Override the default contexts generated by AdminlinksMixin to add our
        HTML.
        """
        modeladmin = get_modeladmin(EditRegionChunk, self.admin_site.name)
        changelists = modeladmin.render_changelists_for_object(
            request=request, obj=obj.content_object)
        context = super(ChunkAdmin, self).get_response_change_context(request,
                                                                      obj)
        context.update(html=changelists)
        return context

    def get_response_delete_context(self, request, obj_id, extra_context):
        """
        Override the default contexts generated by AdminlinksMixin to add our
        HTML.
        """
        modeladmin = get_modeladmin(EditRegionChunk, self.admin_site.name)
        context = super(ChunkAdmin, self).get_response_delete_context(
            request, obj_id, extra_context)
        try:
            changelists = modeladmin.render_changelists_for_object(
                request=request, obj=extra_context['gfk']['content_object'])
            context.update(html=changelists)
        except KeyError as e:
            # extra context didn't include gfk, or possibly content_object within
            # that gfk key, either way, we now can't render the HTML for the
            # client :(
            pass
        return context

    def render_into_region(self, obj, context, **kwargs):
        """
        These exist purely to avoid unexpected breakages if an admin subclass
        doesn't implement them.

        :param obj: The :class:`~editregions.models.EditRegionChunk` subclass
                    currently expecting to be rendered.
        :param context: The overall template context.
        :param extra: Additional data available when rendering this object,
                      mostly related to the current iteration state.
        :return: Some output. Usually HTML for output on a page.
        """
        msg = ('`render_into_region` not implemented on {0!r}'.format(
            self.__class__))
        if settings.DEBUG:
            raise NotImplementedError(msg)
        logger.warning(msg)
        return None

    def render_into_summary(self, obj, context, **kwargs):
        """
        These exist purely to avoid unexpected breakages if an admin subclass
        doesn't implement them.

        :param obj: The :class:`~editregions.models.EditRegionChunk` subclass
                    currently expecting to be rendered.
        :param context: The overall template context.
        :param extra: Additional data available when rendering this summary,
                      mostly related to the current iteration state.
        :return: Some output. Usually a text representation of the
                 :meth: `~editregions.admin.modeladmins.ChunkAdmin.render_into_region`
        """
        msg = ('`render_into_summary` not implemented on {0!r}'.format(
            self.__class__))
        if settings.DEBUG:
            raise NotImplementedError(msg)
        logger.warning(msg)
        return None

    @property
    def media(self):
        media_instance = super(ChunkAdmin, self).media
        return media_instance + Media(js=['editregions/js/childevents.js'])


class SupportsEditRegions(object):
    editregion_template_name_suffix = '_detail'

    def get_inline_instances(self, request, *args, **kwargs):
        klass = EditRegionInline
        if klass not in self.inlines:
            self.inlines.append(klass)
        return super(SupportsEditRegions, self).get_inline_instances(
            request, *args, **kwargs)

    def get_editregions_templates(self, obj):
        opts = obj._meta.opts
        kwargs = {'app': opts.app_label, 'pk': obj.pk,
                  'suffix': self.editregion_template_name_suffix}
        if hasattr(opts, 'model_name'):
            kwargs.update(model=opts.model_name)
        else:
            kwargs.update(model=opts.module_name)
        return (
            '{app}/{model}/{pk}{suffix}.html'.format(**kwargs),
            '{app}/{model}{suffix}.html'.format(**kwargs),
            '{app}{suffix}.html'.format(**kwargs),
        )
