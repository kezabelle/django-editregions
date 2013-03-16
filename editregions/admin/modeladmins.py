# -*- coding: utf-8 -*-
from copy import deepcopy
import logging
from django.contrib.admin import helpers
from django.contrib.admin.options import StackedInline, TabularInline, csrf_protect_m
from django.contrib.admin.util import unquote
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import SuspiciousOperation, ImproperlyConfigured, PermissionDenied
from django.db import transaction
from django.db.models.fields import BLANK_CHOICE_DASH
from django.forms.fields import Field
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.template.loader import render_to_string
from django.utils.datastructures import SortedDict
from django.utils.encoding import force_unicode
from django.utils.functional import update_wrapper
from django.utils.safestring import mark_safe
from django.utils.text import normalize_newlines
from django.utils.translation import string_concat, ugettext_lazy as _
from adminlinks.admin import AdminlinksMixin, POPUP_VAR, FRONTEND_VAR
from editregions.admin.decorators import guard_querystring_m
from editregions.admin.forms import ReorderChunksForm, MovementForm
from editregions.admin.utils import RequiredInlineFormSet, AdminChunkWrapper
from editregions.admin.widgets import ChunkList
from editregions.utils.regions import (sorted_regions, scan_template_for_named_regions,
                                       get_pretty_region_name, validate_region_name,
                                       get_enabled_chunks_for_region)
from editregions.utils.chunks import get_chunks_for_region, get_last_chunk_position


logger = logging.getLogger(__name__)

class OneToOneStackedInline(StackedInline):
    extra = 1
    max_num = 1
    can_delete = False
    formset = RequiredInlineFormSet
    template = 'admin/editregions/edit_inline/stacked_one.html'



class OneToOneTabularInline(TabularInline):
    extra = 1
    max_num = 1
    can_delete = False
    formset = RequiredInlineFormSet
    template = 'admin/editregions/edit_inline/tabular_one.html'


class RegionAdmin(AdminlinksMixin):
    """
    Brief note to self:
    If both region and obj are required for a method signature, for consistency
    try and ensure that obj comes first. If request is involved, it comes first.
    thus: def method(self, request, obj, region, *args, **kwargs)
    """
    edit_regions = []

    def _get_content_type(self, obj=None):
        # We use get_by_natural_key in case it's an older Django version than 1.4,
        # and we want to allow for using proxy models,
        # which isn't fixed until 1.5
        if obj is None:
            obj = self.model
        return ContentType.objects.get_by_natural_key(obj._meta.app_label,
            obj._meta.module_name)

    def get_regions(self, request, obj=None):
        """
        We only want to get regions once an object has been initially saved,
        so that we can access the appropriate ContentType and Object ID pair.

        If editing an existing object, regions found in the subclass attribute
        `edit_regions` will be used.

        .. testcase: TODO
        """
        if obj is None:
            return []
        for region in self.edit_regions:
            validate_region_name(region)
        return self.edit_regions

    def get_region_name(self, region):
        """
        .. testcase: TODO
        """
        validate_region_name(region)
        return get_pretty_region_name(region)

    def get_region_widget(self, obj, region):
        """
        Overridable display of the widget for editing chunks in a region.
        Note that while this is a form Widget, it really just renders a template,
        because the way Django widgets work is really horrid, and no-one should
        have to put up with it.

        .. testcase: TODO
        """
        content_id = obj.pk

        content_type = self._get_content_type(obj).pk
        return ChunkList(attrs={
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
        })

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


    def get_unused_regions(self):
        """
        .. testcase: TODO
        """
        # The idea is, given we're working with X template, find regions in the
        # database which aren't used by this template, and display those differently.
        return 1

    def get_fieldsets(self, request, obj=None, *args, **kwargs):
        """
        Overrides the default fieldset to add our regions into the admin's expectations
        Returns a list.

        .. testcase: TODO
        """

        # We need to deepcopy here to avoid self.fieldsets getting populated
        # with fields from previously edited pages. I have no idea why, because
        # I can't figure out where self.fieldsets is re-bound, but django CMS
        # does this too, so it's probably the same issue.
        fieldsets = deepcopy(list(super(RegionAdmin, self).get_fieldsets(request,
            obj)))
        success_conditions = [
            obj is not None,
            POPUP_VAR not in request.REQUEST,
            FRONTEND_VAR not in request.REQUEST,
            ]
        if all(success_conditions):
            # Find all regions, and go through the existing fieldsets checking
            # to see if they're already set up correctly. If they're not set up
            # correctly, remove them from the existing fieldsets for configuration
            # later on.
            regions_found = sorted_regions(self.get_regions(request, obj))
#            already_setup_regions = set()
#            for _f, data in fieldsets:
#                must_pass = (
#                    len(data['fields']) == 1,
#                    data['fields'] in regions_found,
#                    'classes' in data,
#                    'chunk-holder' in data.get('classes', {}),
#                    # Note: at the moment, there's no way I can think of to allow
#                    # for manual fieldsets, but I don't want to delete the code yet
#                    # so we're just going to fail this test.
#                    True is False,
#                )
#                if all(must_pass):
#                    already_setup_regions.add(data['fields'])
#                else:
#                    for region in regions_found:
#                        if region in data['fields']:
#                            data['fields'].remove(region)
#
#            # Once we've checked and tidied up the existing fieldsets, we can
#            # find the regions that weren't set up correctly (or at all), and
#            # go through the correct process for them.
#            regions_to_add = [region for region in regions_found
#                              if region not in already_setup_regions]
            for region in regions_found:
                fieldsets.append(
                    (self.get_region_name(region), {
                        u'fields': [region],
                        u'classes': [u'region', u'chunk-holder'],
                        }),
                )
        return fieldsets

    def get_form(self, request, obj=None, **kwargs):
        """
        Works in conjunction with get_fieldsets to provision a number of
        displayable placeholder editors.

        :return: django.forms.models.ModelForm
        """
        form = super(RegionAdmin, self).get_form(request, obj, **kwargs)
        # only try and do our region things if we're editing something.
        # This is because at the 'add' stage, we won't know about any object id.
        success_conditions = [
            obj is not None,
            POPUP_VAR not in request.REQUEST,
            FRONTEND_VAR not in request.REQUEST,
        ]
        if all(success_conditions):
            extra_fields = SortedDict()
            # TODO: Figure out a way to avoid calling get_regions here, as it
            # will get called again by get_fieldsets.
            found_regions = self.get_regions(request, obj)
            # we want to exclude the potentially generated regions.
            # sidenote: self.exclude may evaluate to None, hence the ``or []`` guard.
            exclusions = set(found_regions)
            exclusions |= set(self.exclude or [])
            self.exclude = exclusions
            # This whole bit could be in an if branch, but I can't be bothered
            # so we'll always iterate over a potentially empty list, and add
            # a potentially empty dictionary back to the form.
            for region in found_regions:
                extra_fields[region] = Field(required=False,
                    widget=self.get_region_widget(obj, region))
            form.base_fields.update(extra_fields)
        return form

#
#    def reorder_chunks(self, request, obj_id):
#        ct = self._get_content_type()
#        # todo, check permissions
#        import pdb; pdb.set_trace()
#        form = ReorderChunksForm(data=request.GET, files=None,
#            content_type=ct, obj_id=obj_id)
#        if form.is_valid() and form.save():
#            return HttpResponse('ok')
#        return HttpResponseBadRequest('invalid')

    class Media:
        css = {
            'screen': [
                'adminlinks/css/fancyiframe-custom.css',
                'css/editregions.css',
            ],
        }
        js = [
            'adminlinks/js/jquery.fancyiframe.js',
            'js/jquery.tablednd.js',
            'js/jquery.animate-colors.js',
            'js/editregions.js',
        ]


class RegionTemplateAdmin(RegionAdmin):
    template_key = 'current_template'
    template_changed = '%s_has_been_changed'

    def get_regions(self, request, obj=None):
        """
        As with `RegionAdmin`, We only want to get regions once an object has
        been initially saved, so that we can access the appropriate ContentType
        and Object ID pair.

        If editing an existing object, regions found by scanning a template
        will be returned, and sorted into a unique list in the order they appear
        in the compiled template.
        """
        if obj is None:
            return []
        if not hasattr(obj, 'get_template'):
            raise ImproperlyConfigured(u'%(obj)r must have a `get_template` method '
            u'to be used with %(cls)r' % {'obj': obj.__class__, 'cls': RegionTemplateAdmin})
        regions = scan_template_for_named_regions(self.get_template(request, obj))
        return sorted_regions(regions)

    def get_template(self, request, obj=None):
        """Allows for hooking into the process of deciding on a template, if necessary.

        By default, we're only using it to look in the query string for an attempt
        at loading a different template.

        :param request: The WSGIRequest
        :param obj: The object currently begin changed.
        :return: unicode string representing a path in any TEMPLATE_DIRS
        """
        new_template = request.GET.get(self.template_key, None)
        if new_template is not None:
            return new_template
        return obj.get_template(request)

    def get_object(self, request, object_id):
        """Allow us to change the template being requested.
        Unfortunately, this is horrible, because we don't know the template field
        name, nor can I figure out how to modify the initial data for an edit
        object in change_view.

        :param request:  The WSGIRequest
        :param object_id: The object idenitifer we'd like to find.
        :return: our model object.
        """
        obj = super(RegionTemplateAdmin, self).get_object(request, object_id)
        # If we found an object, we can loop through its fields and find the
        # nominated template field, and change it to reflect any change dictated
        # by self.get_template - which itself may just return obj.get_template again.
        if obj is not None:
            setattr(obj, self.template_changed % self.template_key, False)
            existing_template = obj.get_template(request)
            for fieldname in obj._meta.get_all_field_names():
                # the attribute matches, which is a good thing! now we can modify
                # it and end the loop as early as possible.
                if getattr(obj, fieldname, None) == existing_template:
                    setattr(obj, fieldname, self.get_template(request, obj))
                    break

            # this is used by self.get_form to establish whether to show
            # more help text.
            if existing_template != self.get_template(request, obj):
                setattr(obj, self.template_changed % self.template_key, True)
        return obj

    def get_form(self, request, obj=None, **kwargs):
        """Overrides the default form returned, so that we can patch on template specific things.

        :param request: The WSGIRequest
        :param obj: The object currently begin changed.
        :param kwargs: Additional arguments for passing up the parent chain.
        :return: ModelForm
        """
        form = super(RegionTemplateAdmin, self).get_form(request, obj, **kwargs)
        # Now we want to mark our template field so that we can find it
        # in the DOM.
        if obj is not None:
            given_template = force_unicode(self.get_template(request, obj))
            # make sure the new template is valid (hopefully), and mark the field
            # for the JavaScript. Then break the loop as early as possible.
            for field_name, bound_field in form.base_fields.items():
                if hasattr(bound_field, 'valid_value') and bound_field.valid_value(given_template):
                    bound_field.widget.attrs.update({'rel': self.template_key})
                    help_text_requirements = [
                        self.template_key in request.GET,
                        getattr(obj, self.template_changed % self.template_key, False) == True
                    ]
                    if all(help_text_requirements):
                        # TODO: add bmispelon to thanks list for pointing me at string_concat
                        bound_field.help_text = string_concat(bound_field.help_text,
                            _('<br><b>This change in template has not yet been saved permanently.</b>'))
                    break

        return form


class ChunkAdmin(AdminlinksMixin):
    actions = None
    actions_on_top = False
    actions_on_bottom = False
    save_as = False
    save_on_top = False
    exclude = ['content_type', 'content_id', 'region', 'position',
               'subcontent_type']
    change_readonly_fields = ['created', 'modified']

    def _get_wrap(self):
        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            return update_wrapper(wrapper, view)
        return wrap

    def get_urls(self):
        original_urls = super(ChunkAdmin, self).get_urls()
        from django.conf.urls.defaults import patterns, url
        wrap = self._get_wrap()
        info = self.model._meta.app_label, self.model._meta.module_name
        extra_urls = patterns('',
            url(r'^(?P<obj_id>.+)/move/$',
                wrap(self.move_view),
                name='%s_%s_move' % info)
        )
        # extras have to come first, otherwise everything is gobbled by the
        # greedy nature of (.+) for the changelist view.
        return extra_urls + original_urls

    def get_model_perms(self, request, *args, **kwargs):
        """ Shadow method for the default ModelAdmin. Allows us to hide chunks.
        By using an empty dictionary, permissions still work, but chunk administration
        views are hidden from the default AdminSite index.

        :param request: The WSGIRequest.
        :return: Empty dictionary
        """
        return {}

    def get_readonly_fields(self, request, obj=None):
        """ Shadow method for the default ModelAdmin.
        Allows us to view created/modified fields as read only.

        :param request: The WSGIRequest.
        :param obj: the current object to be viewed.
        :return:
        """
        if obj is not None:
            extras = list(self.readonly_fields)
            extras.extend(self.change_readonly_fields)
            return extras
        return self.readonly_fields

    def get_chunk_renderer_content_type(self):
        """
        Someone else should render this chunk, rather than the regiterered model.
        :return: The content type for the renderer
        :rtype: :class:ContentType
        """
        opts = self.model._meta
        if getattr(self, 'chunk_renderer', None) is not None:
            opts = self.chunk_renderer._meta
        return ContentType.objects.get_by_natural_key(app_label=opts.app_label,
            model=opts.module_name)

    def save_model(self, request, obj, form, change):
        """Adds extra fields to the object so it's saved against the correct content type etc."""
        validate_region_name(request.GET.get('region'))
        obj.content_type = ContentType.objects.get_for_id(request.GET.get('content_type'))
        obj.content_id = int(request.GET.get('content_id'))
        obj.region = str(request.GET.get('region'))
        obj.subcontent_type = self.get_chunk_renderer_content_type()
        # If the position is not set,
        # it's easiest to assume it's going on the end of the chunk list.
        if obj.position is None:
            new_position = get_last_chunk_position(content_id=obj.content_id,
                content_type=obj.content_type, region_name=obj.region)
            obj.position = new_position + 1
        super(ChunkAdmin, self).save_model(request, obj, form, change)


    def guard_querystring(self, request):
        extra_fields = []
        fields = ['content_type', 'content_id', 'region'] + extra_fields
        self._guarded = [(field, request.GET.get(field, None)) for field in fields]
        self._guarded = dict(self._guarded)
        if not all(self._guarded.values()):
            logger.warning('Parameter missing from request: %s' % request.path,
                extra={
                    'status_code': 405,
                    'request': request
                }
            )
            raise SuspiciousOperation('Parameter missing from request')

    def response_max(self, request, limit, found):
        """
        If a chunk limit has been reached,
        adding a new one via `add_view` will instead return this view.
        """
        possible_templates = [
            'admin/editregions/limit_reached.html'
        ]
        context = {
            'is_popup': "_popup" in request.REQUEST,
            'found': found,
            'limit': limit,
        }
        return render_to_response(possible_templates, context,
            context_instance=RequestContext(request))

#    @csrf_protect_m
#    @transaction.commit_on_success
#    @guard_querystring_m
    def add_view(self, request, *args, **kwargs):
        self.guard_querystring(request)
        available_chunks = get_enabled_chunks_for_region(str(request.GET.get('region')))
        limit = available_chunks[self.model]
        # if there's a limit (no infinity set) ensure we haven't it it yet.
        if limit is not None:
            already_created = self.model.objects.filter(**self._guarded).count()
            if already_created >= limit:
                return self.response_max(request, limit, already_created)
        return super(ChunkAdmin, self).add_view(request, *args, **kwargs)

    def change_view(self, request, *args, **kwargs):
        #self.guard_querystring(request)
        return super(ChunkAdmin, self).change_view(request, *args, **kwargs)

    def delete_view(self, request, *args, **kwargs):
        self.guard_querystring(request)
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

    def get_admin_wrapper_class(self):
        """
        .. testcase: TODO
        """
        return AdminChunkWrapper

    def move_view(self, request, obj_id, *args, **kwargs):
        self.guard_querystring(request)
        opts = self.model._meta
        obj = self.get_object(request, unquote(obj_id))
        if not self.has_change_permission(request, obj):
            raise PermissionDenied

        form = MovementForm(
            region=str(request.GET.get('region')),
            data=request.POST or None,
            files=None,
            initial=None)
        the_fieldset = [(None, {'fields': [form.base_fields.keys()]})]
        adminForm = helpers.AdminForm(form, the_fieldset, prepopulated_fields={},
            readonly_fields=None, model_admin=self)
        media = self.media + adminForm.media

        context = {
            'title': '', #_('Change %s') % force_unicode(obj),
            'adminform': adminForm,
            'object_id': obj_id,
            'original': obj,
            'show_delete': False,
            'is_popup': POPUP_VAR in request.REQUEST,
            'media': mark_safe(media),
            'errors': helpers.AdminErrorList(form, inline_formsets=[]),
            'root_path': getattr(self.admin_site, 'root_path', None),
            'app_label': opts.app_label,
        }
        return self.render_change_form(request, context, obj=obj)


    def get_response_add_context(self, request, obj):
        """
        This method allows us to add custom data to any success template displayed
        because we're in our admin popup.
        TODO: refactor!
        """
        klass = self.get_admin_wrapper_class()
        opts = ContentType.objects.get_for_id(obj.chunk_content_type_id).model_class()._meta
        html = render_to_string('admin/editregions/widgets/single_existing_chunk.html', {
            'chunk': klass(opts=opts, namespace=self.admin_site.app_name,
                region=obj.region, content_type=obj.content_type,
                content_id=obj.content_id, obj=obj)
        })
        html = mark_safe(normalize_newlines(html).replace("\n", ""))
        return {'attached_to': self._guarded, 'html': html}

    def get_response_change_context(self, request, obj):
        """
        This method allows us to add custom data to any success template displayed
        because we're in our admin popup.
        TODO: refactor!
        """
        klass = self.get_admin_wrapper_class()
        opts = ContentType.objects.get_for_id(obj.chunk_content_type_id).model_class()._meta
        html = render_to_string('admin/editregions/widgets/single_existing_chunk.html', {
            'chunk': klass(opts=opts, namespace=self.admin_site.app_name,
                region=obj.region, content_type=obj.content_type,
                content_id=obj.content_id, obj=obj)
        })
        html = mark_safe(normalize_newlines(html).replace("\n", ""))
        return {'attached_to': self._guarded, 'html': html}

    def get_response_delete_context(self, request, obj_id):
        """
        This method allows us to add custom data to any success template displayed
        because we're in our admin popup.
        Note that unlike get_response_add_context and get_response_change_context,
        we do not have access to `obj`,
        because it will probably already have been deleted by this point.
        """
        return {'attached_to': self._guarded}
