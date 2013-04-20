# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging
from adminlinks.templatetags.adminlinks_buttons import BaseAdminLink
from django import template
from django.contrib.contenttypes.models import ContentType
from django.http import QueryDict
from editregions.models import EditRegionChunk
from editregions.admin.utils import AdminChunkWrapper
from editregions.utils.regions import (validate_region_name,
                                       fake_context_payload,
                                       get_pretty_region_name)
from adminlinks.templatetags.utils import (get_admin_site, context_passes_test,
                                           _add_custom_link_to_context)
from classytags.arguments import StringArgument, Argument
from classytags.core import Options
from classytags.helpers import InclusionTag

register = template.Library()
logger = logging.getLogger(__name__)


class EditRegionToolbar(BaseAdminLink, InclusionTag):
    # This template being here allows us to override all adminlinks stuff in one
    # place, so while it's unconventional, because it's not in
    # 'editregions/adminlinks' I just don't care, it's useful.
    template = 'adminlinks/editregion_toolbar.html'

    options = Options(
        BaseAdminLink.base_options[0],  # obj
        StringArgument('region_name', required=True, resolve=False),
        StringArgument('admin_site', required=False, default='admin'),
        Argument('querystring', required=False, default='pop=1'),
    )

    def get_context(self, context, obj, region_name, admin_site, querystring):
        """
        ..todo:: document

        Always returns the existing context.
        """
        validate_region_name(region_name)

        if not self.is_valid(context, obj):
            return context

        site = get_admin_site(admin_site)
        if site is None:
            logger.debug('Invalid admin site')
            return context

        link = _add_custom_link_to_context(admin_site, context['request'],
                                           EditRegionChunk._meta, 'change',
                                           'changelist', None, query=querystring)
        # just using the existance of link as a guard to ensure permissions
        # checked out and the admin is loaded.
        if link['link']:
            querystring = QueryDict(querystring)
            wrapped = AdminChunkWrapper(opts=EditRegionChunk._meta,
                                        namespace=site.name,
                                        content_id=obj.pk,
                                        content_type=ContentType.objects.get_for_model(obj),
                                        region=region_name)
            wrapped.querydict.update(querystring)
            # replace the default values with our own, better ones :\
            link.update(link=wrapped.get_manage_url(),
                        verbose_name=get_pretty_region_name(region_name))
        context.update(link)
        return context
register.tag(name='render_adminlinks_editregion',
             compile_function=EditRegionToolbar)
