# -*- coding: utf-8 -*-
from django.core.exceptions import ImproperlyConfigured


def render_one_chunk(context, chunk, renderer=None):
    # we could just let the errors bubble up, but instead we'll provide more
    # helpful error messages than one might otherwise get (AttributeError for
    # no render_into_region, TypeError for calling render_into_region because of
    # it being unbound method (got RequestContext instance instead))
    if not hasattr(chunk, 'render_into_region'):
        raise ImproperlyConfigured('%r does not have a `render_into_region` method' % chunk)
    renderer = getattr(chunk, 'render_into_region')
    if not callable(renderer):
        raise ImproperlyConfigured('%r is not callable' % renderer)
    return renderer(context)


def render_one_summary(context, chunk, renderer=None):

    if hasattr(chunk, 'render_summary'):
        summary = getattr(chunk, 'render_summary')
        if not callable(summary):
            raise ImproperlyConfigured('%r is not callable' % summary)
        return summary(context)

    # if we don't have a render summary,
    # just show the chunk.
    return render_one_chunk(context, chunk, renderer)
