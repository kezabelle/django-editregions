# -*- coding: utf-8 -*-
from django import template
from django.contrib.contenttypes.models import ContentType
from editregions.models import EditRegionChunk
from editregions.utils.chunks import get_chunks_for_region
from editregions.admin.utils import AdminChunkWrapper
from editregions.utils.data import convert_context_to_dict
from editregions.utils.regions import (validate_region_name, fake_context_payload,
                                       get_pretty_region_name,
                                       get_enabled_chunks_for_region)
from adminlinks.templatetags.utils import get_admin_site, context_passes_test
from adminlinks.templatetags.adminlinks_buttons import _add_custom_link_to_context
from classytags.arguments import StringArgument, Argument
from classytags.core import Options
from classytags.helpers import InclusionTag

register = template.Library()


class EditRegionToolbar(InclusionTag):
    # This template being here allows us to override all adminlinks stuff in one
    # place, so while it's unconventional, because it's not in
    # 'editregions/adminlinks' I just don't care, it's useful.
    template = 'adminlinks/editregion_toolbar.html'

    options = Options(
        StringArgument('name', required=True, resolve=False),
        Argument('content_object', required=True, default=None, resolve=True),
        StringArgument('admin_site', required=False, default='admin'),
    )

    def get_context(self, context, name, content_object, admin_site):
        """
        ..todo:: document

        Always returns the existing context.
        """
        validate_region_name(name)

        # if we're in a fake request to this template, assume we're scanning
        # for placeholders, so we can stop early!
        if fake_context_payload in context:
            return context

        site = get_admin_site(admin_site)
        if context_passes_test(context) and site is not None:
            link = _add_custom_link_to_context(admin_site, context['request'],
                                        EditRegionChunk._meta, 'change',
                                        'changelist', None)
            context.update(link)
            context.update({u'verbose_name': get_pretty_region_name(name)})
            # modeladmins = get_registered_modeladmins(context['request'], site)
            # TODO: fix this to be more DRY, as it's a copy-paste from admin.
#            available_chunks = [AdminChunkWrapper(**{
#                'opts': x._meta,
#                'namespace': site.app_name,
#                'region': name,
#                'content_type': ContentType.objects.get_for_model(content_object).pk,
#                'content_id': content_object.pk,
#            }) for x in get_enabled_chunks_for_region(name)]
#            existing_chunks = [AdminChunkWrapper(**{
#                # Using get_for_id to ensure that proxy models etc are handled nicely.
#                # Even under Django < 1.5
#                'opts': ContentType.objects.get_for_id(x.chunk_content_type_id).model_class()._meta,
#                'namespace': site.app_name,
#                'region': name,
#                'content_type': ContentType.objects.get_for_model(content_object).pk,
#                'content_id': content_object.pk,
#                'obj': x,
#            }) for x in get_chunks_for_region(content_id=content_object.pk, region=name)]
#            context.update({
#                'should_display_toolbar': True,
#                'app_list': ['aaaa'],
#                'region_name': get_pretty_region_name(name),
#                'available_chunks': available_chunks,
#                'existing_chunks': existing_chunks,
#            })
        return context
register.tag(name='render_adminlinks_editregion',
             compile_function=EditRegionToolbar)
