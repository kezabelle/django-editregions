# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging
from adminlinks.templatetags.adminlinks_buttons import BaseAdminLink, _changelist_popup_qs
from django import template
from django.http import QueryDict
from editregions.models import EditRegionChunk
from editregions.admin.utils import AdminChunkWrapper
from editregions.utils.data import get_content_type
from editregions.utils.regions import (validate_region_name,
                                       get_pretty_region_name, get_first_valid_template)
from adminlinks.templatetags.utils import (get_admin_site,
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
        # StringArgument('region_name', required=True, resolve=True),
        StringArgument('admin_site', required=False, default='admin'),
        Argument('querystring', required=False, default=_changelist_popup_qs()),
    )

    def get_link_context(self, context, obj, admin_site, querystring):
        """
        ..todo:: document

        Always returns the existing context.
        """
        # validate_region_name(region_name)
        site = get_admin_site(admin_site)
        if site is None:
            logger.debug('Invalid admin site')
            return {}
        content_type = get_content_type(obj)
        link = _add_custom_link_to_context(admin_site, context['request'],
                                           EditRegionChunk._meta, 'change',
                                           'changelist', [content_type.pk, obj.pk],
                                           query=querystring)

        if link['verbose_name']:
            logger.debug('link created successfully, swapping out the '
                         '`verbose_name` available to the context')
            link['verbose_name'] = EditRegionChunk._meta.verbose_name_plural
            link['obj_name'] = obj._meta.verbose_name
        return link
register.tag(name='render_adminlinks_editregion',
             compile_function=EditRegionToolbar)
