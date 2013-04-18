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
            if link['link']:
                wrapped = AdminChunkWrapper(opts=EditRegionChunk._meta,
                                            namespace=site.name,
                                            content_id=content_object.pk,
                                            content_type=ContentType.objects.get_for_model(content_object),
                                            region=name)
                # replace the default values with our own, better ones :\
                link.update(link=wrapped.get_manage_url(),
                            verbose_name=get_pretty_region_name(name))
            context.update(link)
        return context
register.tag(name='render_adminlinks_editregion',
             compile_function=EditRegionToolbar)
