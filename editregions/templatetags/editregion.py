# -*- coding: utf-8 -*-
from collections import namedtuple
from itertools import chain
import logging
from classytags.helpers import AsTag
from django import template
from django.conf import settings
from django.contrib.admin.sites import NotRegistered
from django.contrib.contenttypes.models import ContentType
from classytags.core import Options
from classytags.arguments import Argument, StringArgument, Flag
from django.utils.html import strip_tags
from django.core.exceptions import ImproperlyConfigured
import operator
from editregions.models import EditRegionChunk, EditRegionConfiguration
from editregions.text import ttag_no_obj, ttag_not_model
from editregions.utils.regions import validate_region_name
from editregions.utils.data import (get_content_type, get_modeladmin,
                                    attach_configuration, get_configuration,
                                    healed_context, RegionMedia)


register = template.Library()
logger = logging.getLogger(__name__)


IterationData = namedtuple('IterationData', [
    'counter0', 'counter', 'revcounter', 'revcounter0', 'first', 'last',
    'total', 'region', 'remaining', 'used', 'object',  'previous_chunk',
    'previous', 'previous0', 'next_chunk', 'next', 'next0'])


def render_one_chunk(context, chunk, extra, renderer=None):
    # we could just let the errors bubble up, but instead we'll provide more
    # helpful error messages than one might otherwise get (AttributeError for
    # no render_into_region, TypeError for calling render_into_region because of
    # it being unbound method (got RequestContext instance instead))
    if renderer is None:
        logger.debug('No renderer given as an argument, fetching the '
                     'ModelAdmin instance for the first time')
        renderer = get_modeladmin(chunk)
    if not hasattr(renderer, 'render_into_region'):
        msg = ('{0.__class__!r} does not have a `render_into_region` '
               'method'.format(renderer))
        raise ImproperlyConfigured(msg)
    return renderer.render_into_region(context=context, obj=chunk,
                                       extra=extra)


def render_one_mediagroup(context, chunk, extra, renderer=None):
    # we could just let the errors bubble up, but instead we'll provide more
    # helpful error messages than one might otherwise get (AttributeError for
    # no render_into_region, TypeError for calling render_into_region because of
    # it being unbound method (got RequestContext instance instead))
    if renderer is None:
        logger.debug('No renderer given as an argument, fetching the '
                     'ModelAdmin instance for the first time')
        renderer = get_modeladmin(chunk)
    if hasattr(renderer, 'render_into_mediagroup'):
        return renderer.render_into_mediagroup(context=context, obj=chunk,
                                               extra=extra)
    return None


def chunk_iteration_context(index, value, iterable):
    """
    Each time we render a chunk, we should also inject an additional set of
    context items.

    Returns a dictionary whose key gets put into context, and whose values
    are a namedtuple available to render_into_<region|summary> methods,
    as well as template instances.
    """
    index_plus = index + 1
    index_minus = index - 1
    count = len(iterable)
    iterdata = {
        'counter0': index,
        'counter': index_plus,
        'revcounter': count - index,
        'revcounter0': (count - index) - 1,
        'first': index == 0,
        'last': index == (count - 1),
        'total': count,
        'region': getattr(value, 'region', None),
        'remaining': iterable[index_plus:],
        'used': iterable[:index],
        'object': value,
        'previous_chunk': None,
        'previous': None,
        'previous0': None,
        'next_chunk': None,
        'next': None,
        'next0': None,
    }

    try:
        assert index_minus >= 0
        iterdata.update(
            previous_chunk=iterable[index_minus],
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
        iterdata.update(
            next_chunk=iterable[index_plus],
            next=index_plus,
            next0=index
        )
    except IndexError:
        # Unable to get anything from `plugins` at position `index`.
        # Should be the last iteration, so there can be no next.
        pass

    return {'chunkloop': IterationData(**iterdata)}


def render_all_chunks(context, found_chunks, iter_func=chunk_iteration_context,
                      render_func=render_one_chunk):
    logger.info('Rendering {0} chunks'.format(len(found_chunks)))
    for index, chunk in enumerate(found_chunks):
        # new_context = convert_context_to_dict(context)
        with healed_context(context) as new_ctx:
            iteration = iter_func(index=index, value=chunk,
                                  iterable=found_chunks)
            new_ctx.update(iteration)
            output = render_func(context=new_ctx, chunk=chunk, extra=iteration)
        # a chunk may return None if the ModelAdmin responsible for
        # rendering it doesn't implement the correct methods (instead
        # raising a warning to stderr), so we screen it all here.
        if output is not None:
            yield output


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

    def do_validate(self, region_name, content_object):
        validate_region_name(region_name)
        # somehow, a None got through. Interesting.
        if content_object is None:
            error = ttag_no_obj % {
                'tagname': self.name,
                'region': region_name,
            }
            logger.error(error)
            if settings.DEBUG:
                raise ImproperlyConfigured(error)
            return False
        return True

    def render_tag(self, context, name, content_object, inherit, **kwargs):
        is_valid = self.do_validate(region_name=name,
                                    content_object=content_object)
        if not is_valid:
            return ''

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
            logger.exception(
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
            logger.exception(error)
            return None
        except ValueError:
            error = "content_object was probably '', check the context provided"
            if settings.DEBUG:
                raise ValueError(error)
            logger.exception(error)
            return None

    def do_render(self, context, results):
        return render_all_chunks(context=context, found_chunks=results,
                                 render_func=render_one_chunk)

    def fetch(self, config, region):
        """
        Ask a EditRegionConfiguration (or similar ``config``) for the chunks
        as appropriate, either by region or in totality.

        Most of the time, ``region`` is pre-validated to not be blank
        (see do_validate), so the second return is the preferred one
        """
        if not region:
            # this may be triggered by subclasses which need to get all
            # chunk values, not just a specific region's. See the media tags.
            return tuple(chain.from_iterable(config.fetch_chunks().values()))
        # this is the prefered one.
        return config.fetch_chunks_for(region=region)

    def get_value(self, context, name, content_object, inherit, **kwargs):
        content_type = self.get_content_type(content_object)
        if content_type is None:
            return ()

        # cache on the object so that showing the first editregion does the
        # configuration request, and additional ones re-use the config found.
        attach_configuration(content_object, EditRegionConfiguration)
        erc = get_configuration(content_object)
        results = self.fetch(erc, region=name)
        chunks = tuple(self.do_render(context, results))
        if inherit and len(chunks) < 1:
            chunks = self.get_ancestors_instead(context, name, content_object)
        return chunks

    def get_ancestors_instead(self, context, region_name, content_object):
        # make sure we have the damn method we need.
        try:
            parents = content_object.get_ancestors()
        except AttributeError as e:
            parents = None
        if parents is None:
            try:
                modeladmin = get_modeladmin(content_object)
                parents = modeladmin.get_ancestors(obj=content_object)
            except (NotRegistered, AttributeError) as e:
                # parents will remain None
                pass
        if parents is None:
            # doesn't have ancestors conforming to the mptt/treebeard
            # API, so it's probably a custom model that is BROKEN.
            error = ("{cls!r}, or the ModelAdmin for it, should implement "
                     "`get_ancestors` to use the 'inherit' argument for "
                     "this template tag".format(
                         cls=content_object.__class__))
            if settings.DEBUG:
                raise ImproperlyConfigured(error)
            logger.error(error, exc_info=1)
            return ()

        # if there are parents, see if we can get values from them.
        for distance, parent in enumerate(reversed(parents), start=1):
            attach_configuration(parent, EditRegionConfiguration)
            parent_erc = get_configuration(parent)
            parent_results = self.fetch(parent_erc, region=region_name)
            chunks = tuple(self.do_render(context, parent_results))
            chunk_count = len(chunks)
            if chunk_count > 0:
                logging.info("Found {1} chunks after {0} iterations over "
                             "objects in `get_ancestors`".format(
                                 distance, chunk_count))
                # stop processing further, we found some results!
                return chunks
        logging.debug("Inheriting from an ancestor yielded nothing")
        return ()

    def get_tag(self, context, name, content_object, inherit, **kwargs):
        results = self.get_value(context, name, content_object, inherit, **kwargs)
        if results is None:
            return u''
        return u'\n'.join(results)
register.tag(EditRegionTag.name, EditRegionTag)


class EditRegionMediaTag(EditRegionTag):
    def do_render(self, context, results):
        the_media = RegionMedia()
        for datadict in render_all_chunks(context=context,
                                          found_chunks=results,
                                          render_func=render_one_mediagroup):
            if datadict is not None:
                for position, values in datadict.items():
                    for value in values:
                        the_media.add(position, value)
        namespace, sep, attr = self.name.partition('_')
        return getattr(the_media, attr)

    def do_validate(self, region_name, content_object):
        if region_name:
            validate_region_name(region_name)
        # somehow, a None got through. Interesting.
        if content_object is None:
            error = ttag_no_obj % {
                'tagname': self.name,
                'region': region_name,
            }
            logger.error(error)
            if settings.DEBUG:
                raise ImproperlyConfigured(error)
            return False
        return True


class EditRegionTop(EditRegionMediaTag):
    name = 'editregion_top'
register.tag(EditRegionTop.name, EditRegionTop)


class EditRegionBottom(EditRegionMediaTag):
    name = 'editregion_bottom'
register.tag(EditRegionBottom.name, EditRegionBottom)
