# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging
import os
import re
from django.conf import settings
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db.models.loading import get_model
from django.template.loader import select_template
from django.template.context import Context
from django.utils.datastructures import SortedDict
from django.utils import simplejson as json
from django.core.validators import RegexValidator, slug_re, MaxLengthValidator
from django.utils.translation import ugettext_lazy as _
from editregions.constants import EDIT_REGIONS

logger = logging.getLogger(__name__)

validate_region_name_error = _('Enter a valid region name consisting of '
                               'letters, numbers, underscores and hyphens.')

region_name_startswith = _('Region names may not begin with "_"')
region_name_endswith = _('Region names may not end with "_"')

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

    :testcase: `~editregions.tests.utils.RegionNameValidationTestCase`
    """
    if name.startswith('_'):
        raise ValidationError(region_name_startswith)
    if name.endswith('_'):
        raise ValidationError(region_name_endswith)
    MaxLengthValidator(75)(name)
    validate_region_re(name)
    return True

################################################################################
################################################################################
################################################################################
################################################################################
################################################################################
################################################################################
################################################################################
################################################################################
# GET RID OF ALL OF THESE!
################################################################################
################################################################################
################################################################################
################################################################################
################################################################################
################################################################################
################################################################################
################################################################################

# When there's no 'name' in the EDIT_REGIONS dictionary for a given edit region
# fall back to using a regular expression to prettify it.
fallback_region_name_re = re.compile(r'[_\W]+')


def get_first_valid_template(template_names):
    """
    Given a bunch of templates (tuple, list), find the first one in the
    settings dictionary. Assumes the incoming template list is ordered in
    discovery-preference order.
    """
    if isinstance(template_names, basestring):
        template_names = (template_names,)

    discovered = select_template('%s.json' % os.path.splitext(x)[0]
                                 for x in template_names)
    return discovered


def get_template_region_configuration(template):
    rendered_template = template.render(Context())
    parsed_template = json.loads(rendered_template)
    for key, config in parsed_template.items():
        if 'models' in parsed_template[key]:
            parsed_template[key]['models'] = get_enabled_chunks_for_region(parsed_template[key]['models'])
    return parsed_template


def get_regions_for_template(template):
    """
    Given a single template (using get_first_valid_template()), find all
    regions provided to it.
    """
    return (x for x in get_template_region_configuration(template))


def get_pretty_region_name(template, name, editable_regions=None):
    """
    Try and find a not-machine-oriented name for this region, potentially
    localized. If none exists, use the given regular expression to provide
    a poor facsimile.
    """
    try:
        return get_template_region_configuration(template)[name]['name']
    except (KeyError, IndexError) as e:
        # KeyError = settings['whatever'] wasn't in the settings conf
        # IndexError = doing [0] on the list didn't yield anything; so no valid
        # region was found.
        logbits = {'region': name}
        logger.debug('No declared name for "%(region)s" in your EDIT_REGIONS '
                     'setting, falling back to using a regular expression' % logbits)
        return re.sub(fallback_region_name_re, string=name, repl=' ')


def get_enabled_chunks_for_region(model_mapping):
    """
    Get the list of available chunks. This allows chunks to exist in the database
    but get turned off after the fact, without deleting them.

    Returns an dictionary like object (specifically, a `SortedDict`) whose
    keys are the actual models, rather than dotted paths, and whose values are the
    counts for each chunk.
    """
    resolved = SortedDict()
    # Replace the dotted app_label/model_name combo with the actual model.
    for chunk, count in model_mapping.items():
        model = get_model(*chunk.split('.')[0:2])
        # Once we have a model and there's no stupid limit set,
        # add it to our new data structure.
        # Note that while None > 0 appears correct,
        # it isn't because None is a special value for infinite.
        if model is not None and (count is None or count > 0):
            resolved.update({model: count})
        if model is None:
            msg = 'Unable to load model "{cls}"'.format(cls=chunk)
            if settings.DEBUG:
                raise ObjectDoesNotExist(msg)
            logger.error(msg)
    if len(resolved) == 0:
        logger.debug('No chunks types found for "%(region)s"' % {'region': name})
    return resolved


def discover_template_and_configuration(template_names):
    template = get_first_valid_template(template_names=template_names)
    config = get_template_region_configuration(template)
    for region_name in config:
        if 'name' not in config[region_name]:
            logbits = {'region': region_name}
            logger.debug('No declared name for "%(region)s" in configuration, '
                         'falling back to using a regular expression' % logbits)
            config[region_name]['name'] = re.sub(pattern=fallback_region_name_re,
                                                 string=region_name, repl=' ')
    return template, config
