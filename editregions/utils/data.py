# -*- coding: utf-8 -*-
from contextlib import contextmanager
import logging
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.template.context import BaseContext, Context
from django.utils.functional import SimpleLazyObject
from django.conf import settings
try:
    from django.utils.six import string_types
except ImportError:
    string_types = basestring,
from adminlinks.templatetags.utils import get_admin_site

logger = logging.getLogger(__name__)


def get_model_class(obj):
    """
    compatibility layer over the fact get_model is internal and could go away
    in the future, which would require us switch over to using contenttypes.

    :param obj: a model instance
    :return: an installed model class, or None.

    .. testcase:: GetModelClassTestCase
    """
    return get_content_type(obj).model_class()


def get_content_type(input):
    """
    :param input:
    :return: the matching content type
    :rtype: ContentType

    .. testcase:: GetContentTypeTestCase
    """
    if hasattr(input, '_meta'):
        logger.info('Input is a Django model, using `get_for_model`')
        return ContentType.objects.get_for_model(input)

    if isinstance(input, string_types) and input.count('.') == 1:
        logger.info('Input is a dotted string "appname.ModelName", splitting '
                    'into component parts for lookup `get_by_natural_key`')
        parts = tuple(input.split('.')[0:2])
        try:
            return ContentType.objects.get_by_natural_key(
                app_label=parts[0].lower(), model=parts[1].lower())
        except ContentType.DoesNotExist as e:
            # give a clearer indication wtf went wrong.
            msg = 'Unable to find ContentType for app: %s, model: %s' % parts
            e.args = (msg,) + e.args[1:]
            raise
    logger.info('Input failed previous tests, assumed to be a ContentType `pk`')
    return ContentType.objects.get_for_id(input)


def get_modeladmin(obj, admin_namespace='admin'):
    """
    convienience function around finding the modeladmin we want.
    Allows us to provide a class or instance and get back the modeladmin.

    .. testcase:: GetModelAdminTestCase
    """
    model = get_model_class(obj)
    admin = get_admin_site(admin_namespace)
    try:
        return admin._registry[model]
    except KeyError as e:
        if settings.DEBUG:
            msg = '{key} not found in {admin}'.format(key=e.args[0],
                                                      admin=admin.__class__)
            raise ImproperlyConfigured(msg)
        raise
    # except AttributeError <= could happen, but wtf should I do then, it's
    # unrecoverable ...?


def attach_configuration(obj, config_class):
    """
    .. testcase:: AttachConfigurationTestCase
    """
    created = False
    if not hasattr(obj, '__editregion_config'):
        logger.debug('__editregion_config not on {cls!r} for this template '
                     'rendering request, creating it'.format(cls=obj))

        def _generate_config():
            return config_class(obj)

        config = SimpleLazyObject(_generate_config)
        setattr(obj, '__editregion_config', config)
        created = True
    return obj, created


def get_configuration(obj):
    """
    .. testcase:: GetConfigurationTestCase
    """
    return getattr(obj, '__editregion_config', None)


@contextmanager
def healed_context(context):
    """
    .. testcase:: HealedContextTestCase
    """
    if not isinstance(context, BaseContext):
        context = Context(context)
    original_context_length = len(context.dicts)
    yield context
    ctx_length = len(context.dicts)
    while ctx_length > 1 and ctx_length > original_context_length:
        logger.debug('Removing excess context dicts (target size {0},'
                     'working size {1})'.format(original_context_length,
                                               ctx_length))
        context.pop()
        ctx_length = len(context.dicts)
