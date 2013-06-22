# -*- coding: utf-8 -*-
import logging
from django import template
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from classytags.core import Tag, Options
from classytags.arguments import Argument, StringArgument
from django.core.exceptions import ImproperlyConfigured
from editregions.models import EditRegionChunk
from editregions.text import ttag_no_obj, ttag_not_model
from editregions.utils.chunks import get_chunks_for_region, render_all_chunks
from editregions.utils.regions import (validate_region_name,
                                       get_first_valid_template)
from editregions.utils.data import get_content_type

register = template.Library()
logger = logging.getLogger(__name__)


class EditRegionTag(Tag):
    """
    Output the contents of a region in a region group::

        {% load editregion %}
        {% editregion 'region_name' object %}

    Note that if no object is provided in debug mode,
    the tag will raise an ImproperlyConfigured exception and expect you to fix it.
    In production (DEBUG=False) it will avoid raising that and should hopefully
    return nothing if something goes wrong.

    .. note::
        This is a bit slow, without the cached template loader being used.
        Needs addressing - periodically see if we can improve it according to
        django-debug-toolbar-template-timings.
    """
    model = EditRegionChunk
    options = Options(
        StringArgument('name', required=True, resolve=True),
        Argument('content_object', required=True, default=None, resolve=True),
    )

    def render_tag(self, context, name, content_object, **kwargs):
        validate_region_name(name)
        # if we're in a fake request to this template, assume we're scanning
        # for placeholders, and set the appropriate string to read back.

        _tag_name = 'editregion'

        # somehow, a None got through. Interesting.
        if content_object is None:
            error = ttag_no_obj % {
                'tagname': _tag_name,
                'region': name,
            }
            if settings.DEBUG:
                raise ImproperlyConfigured(error)
            else:
                logger.error(error)

        try:
            content_type = get_content_type(content_object)
        except ContentType.DoesNotExist:
            # the model doesn't exist in the content types table. I don'
            #  know why.
            logger.error('content object does not exist')
            return u''
        except AttributeError:
            # we didn't get a proper django model, but something has definitely
            # been passed in, because the earlier None sentinel didn't catch it.
            error = ttag_not_model % {
                'tagname': _tag_name,
                'type': type(content_object).__name__
            }
            if settings.DEBUG:
                raise ImproperlyConfigured(error)
            else:
                logger.error(error)
            return u''

        results = get_chunks_for_region(content_id=content_object.pk,
                                        content_type=content_type, region=name)
        templates = content_object.get_region_groups()
        template = get_first_valid_template(templates)
        # if it's being used as an `as x` output tag,
        # return the unjoined list.
        #if kwargs.pop(self.varname_name):
        #    return render_all_chunks(context, name, results)
        return u'\n'.join(render_all_chunks(template, context, name, results))
register.tag('editregion', EditRegionTag)
