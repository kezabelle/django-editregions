# -*- coding: utf-8 -*-
import logging
from copy import copy
from django.core.exceptions import ImproperlyConfigured
from editregions.utils.data import get_modeladmin

logger = logging.getLogger(__name__)


def render_all_chunks(template, context, region, found_chunks):
    """

    :used by:
        :class:`~editregions.templatetags.editregion.EditRegionTag`
    """
    # enabled = get_enabled_chunks_for_region(template=template, name=region)
    # enabled_relateds = get_related_names_for_enabled_chunks(enabled)
    # found_chunks.select_subclasses(*enabled_relateds)
    # print(found_chunks.subclasses)
    # print(found_chunks.query.select_related)

    # filter our chunks which are no long enabled ...
    # this'll hit the ContentType cache after a while ...
    # to_render = [x for x in found_chunks if get_model_class(x) in enabled]
    to_render = found_chunks
    logger.info('Rendering %(renderable)d of %(possible)d chunks' % {
        'renderable': len(to_render),
        'possible': len(to_render), #len(enabled),
    })
    # del enabled
    # output = []

    # In the future, it'd be nice to be able to just use the existing context and
    # do context.push()/pop() ... but we can't, because otherwise nothing
    # shows up in debug_toolbar, because Context() has no items() attribute.
    # See https://code.djangoproject.com/ticket/20287#ticket
    # LAME.
    for index, chunk in enumerate(to_render):
        # new_context = convert_context_to_dict(context)
        new_context = copy(context)
        new_context.update(chunk_iteration_context(index, chunk, to_render))
        output = render_one_chunk(new_context, chunk)
        # a chunk may return None if the ModelAdmin responsible for
        # rendering it doesn't implement the correct methods (instead raising
        # a warning to stderr), so we screen it all here.
        if output is not None:
            yield output
        del index, chunk, output
    del to_render


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


def render_one_summary(context, chunk, renderer=None):
    renderer = get_modeladmin(chunk)
    if hasattr(renderer, 'render_into_summary'):
        logger.debug('ModelAdmin instance has a `render_into_summary` method, '
                     'using it in preference to the `render_one_chunk` fallback')
        return renderer.render_into_summary(context=context, obj=chunk)
    return render_one_chunk(context, chunk, renderer)


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
