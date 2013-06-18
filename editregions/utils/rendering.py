# -*- coding: utf-8 -*-
import logging
from django.core.exceptions import ImproperlyConfigured
from editregions.utils.data import get_modeladmin

logger = logging.getLogger(__name__)


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
