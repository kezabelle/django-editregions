# -*- coding: utf-8 -*-
from classytags.arguments import Argument, StringArgument
from classytags.core import Options
from classytags.helpers import AsTag
from django import template
from editregions.models import EditRegionChunk
from editregions.utils.regions import (get_first_valid_template,
                                       get_regions_for_template)


register = template.Library()


class GetAllRegions(AsTag):
    """
    Allows the context to be populated with a `list` of regions for the
    current object. Useful if you need to automate output of the regions
    in order.
    """
    model = EditRegionChunk
    options = Options(
        Argument('content_object', required=True, default=None, resolve=True),
        'as', StringArgument('varname', resolve=False, required=False),
    )

    def get_value(self, context, content_object):
        templates = content_object.get_region_groups()
        template = get_first_valid_template(templates)
        return get_regions_for_template(template)
register.tag('get_regions_for', GetAllRegions)
