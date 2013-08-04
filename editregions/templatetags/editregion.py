# -*- coding: utf-8 -*-
import logging
from classytags.helpers import AsTag
from django import template
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from classytags.core import Options
from classytags.arguments import Argument, StringArgument, Flag
from django.core.cache import cache, DEFAULT_CACHE_ALIAS
from django.core.exceptions import ImproperlyConfigured
from editregions.constants import RENDERED_CACHE_KEY
from editregions.models import EditRegionChunk
from editregions.text import ttag_no_obj, ttag_not_model, ttag_no_ancestors
from editregions.utils.chunks import get_chunks_for_region, render_all_chunks
from editregions.utils.regions import (validate_region_name,
                                       get_first_valid_template)
from editregions.utils.data import get_content_type

register = template.Library()
logger = logging.getLogger(__name__)


class EditRegionTag(AsTag):
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
    name = 'editregion'
    options = Options(
        StringArgument('name', required=True, resolve=True),
        Argument('content_object', required=True, default=None, resolve=True),
        Flag('inherit', true_values=['inherit'], case_sensitive=False,
             default=False),
        'as', Argument('output_var', required=False, default=None, resolve=False)
    )

    def render_tag(self, context, name, content_object, inherit, **kwargs):
        validate_region_name(name)
        # somehow, a None got through. Interesting.
        if content_object is None:
            error = ttag_no_obj % {
                'tagname': self.name,
                'region': name,
            }
            logger.error(error)
            if settings.DEBUG:
                raise ImproperlyConfigured(error)

        #: this is basically from the core :class:`~classytags.core.Tag`
        #: implementation but changed to allow us to have different output
        #: so that using it as an AS tag returns a *list* of chunks, while
        #: doing it as a normal tag just outputs a string.
        varname = kwargs.pop(self.varname_name)
        if varname:
            context[varname] = self.get_value(context, name, content_object,
                                              inherit, **kwargs)
            return ''
        else:
            return self.get_tag(context, name, content_object, inherit, **kwargs)

    def get_content_type(self, content_object):
        try:
            return get_content_type(content_object)
        except ContentType.DoesNotExist:
            # the model doesn't exist in the content types table. I don'
            #  know why.
            logger.error('content object does not exist')
            return None
        except AttributeError:
            # we didn't get a proper django model, but something has definitely
            # been passed in, because the earlier None sentinel didn't catch it.
            error = ttag_not_model % {
                'tagname': self.name,
                'type': type(content_object).__name__
            }
            if settings.DEBUG:
                raise ImproperlyConfigured(error)
            else:
                logger.error(error)
            return None

    def get_value(self, context, name, content_object, inherit, **kwargs):
        content_type = self.get_content_type(content_object)
        if content_type is None:
            return ()

        results = get_chunks_for_region(content_id=content_object.pk,
                                        content_type=content_type, region=name)
        templates = content_object.get_region_groups()
        template = get_first_valid_template(templates)
        # if it's being used as an `as x` output tag,
        # return the unjoined list.
        #if kwargs.pop(self.varname_name):
        #    return render_all_chunks(context, name, results)
        KEY = RENDERED_CACHE_KEY.format(content_type_id=content_type.pk,
                                        content_id=content_object.pk,
                                        region=name)
        chunks = cache.get(KEY, None)
        if chunks is None:
            logger.debug("key {key} was not found in the '{cache}' backend, "
                         "so we're polling the DB for chunks".format(key=KEY,
                         cache=DEFAULT_CACHE_ALIAS))
            chunks = list(render_all_chunks(template, context, name, results))

        if inherit:
            # make sure we have the damn method we need.
            try:
                parents = content_object.get_ancestors()
            except AttributeError as e:
                # doesn't have ancestors :(
                parents = ()
                error = ttag_no_ancestors % {
                    'obj': content_object.__class__.__name__,
                    'attr': 'get_ancestors',
                    'thing': inherit,
                }
                if settings.DEBUG:
                    raise ImproperlyConfigured(error)
                else:
                    logger.error(error)
            # if there are parents, see if we can get values from them.
            for parent in parents:
                parent_results = get_chunks_for_region(
                    content_id=parent.pk,
                    content_type=self.get_content_type(parent),
                    region=name)
                chunks = list(render_all_chunks(template, context, name,
                                                parent_results))
                if len(chunks) > 0:
                    # stop processing further, we found some results!
                    break
        return chunks

    def get_tag(self, context, name, content_object, inherit, **kwargs):
        results = self.get_value(context, name, content_object, inherit, **kwargs)
        if results is None:
            return u''

        return u'\n'.join(results)
register.tag(EditRegionTag.name, EditRegionTag)
