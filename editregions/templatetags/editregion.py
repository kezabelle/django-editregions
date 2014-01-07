# -*- coding: utf-8 -*-
import logging
from copy import copy
from classytags.helpers import AsTag
from django import template
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from classytags.core import Options
from classytags.arguments import Argument, StringArgument, Flag
from django.utils.html import strip_tags
from django.core.exceptions import ImproperlyConfigured
from editregions.models import EditRegionChunk, EditRegionConfiguration
from editregions.text import ttag_no_obj, ttag_not_model, ttag_no_ancestors
from editregions.utils.regions import validate_region_name
from editregions.utils.data import (get_content_type, get_modeladmin,
                                    attach_configuration, get_configuration)


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
            return self.get_tag(context, name, content_object, inherit,
                                **kwargs)

    def get_content_type(self, content_object):
        """
        Try and get the ContentType for the given object, and in
        DEBUG showing an appropriate error message, while in production just
        logging it for subscribers and moving on.
        """
        try:
            return get_content_type(content_object)
        except ContentType.DoesNotExist:
            # the model doesn't exist in the content types table. I don'
            #  know why.
            if settings.DEBUG:
                raise
            logger.error(
                'content object does not exist for {cls!r}'.format(
                    cls=content_object))
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
            logger.error(error)
            return None

    def get_value(self, context, name, content_object, inherit, **kwargs):
        content_type = self.get_content_type(content_object)
        if content_type is None:
            return ()

        # cache on the object so that showing the first editregion does the
        # configuration request, and additional ones re-use the config found.
        attach_configuration(content_object, EditRegionConfiguration)
        erc = get_configuration(content_object)

        results = erc.fetch_chunks_for(region=name)
        chunks = list(EditRegionTag.render_all_chunks(erc.template, context,
                                                      name, results))

        if inherit and len(chunks) < 1:
            # make sure we have the damn method we need.
            try:
                parents = content_object.get_ancestors()
            except AttributeError as e:
                # doesn't have ancestors conforming to the mptt/treebeard
                # API, so it's probably a custom model that is BROKEN.
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
                parent_results = EditRegionChunk.polymorphs.filter(
                    content_id=parent.pk,
                    content_type=self.get_content_type(parent),
                    region=name).select_subclasses()
                chunks = list(EditRegionTag.render_all_chunks(erc.template,
                                                              context, name,
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

    @staticmethod
    def render_one_chunk(context, chunk, renderer=None):
        # we could just let the errors bubble up, but instead we'll provide more
        # helpful error messages than one might otherwise get (AttributeError for
        # no render_into_region, TypeError for calling render_into_region because of
        # it being unbound method (got RequestContext instance instead))
        if renderer is None:
            logger.debug('No renderer given as an argument, fetching the '
                         'ModelAdmin instance for the first time')
            renderer = get_modeladmin(chunk)
        if not hasattr(renderer, 'render_into_region'):
            raise ImproperlyConfigured('%r does not have a `render_into_region` method' % renderer.__class__)
        return renderer.render_into_region(context=context, obj=chunk)

    @staticmethod
    def render_one_summary(context, chunk, renderer=None):
        if renderer is None:
            logger.debug('No renderer given as an argument, fetching the '
                         'ModelAdmin instance for the first time')
            renderer = get_modeladmin(chunk)
        if hasattr(renderer, 'render_into_summary'):
            logger.debug('ModelAdmin instance has a `render_into_summary` method, '
                         'using it in preference to the `render_one_chunk` fallback')
            return renderer.render_into_summary(context=context, obj=chunk)
        return strip_tags(EditRegionTag.render_one_chunk(context, chunk, renderer))

    @staticmethod
    def render_all_chunks(template, context, region, found_chunks):
        """

        :used by:
            :class:`~editregions.templatetags.editregion.EditRegionTag`
        """
        logger.info('Rendering %(renderable)d of %(possible)d chunks' % {
            'renderable': len(found_chunks),
            'possible': len(found_chunks),
        })

        # In the future, it'd be nice to be able to just use the existing context and
        # do context.push()/pop() ... but we can't, because otherwise nothing
        # shows up in debug_toolbar, because Context() has no items() attribute.
        # See https://code.djangoproject.com/ticket/20287#ticket
        # LAME.
        original_context_length = len(context.dicts)
        for index, chunk in enumerate(found_chunks):
            # new_context = convert_context_to_dict(context)
            context.update(EditRegionTag.chunk_iteration_context(index,
                                                                 chunk,
                                                                 found_chunks))
            output = EditRegionTag.render_one_chunk(context, chunk)
            # heal the context back to it's state prior to our fiddling with it
            ctx_length = len(context.dicts)
            while ctx_length > 1 and ctx_length > original_context_length:
                logger.debug('Removing excess context dicts.')
                context.pop()
                ctx_length = len(context.dicts)
            # a chunk may return None if the ModelAdmin responsible for
            # rendering it doesn't implement the correct methods (instead raising
            # a warning to stderr), so we screen it all here.
            if output is not None:
                yield output

    @staticmethod
    def chunk_iteration_context(index, value, iterable):
        """
        Each time we render a chunk, we should also inject an additional set of
        context items.

        Returns a tuple of the key name to use, and the dictionary of values to
        put into it.

        .. testcase: ChunkContextTestCase
        """
        index_plus = index + 1
        index_minus = index - 1
        plugin_count = len(iterable)
        plugin_context = {
            'counter0': index,
            'counter': index_plus,
            'revcounter': plugin_count - index,
            'revcounter0': (plugin_count - index) - 1,
            'first': index == 0,
            'last': index == (plugin_count - 1),
            'total': plugin_count,
            'region': value.region,
            'remaining_plugins': iterable[index_plus:],
            'used_plugins': iterable[:index],
            'object': value,
            'previous_plugin': None,
            'previous': None,
            'previous0': None,
            'next_plugin': None,
            'next': None,
            'next0': None,
        }

        try:
            assert index_minus >= 0
            plugin_context.update(
                previous_plugin=iterable[index_minus],
                previous=index,
                previous0=index_minus,
            )
        except AssertionError:
            # If `index_minus` is less than 0, we want to change values, because
            # minus numbers will still retrieve things from the `iterable`, only
            # from the other end.
            # Should be the first iteration, so no previous can exist.
            pass

        try:
            plugin_context.update(
                next_plugin=iterable[index_plus],
                next=index_plus,
                next0=index
            )
        except IndexError:
            # Unable to get anything from `plugins` at position `index`.
            # Should be the last iteration, so there can be no next.
            pass

        return {'chunkloop': plugin_context}
register.tag(EditRegionTag.name, EditRegionTag)
