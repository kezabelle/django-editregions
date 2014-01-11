# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, slug_re, MaxLengthValidator
from editregions.text import (validate_region_name_error,
                              region_name_startswith, region_name_endswith)

logger = logging.getLogger(__name__)

validate_region_re = RegexValidator(slug_re, validate_region_name_error,
                                    'invalid')


def validate_region_name(name):
    """
    This looks like it doubles up on model validation, which is true, but it
    also exists to ensure that at the point of usage in templates etc, the
    region name cannot violate the maximum length, and saves a trip to the database
    to lookup something horribly incorrect.

    :used by:
        :attr:`~editregions.models.EditRegionChunk.region`
        :meth:`~editregions.modeladmins2.EditRegionInline.get_region_name`
        :meth:`~editregions.templatetags.adminlinks_editregion.EditRegionToolbar.get_context`
        :meth:`~editregions.templatetags.editregion.EditRegionTag.render_tag`

    .. testcase:: ValidateRegionNameTestCase
    """
    if name.startswith('_'):
        raise ValidationError(region_name_startswith)
    if name.endswith('_'):
        raise ValidationError(region_name_endswith)
    MaxLengthValidator(75)(name)
    validate_region_re(name)
    return True
