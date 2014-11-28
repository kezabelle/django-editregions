# -*- coding: utf-8 -*-
from contextlib import contextmanager
import logging
from collections import namedtuple
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.template.context import BaseContext, Context
try:
    from django.utils.encoding import force_text
except ImportError:
    from django.utils.encoding import force_unicode as force_text
from django.utils.functional import SimpleLazyObject
from django.conf import settings

try:
    from django.utils.six import string_types
except ImportError:  # pragma: no cover
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


class AppModel(namedtuple('AppModel', ['app_label', 'model'])):
    __slots__ = ()

    @property
    def app_label_natural_key(self):
        return self.app_label.lower()

    @property
    def model_natural_key(self):
        return self.model.lower()

    def __str__(self):
        return '{app!s}.{model!s}'.format(app=self.app_label, model=self.model)


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
        appmodel = AppModel._make(input.split('.')[0:2])
        try:
            return ContentType.objects.get_by_natural_key(
                app_label=appmodel.app_label_natural_key,
                model=appmodel.model_natural_key)
        except ContentType.DoesNotExist as e:
            # give a clearer indication wtf went wrong.
            msg = 'Unable to find ContentType for {0!s}'.format(appmodel)
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
    if not hasattr(obj, '__editregionconfig__'):
        logger.debug('__editregionconfig__ not on {cls!r} for this template '
                     'rendering request, creating it'.format(cls=obj))

        setattr(obj, '__editregionconfig__', config_class(obj))
        created = True
    return obj, created


def get_configuration(obj):
    """
    .. testcase:: GetConfigurationTestCase
    """
    return getattr(obj, '__editregionconfig__', None)


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


class RegionMedia(object):
    __slots__ = ('top', 'bottom')

    def __init__(self, top=None, bottom=None):
        self.top = []
        self.bottom = []
        # apply and de-duplicate params.
        if top is not None:
            for val in top:
                self.add_to_top(val)
        if bottom is not None:
            for val in bottom:
                self.add_to_bottom(val)

    def __repr__(self):
        return '<{mod}.{cls} top={top!r}, bottom={bottom!r}>'.format(
            mod=self.__module__, cls=self.__class__.__name__, top=self.top,
            bottom=self.bottom)

    def _asdict(self):
        return {'top': self.top, 'bottom': self.bottom}

    @classmethod
    def _make(cls, iterable):
        new_cls = cls()
        vals = tuple(iterable)
        new_cls.top = list(vals[0])
        new_cls.bottom = list(vals[1])
        return new_cls

    def __getitem__(self, name):
        if name not in ('top', 'bottom'):
            raise KeyError('{name} not available in {cls}'.format(
                name=name, cls=self.__class__.__name__))
        new_version = self.__class__()
        old_vals = getattr(self, name)[:]
        setattr(new_version, name, old_vals)
        return new_version

    def __nonzero__(self):
        return len(self.top) > 0 or len(self.bottom) > 0

    __bool__ = __nonzero__

    def __eq__(self, other):
        return self.top == other.top and self.bottom == other.bottom

    def __contains__(self, item):
        search_val = force_text(item).strip()
        return search_val in self.top or search_val in self.bottom

    def __len__(self):
        return len(self.top) + len(self.bottom)

    def add(self, position, data):
        existing = getattr(self, position)
        prepared_data = force_text(data).strip()
        if prepared_data not in existing:
            existing.append(prepared_data)
            return True
        return False

    def remove(self, position, data):
        existing = getattr(self, position)
        prepared_data = force_text(data).strip()
        if prepared_data in existing:
            existing.remove(prepared_data)
            return True
        return False

    def __add__(self, other):
        new_version = self.__class__()
        for field in ('top', 'bottom'):
            for side in (self, other):
                # copy my fields ...
                this_field = getattr(side, field, ())[:]
                for old_value in this_field:
                    new_version.add(field, old_value)
        return new_version

    # def render(self, position):
    #     return getattr(self, position)

    def add_to_top(self, data):
        return self.add('top', data)

    def add_to_bottom(self, data):
        return self.add('bottom', data)

    def remove_from_top(self, data):
        return self.remove('top', data)

    def remove_from_bottom(self, data):
        return self.remove('bottom', data)
