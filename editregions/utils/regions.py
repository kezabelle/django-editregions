# -*- coding: utf-8 -*-
import logging
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db.models.loading import get_model
from django.utils.datastructures import SortedDict
import re
from django.core.validators import RegexValidator, slug_re, MaxLengthValidator
from django.utils.translation import ugettext_lazy as _
from editregions.constants import EDIT_REGIONS
from editregions.utils.data import get_model_class

logger = logging.getLogger(__name__)

validate_region_name_error = _(u'Enter a valid region name consisting of '
                               u'letters, numbers, underscores and hyphens.')

region_name_startswith = _(u'Region names may not begin with "_"')
region_name_endswith = _(u'Region names may not end with "_"')

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


# When there's no 'name' in the EDIT_REGIONS dictionary for a given edit region
# fall back to using a regular expression to prettify it.
fallback_region_name_re = re.compile(r'[_\W]+')


def get_first_valid_template(template_names, settings=None):
    """
    Given a bunch of templates (tuple, list), find the first one in the
    settings dictionary. Assumes the incoming template list is ordered in
    discovery-preference order.
    """
    settings = settings or EDIT_REGIONS
    if isinstance(template_names, basestring):
        template_names = (template_names,)
    for template in template_names:
        if template in settings:
            return template
    tried_templates = ', '.join(template_names)
    msg = 'None of the given templates (%s) is in the settings config.' % tried_templates
    raise KeyError(msg)


def get_regions_for_template(template, settings=None):
    """
    Given a single template (using get_first_valid_template()), find all
    regions provided to it.
    """
    settings = settings or EDIT_REGIONS
    return [x[0] for x in settings[template]]


def get_pretty_region_name(template, name, settings=None):
    """
    Try and find a not-machine-oriented name for this region, potentially
    localized. If none exists, use the given regular expression to provide
    a poor facsimile.

    .. testcase: PrettyNameTestCase
    """
    settings = settings or EDIT_REGIONS
    try:
        return [x[1] for x in settings[template] if x[0] == name][0]
    except KeyError:
        logbits = {'region': name}
        logger.debug(u'No declared name for "%(region)s" in your EDIT_REGIONS '
                     u'setting, falling back to using a regular expression' % logbits)
        return re.sub(fallback_region_name_re, string=name, repl=' ')


def get_enabled_chunks_for_region(template, name, given_settings=None):
    """
    Get the list of available chunks. This allows chunks to exist in the database
    but get turned off after the fact, without deleting them.

    Returns an dictionary like object (specifically, a `SortedDict`) whose
    keys are the actual models, rather than dotted paths, and whose values are the
    counts for each chunk.
    """
    if given_settings is None:
        given_settings = EDIT_REGIONS
    resolved = SortedDict()
    if template in given_settings:
        chunktypes = [x[2] for x in given_settings[template] if x[0] == name][0]
        # Replace the dotted app_label/model_name combo with the actual model.
        for chunk, count in chunktypes.items():
            model = get_model(*chunk.split('.')[0:2])
            # Once we have a model and there's no stupid limit set,
            # add it to our new data structure.
            # Note that while None > 0 appears correct,
            # it isn't because None is a special value for infinite.
            if model is not None and (count is None or count > 0):
                resolved.update({model: count})
            if model is None:
                logger.error(u'Unable to find model "%(chunk)s"' % {'chunk': chunk})
    if len(resolved) == 0:
        logger.debug(u'No chunks types found for "%(region)s"' % {'region': name})
    return resolved
