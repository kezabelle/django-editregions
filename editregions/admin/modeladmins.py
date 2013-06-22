# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from functools import update_wrapper
import logging
from django.conf import settings
import warnings
from django.template.response import TemplateResponse
from adminlinks.admin import AdminlinksMixin
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
from editregions.utils.data import (get_modeladmin, get_content_type,
                                    get_model_class)
from editregions.utils.rendering import render_one_summary
from editregions.admin.changelist import EditRegionChangeList
from editregions.admin.forms import EditRegionInlineFormSet, MovementForm
from editregions.admin.utils import (AdminChunkWrapper, shared_media,
                                     guard_querystring_m, FakeObj)
from editregions.models import EditRegionChunk
from editregions.utils.regions import (get_enabled_chunks_for_region,
                                       get_pretty_region_name,
                                       get_first_valid_template,
                                       get_regions_for_template)
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
    change_list_template = 'admin/editregions/change_list.html'

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
        templates = obj.content_object.get_region_groups()
        template = get_first_valid_template(templates)
        return get_pretty_region_name(template, obj.region)
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
        AdminChunkWrapper = self.get_admin_wrapper_class()
        delete_url = AdminChunkWrapper(opts=obj._meta,
                                       namespace=self.admin_site.name,
                                       obj=obj).get_delete_url()
        html = ('<div class="drag_handle" data-pk="%(pk)s" data-href="%(url)s">'
                '</div>&nbsp;<a class="delete_handle" href="%(delete_url)s">'
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

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.module_name
        urlpatterns = patterns('',
                               # parent_ct is the Django ContentType PK for
                               # the object the EditRegionChunks are bound to
                               # eg: a page, a blog post, a project.
                               # parent_id is the PK of the parent object in
                               # question. We don't know what format the PK takes
                               # so we accept anything.
                               url(r'^(?P<parent_ct>\d+)/(?P<parent_id>.+)/$',
                                   wrap(self.list_view),
                                   name='%s_%s_changelist' % info),
                               # moving an object from one position to another
                               # potentially across regions.
                               url(r'^move/$',
                                   wrap(self.move_view),
                                   name='%s_%s_move' % info))
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
            html = self.render_changelists_for_object(request=request,
                                                      obj=form.cleaned_data['pk'].content_object)
            json_data = {
                'action': 'move', 'html': html,
                'primary_key': form.cleaned_data['pk'].pk,
            }
            self.log_change(request, *form.change_message())
            self.log_change(request, *form.parent_change_message())
            return HttpResponse(simplejson.dumps(json_data),
                                mimetype='application/json')
        return HttpResponseBadRequest(simplejson.dumps(form.errors),
                                      mimetype='application/json')

    def queryset(self, *args, **kwargs):
        """
        Don't use the default queryset/manager, as it won't be our interface
        to polymorphic (downcast) EditRegionChunk subclasses. Instead,
        uses :func:`editregions.utils.chunks.get_chunks_for_region` and then
        applies the expected ordering.

        :param args: Stuff to pass through to
               :meth:`~django.contrib.admin.options.BaseModelAdmin.get_ordering`
        :param kwargs: Stuff to pass through to
               :meth:`~django.contrib.admin.options.BaseModelAdmin.get_ordering`
        :return: our EditRegionChunks, but already downcast to their final form.
        :rtype: :class:`~django.db.models.query.QuerySet`
        """
        qs = get_chunks_for_region()
        ordering = self.get_ordering(*args, **kwargs)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs

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
            parent_obj = get_model_class(ct).objects.get(pk=pk)
        except ObjectDoesNotExist as e:
            return HttpResponseBadRequest('something went wrong')

        templates = parent_obj.get_region_groups()
        template = get_first_valid_template(templates)
        AdminChunkWrapper = self.get_admin_wrapper_class()
        filters = (AdminChunkWrapper(**{
            'opts': x._meta,
            'namespace': self.admin_site.app_name,
            'region': region,
            'content_type': ct,
            'content_id': pk,
        }) for x in get_enabled_chunks_for_region(template, region))
        return filters

    def get_admin_wrapper_class(self):
        return AdminChunkWrapper

    def list_view(self, request, parent_ct, parent_id, extra_context=None):
        obj = get_model_class(parent_ct).objects.get(pk=parent_id)
        extra_context = extra_context or {}
        context = self.changelists_as_context_data(request, obj)
        opts = self.model._meta
        app_label = opts.app_label
        context.update({
            'module_name': force_unicode(opts.verbose_name_plural),
            'title': _('Select %s to change') % force_unicode(opts.verbose_name),
            'allow_editregions': True,
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

    def get_regions_for_object(self, request, obj, **kwargs):
        """
        We only want to get regions once an object has been initially saved, so
        that we can access the appropriate ContentType and Object ID pair.

        If editing an existing object, regions found by scanning a template
        will be returned, and sorted into a unique list in the order they appear
        in the compiled template.
        """
        try:
            logger.debug('Requesting region group choices from %(obj)r' % {
                'obj': obj,
            })
            templates = obj.get_region_groups()
        except AttributeError as e:
            msg = ('%(obj)r must have a `get_region_groups` method to be '
                   'used with %(cls)r' % {
                       'obj': obj.__class__, 'cls': EditRegionInline
                   })
            logger.error(msg)
            if settings.DEBUG:
                raise ImproperlyConfigured(msg)
            #: in production, we may not raise ImproperlyConfigured, in which
            #: we would be accessing `templates` without it being set.
            templates = ()
        template = get_first_valid_template(templates)
        return get_regions_for_template(template)

    def get_changelists_for_object(self, request, obj, **kwargs):
        changelists = []

        if obj is not None:
            logger.debug('Editing an object, so do `get_changelists_for_object`')
            # from here on out, we heavily reuse the other modeladmin
            # self.model should be EditRegionChunk
            modeladmin = get_modeladmin(self.model, self.admin_site.name)

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
            # as the internal request.GET may be lossy, we restore the original
            # data here.
            request.GET = old_get
        return changelists

    def changelists_as_context_data(self, request, obj):
        return {
            'inline_admin_formset': {
                'formset': {
                    'region_changelists': self.get_changelists_for_object(request,
                                                                          obj)
                },
            },
        }

    def render_changelists_for_object(self, request, obj):
        context = self.changelists_as_context_data(request, obj)
        return render_to_string(EditRegionInline.template, context)

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
    ct_field = REQUEST_VAR_CT
    ct_fk_field = REQUEST_VAR_ID
    template = 'admin/editregions/edit_inline/none.html'

    def get_formset(self, request, obj=None, **kwargs):
        # sidestep validation which wants to inherit from BaseModelFormSet
        self.formset = EditRegionInlineFormSet
        formset = super(EditRegionInline, self).get_formset(request, obj, **kwargs)
        modeladmin = get_modeladmin(EditRegionChunk, self.admin_site.name)
        if obj is not None and request.method == 'POST':
            # As I won't remember why we have to do this, later, this is the
            # traceback which not doing it caused:
            # https://gist.github.com/kezabelle/40653a0ad1ffd8fc77ba
            # Basically, the template gets changed half way through the request
            # because of the different points at which objects are saved.
            # By not relying on the new instance (with the changed template)
            # instead using the one in the DB (with the old template) we can
            # ensure the regions line up correctly.
            logger.info('Editing an %(obj)r; we may be changing the region '
                        'group being used, so re-grabbing the DB version')
            obj = obj.__class__.objects.get(pk=obj.pk)
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

    def log_addition(self, request, object):
        """
        Should log against the parent object?

        :param request:
        :type request:
        :param object:
        :type object:
        :return:
        :rtype:
        """
        super(ChunkAdmin, self).log_addition(request, object)

    def log_change(self, request, object, message):
        """
        Should log against the parent object too

        :param request:
        :type request:
        :param object:
        :type object:
        :param message:
        :type message:
        :return:
        :rtype:
        """
        super(ChunkAdmin, self).log_change(request, object, message)

    def log_deletion(self, request, object, object_repr):
        """
        Deletes should be logged against the parent thing.

        :param request:
        :type request:
        :param object:
        :type object:
        :param object_repr:
        :type object_repr:
        :return:
        :rtype:
        """
        super(ChunkAdmin, self).log_deletion(request, object, object_repr)

    @guard_querystring_m
    def save_model(self, request, obj, form, change):
        """
        Adds extra fields to the object so it's saved against the correct
        content type etc.
        """
        obj.content_type_id = request.GET[REQUEST_VAR_CT]
        obj.content_id = request.GET[REQUEST_VAR_ID]
        obj.region = request.GET[REQUEST_VAR_REGION]
        if obj.position is None:
            found = get_chunks_for_region(content_type=obj.content_type,
                                          content_id=obj.content_id,
                                          region=obj.region).count()
            obj.position = found+1
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
        parent_class = get_content_type(parent_ct).model_class()
        parent_obj = parent_class.objects.get(pk=parent_id)
        templates = parent_obj.get_region_groups()
        template = get_first_valid_template(templates)
        available_chunks = get_enabled_chunks_for_region(template,
                                                         region)
        limit = available_chunks[self.model]
        # if there's a limit (no infinity set) ensure we haven't it it yet.
        if limit is not None:
            logger.debug('Limit of %(limit)d found for %(cls)r in region '
                         '"%(region)s"' % {
                             'limit': limit,
                             'cls': self.model,
                             'region': region,
                         })
            filters = {'content_type': parent_ct, 'content_id': parent_id,
                       'region': region}
            already_created = self.model.objects.filter(**filters).count()
            if already_created >= limit:
                logger.info('Already hit limit of %(limit)d, found %(exists)d '
                            'objects in the database' % {
                                'limit': limit,
                                'exists': already_created,
                            })
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

    def get_response_extra_context(self, request, obj, action):
        """
        This method allows us to add custom data to any success template displayed
        because we're in our admin popup.
        """
        modeladmin = get_modeladmin(EditRegionChunk, self.admin_site.name)
        ctx_data = {
            'action': {
                'add': action == 'add',
                'change': action == 'change',
                'delete':  action == 'delete',
            },
            'object': {
                'pk': obj.pk,
                'id': obj.pk,
            },
            'html': modeladmin.render_changelists_for_object(request, obj.content_object)
        }
        return ctx_data

    def get_response_add_context(self, request, obj):
        return self.get_response_extra_context(request, obj, 'add')

    def get_response_change_context(self, request, obj):
        return self.get_response_extra_context(request, obj, 'change')

    def get_response_delete_context(self, request, obj_id):
        fake_obj = FakeObj(obj_id)
        return self.get_response_extra_context(request, fake_obj, 'delete')

    def render_into_region(self, obj, context):
        """
        These exist purely to avoid unexpected breakages if an admin subclass
        doesn't implement them.

        :param obj: The :class:`~editregions.models.EditRegionChunk` subclass
                    currently expecting to be rendered.
        :param context: The overall template context.
        :return: Some output. Usually HTML for output on a page.
        """
        warnings.warn('`render_into_region` not implemented on %r' % self.__class__,
                      RuntimeWarning)

    def render_into_summary(self, obj, context):
        """
        These exist purely to avoid unexpected breakages if an admin subclass
        doesn't implement them.

        :param obj: The :class:`~editregions.models.EditRegionChunk` subclass
                    currently expecting to be rendered.
        :param context: The overall template context.
        :return: Some output. Usually a text representation of the
                 :meth: `~editregions.admin.modeladmins.ChunkAdmin.render_into_region`
        """
        warnings.warn('`render_into_summary` not implemented on %r' % self.__class__,
                      RuntimeWarning)
