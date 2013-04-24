# -*- coding: utf-8 -*-
import logging
from django.core.exceptions import ValidationError
from django.core.handlers.base import BaseHandler
from django.contrib.auth.models import AnonymousUser
from django.db.models.loading import get_model
from django.template.loader import render_to_string
from django.utils.datastructures import SortedDict
import re
from django.template.context import Context, get_standard_processors
from django.test.client import RequestFactory
from django.core.validators import RegexValidator, slug_re, MaxLengthValidator
from django.utils.translation import ugettext_lazy as _
from editregions.constants import EDIT_REGIONS

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

def get_pretty_region_name(name, settings=None):
    """
    Try and find a not-machine-oriented name for this region, potentially
    localized. If none exists, use the given regular expression to provide
    a poor facsimile.

    .. testcase: PrettyNameTestCase
    """
    if settings is None:
        settings = EDIT_REGIONS
    try:
        return settings[name]['name']
    except KeyError:
        logbits = {'region': name}
        logger.debug(u'No declared name for "%(region)s" in your EDIT_REGIONS '
                     u'setting, falling back to using a regular expression' % logbits)
        return re.sub(fallback_region_name_re, string=name, repl=' ')

def get_enabled_chunks_for_region(name, settings=None):
    """
    Get the list of available chunks. This allows chunks to exist in the database
    but get turned off after the fact, without deleting them.

    Returns an dictionary like object (specifically, a `SortedDict`) whose
    keys are the actual models, rather than dotted paths, and whose values are the
    counts for each chunk.
    """
    if settings is None:
        settings = EDIT_REGIONS
    resolved = SortedDict()
    if name in settings.keys():
        # Replace the dotted app_label/model_name combo with the actual model.
        for chunk, count in settings[name]['chunks'].items():
            chunked = chunk.split('.')[0:2]
            model = get_model(*chunked)
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

#: String used for finding regions in the rendered down template.
#: Used by :class:`~editregions.templatetags.editregion.EditRegionTag` if the
#: :attr:`~editregions.utils.regions.fake_context_payload` is found.
region_comment = r'<!-- region:%s -->'

#: the region finding string, compiled down into a regular expression for
#: efficient searching.
region_comment_re = re.compile(region_comment % '([-\w]+)')

#: value put into the context if we're rendering down a template for scanning
#: Used by :class:`~editregions.templatetags.editregion.EditRegionTag`
fake_context_payload = u'scanning_for_regions'


class FakedRequestContext(Context):
    """
    When scanning a template for placeholders, we don't want to invoke a real
    request, or a full RequestContext because it may be really expensive,
    especially if uncached. Additionally, we want to provide a get-out-clause
    for template tags to return without doing any work.
    As such, we create a fake User, and put a special key in the context for
    template tags to test.
    """

    def _fake_user_factory(self):
        return AnonymousUser()

    def __init__(self, path, *args, **kwargs):
        super(FakedRequestContext, self).__init__(*args, **kwargs)
        req = RequestFactory().get(path)
        handler = BaseHandler()
        handler.load_middleware()

        # handlers which might affect the incoming request.
        for middleware_method in handler._request_middleware:
            response = middleware_method(req)
            if response is not None:
                break

        # all context processors which are defaults.
        for processor in get_standard_processors():
            self.update(processor(req))
        self.update({
            'request': req,
            fake_context_payload: True
        })


def scan_template_for_named_regions(template_name, request_path='/'):
    given_context = {}
    fake_context = FakedRequestContext(path=request_path)
    compiled_template = render_to_string(template_name, given_context, fake_context)
    return region_comment_re.findall(compiled_template)


def sorted_regions(items):
    """
    Yes, this is just a one line function, but frankly I'll never remember how
    to do this otherwise.

    This is a bit laborious, but we want to (by default) display plugin managers
    in the order in which we find them in the template. Additionally, we want to
    screen for duplicates. That combination of requirements rules out a set,
    hence the conversion to a sorted dictionary and back to a list.

    .. testcase: SortedRegionsTestCase
    """
    return list(SortedDict.fromkeys(items))

