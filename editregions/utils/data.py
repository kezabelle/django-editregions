# -*- coding: utf-8 -*-
import logging
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
from adminlinks.templatetags.utils import get_admin_site

logger = logging.getLogger(__name__)


def queryset_to_attr_map(queryset, attr):
    output = {}
    for obj in queryset:
        result = getattr(obj, attr)
        output[result] = obj
    return output


def get_model_class(obj):
    """
    compatibility layer over the fact get_model is internal and could go away
    in the future, which would require us switch over to using contenttypes.

    :param obj: a model instance
    :return: an installed model class, or None.
    """
    return get_content_type(obj).model_class()


def get_content_type(input):
    if hasattr(input, '_meta'):
        logger.info('Input is a Django model, using `get_for_model`')
        return ContentType.objects.get_for_model(input)

    if isinstance(input, basestring) and input.count('.') == 1:
        logger.info('Input is a dotted string "appname.ModelName", splitting '
                    'into component parts for lookup `get_by_natural_key`')
        parts = tuple(input.split('.')[0:2])
        try:
            return ContentType.objects.get_by_natural_key(app_label=parts[0],
                                                          model=parts[1])
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
