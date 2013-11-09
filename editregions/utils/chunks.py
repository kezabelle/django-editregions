# -*- coding: utf-8 -*-
import logging
# from django.contrib.contenttypes.models import ContentType
# from django.core.exceptions import ImproperlyConfigured
# from django.db.models.fields.related import OneToOneField
from adminlinks.templatetags.utils import convert_context_to_dict
from editregions.utils.rendering import render_one_chunk
from editregions.models import EditRegionChunk
from editregions.utils.regions import get_enabled_chunks_for_region
from editregions.utils.data import get_content_type, get_model_class

logger = logging.getLogger(__name__)

def get_limits_for_chunk_in_region(region, chunk):
    """
    Try to figure out if this chunk type has a maximum limit in this region.
    Returns an integer or None.
    """
    limits = 1
    if limits is not None:
        try:
            return int(limits[chunk])
        except KeyError:
            # Nope, no limit for this chunk.
            # Skipping down to returning None
            pass
    return None


def get_chunks_for_region(**base_filters):
    """
    Mostly want to use content_id, content_type(_id) and region.

    .. seealso:: :class:`~editregions.templatetags.editregion.EditRegionTag`
    """
    logger.debug('Finding EditRegionChunk subclasses using %r' % base_filters)
    # import pdb; pdb.set_trace()
    # chunks = get_enabled_chunks_for_region(template=template, name=region)
    # qs = EditRegionChunk.polymorphs.filter(**base_filters)
    # # try and select everything
    # if not chunks:
    #     qs = qs.select_subclasses()
    # else:
    #     qs = qs.select_subclasses(*get_related_names_for_enabled_chunks(chunks))
    # return qs
    return EditRegionChunk.polymorphs.filter(**base_filters).select_subclasses()


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
        # 'object': value,
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


def render_all_chunks(template, context, region, found_chunks):
    """

    :used by:
        :class:`~editregions.templatetags.editregion.EditRegionTag`
    """
    enabled = get_enabled_chunks_for_region(template=template, name=region)
    # enabled_relateds = get_related_names_for_enabled_chunks(enabled)
    # found_chunks.select_subclasses(*enabled_relateds)
    # print(found_chunks.subclasses)
    # print(found_chunks.query.select_related)

    # filter our chunks which are no long enabled ...
    # this'll hit the ContentType cache after a while ...
    to_render = [x for x in found_chunks if get_model_class(x) in enabled]
    logger.info('Rendering %(renderable)d of %(possible)d chunks' % {
        'renderable': len(to_render),
        'possible': len(enabled),
    })
    del enabled
    # output = []

    # In the future, it'd be nice to be able to just use the existing context and
    # do context.push()/pop() ... but we can't, because otherwise nothing
    # shows up in debug_toolbar, because Context() has no items() attribute.
    # See https://code.djangoproject.com/ticket/20287#ticket
    # LAME.
    for index, chunk in enumerate(to_render):
        new_context = convert_context_to_dict(context)
        new_context.update(chunk_iteration_context(index, chunk, to_render))
        output = render_one_chunk(new_context, chunk)
        # a chunk may return None if the ModelAdmin responsible for
        # rendering it doesn't implement the correct methods (instead raising
        # a warning to stderr), so we screen it all here.
        if output is not None:
            yield output
        del index, chunk, output
    del to_render
