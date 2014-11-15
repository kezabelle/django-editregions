# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import functools
import logging
from django.core.exceptions import SuspiciousOperation, ValidationError
from django.core.urlresolvers import reverse, NoReverseMatch
try:
    from django.apps import apps
    get_app_config = apps.get_app_config
except ImportError:
    def get_app_config(path):
        return path
from django.forms import Media
from django.http import QueryDict
from django.utils.decorators import method_decorator, available_attrs
from django.utils.encoding import python_2_unicode_compatible, force_text
from editregions.constants import (REQUEST_VAR_REGION, REQUEST_VAR_ID,
                                   REQUEST_VAR_CT)
from editregions.utils.versioning import is_django_16plus
from editregions.utils.regions import validate_region_name
from editregions.models import EditRegionChunk
from adminlinks.templatetags.utils import MODELADMIN_REVERSE


logger = logging.getLogger(__name__)


def django_jqueryui_version():
    """
    .. testcase:: JQueryUIVersion
    """
    if is_django_16plus():
        return 'editregions/js/jquery.ui.1-10-3.custom.js'
    return 'editregions/js/jquery.ui.1-8-24.custom.js'

shared_media = Media(
    css={
        'screen': [
            'adminlinks/css/fancyiframe-custom.css',
            'editregions/css/inlines.css',
            'editregions/css/changelist-extras.css',
        ]
    },
    js=[
        'admin/js/jquery.rebind.js',
        'adminlinks/js/jquery.fancyiframe.js',
        django_jqueryui_version(),
        'editregions/js/dragging.js',
    ],
)


def guard_querystring(function):
    @functools.wraps(function, assigned=available_attrs(function))
    def wrapped(request, *args, **kwargs):
        fields_to_search = (REQUEST_VAR_CT, REQUEST_VAR_ID, REQUEST_VAR_REGION)
        fields = {}

        # By default, assume we're looking in the querystring; if it's a POST
        # request, fall back to looking in both GET and POST indiscriminately.
        lookup = request.GET
        if request.method.upper() == 'POST':
            lookup = request.REQUEST

        # Convert content type field into an integer, because that's what
        # Django uses internally.
        content_type = lookup.get(REQUEST_VAR_CT, 0)
        try:
            fields.update({REQUEST_VAR_CT: int(content_type)})
        except (ValueError, TypeError) as e:
            # ValueError: got string which was unconvertable to integer.
            # TypeError: got none, shut up!
            msg = 'Invalid parameter "content_type" with value: %s' % content_type
            logger.warning(msg, extra={'status_code': 405, 'request': request})

        # Content identifier can be anything as long as it isn't 0 and fits
        # within our DB storage max_length.
        content_id = str(lookup.get(REQUEST_VAR_ID, '0'))
        max_length = EditRegionChunk._meta.get_field_by_name(REQUEST_VAR_ID)[0].max_length
        if content_id != '0' and len(content_id) <= max_length:
            fields.update({REQUEST_VAR_ID: content_id})
        else:
            msg = 'Invalid parameter "content_id" with value: %s' % content_type
            logger.warning(msg, extra={'status_code': 405, 'request': request})

        # Our region gets validated using the same format we always use.
        regionval = lookup.get(REQUEST_VAR_REGION, '__error__')
        try:
            validate_region_name(regionval)
            fields.update({REQUEST_VAR_REGION: regionval})
        except ValidationError as e:
            # invalid region name
            logger.warning('Invalid region value: %s' % regionval,
                           extra={'status_code': 405, 'request': request})

        # if we didn't collect all the fields, or the values are falsy,
        # we want to mark that as an error.
        if len(fields) < 3 or not all(fields.values()):
            missing_params = [x for x in fields_to_search if x not in fields]
            msg = ', '.join(missing_params)
            msg += ' invalid for request'
            raise SuspiciousOperation(msg)
        else:
            return function(request, *args, **kwargs)
    return wrapped

guard_querystring_m = method_decorator(guard_querystring)


def get_app_config_verbose_name(app):
    try:
        return get_app_config(app).verbose_name
    except AttributeError:
        return app


@python_2_unicode_compatible
class AdminChunkWrapper(object):
    """
    Used through-out our admin customisations to wrap either the *idea* of
    an object, or the details about an actual object, in a single API.

    .. warning::
        passing `obj` in while assume that the object exists, and prefer its
        values over any others passed in. The absence of `obj` means you really
        need to provide `content_id`, `content_type` and `region`.
    """
    __slots__ = ['opts', 'admin_namespace', 'label', 'exists', 'chunk',
                 'content_type', 'content_id', 'region', 'module', 'url_parts',
                 'querydict', 'verbose_name']

    def __init__(self, opts, namespace, content_id=None, content_type=None,
                 region=None, obj=None):
        """

        :param opts: the `_meta` for resolving the admin view to call ...
                     should usually be :class:`~editregions.models.EditRegionChunk`
                     or a subclass.
        :param namespace: the admin site name
        :param content_id: The parent object id
        :param content_type: The parent object type
        :param region: string region name
        :param obj: The :class:`~editregions.models.EditRegionChunk` subclass
        :return:
        """
        self.opts = opts
        self.admin_namespace = namespace
        self.label = opts.verbose_name
        self.exists = obj is not None
        self.chunk = obj
        self.content_id = content_id
        self.region = region
        self.module = opts.app_label
        self.verbose_name = get_app_config_verbose_name(opts.app_label)

        # if the object already exists in the database, we're probably safe
        # to assume it's data is the most trustworthy.
        if self.exists:
            self.content_type = self.chunk.content_type_id
            self.content_id = self.chunk.content_id
            self.region = self.chunk.region
            self.module = obj._meta.app_label
            self.verbose_name = get_app_config_verbose_name(obj._meta.app_label)
        else:
            try:
                # attempt to accept either ContentType instances or primary keys
                # representing them.
                self.content_type = int(content_type.pk)
            except AttributeError as e:
                # Not an object, instead should be an integer
                self.content_type = content_type

        if self.region is not None:
            validate_region_name(self.region)

        if hasattr(self.opts, 'model_name'):
            model_name = self.opts.model_name
        else:
            model_name = self.opts.module_name

        self.url_parts = {
            'namespace': self.admin_namespace,
            'app': self.opts.app_label,
            'module': model_name,
            'view': '__error__',
        }
        self.querydict = QueryDict('', mutable=True)

        # update the querystring if they're not already in there.
        # possibly this is wrong, and should override any that are there?
        # I'm somewhat confused by it all now.
        for field in ('content_type', 'content_id', 'region'):
            if field not in self.querydict:
                self.querydict.update({field: getattr(self, field) or 0})

    def __str__(self):
        return force_text(self.label)

    def __repr__(self):
        return ('<{x.__module__}.{x.__class__.__name__} '
                'admin={x.admin_namespace}, label="{x.label}", '
                'exists={x.exists!r}, region={x.region}, module={x.module}, '
                'content_id={x.content_id}>').format(x=self)

    def __eq__(self, other):
        return all([
            self.content_type == other.content_type,
            self.content_id == other.content_id,
            self.region == other.region,
            self.opts == other.opts,
            self.admin_namespace == other.admin_namespace,
        ])

    def __nonzero__(self):
        return all([
            self.content_type is not None,
            self.content_id is not None,
        ])

    __bool__ = __nonzero__

    def __contains__(self, item):
        """
        Check a specific obj instance is "in" this.
        """
        return self.exists and item == self.chunk

    def __enter__(self):
        return AdminChunkWrapper(opts=self.opts, namespace=self.admin_namespace,
                                 content_id=self.content_id,
                                 content_type=self.content_type,
                                 region=self.region, obj=self.chunk)

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self

    def _get_admin_url(self, view='add'):
        self.url_parts.update(view=view)
        reverse_args = [self.chunk.pk] if self.exists else []
        endpoint = reverse(MODELADMIN_REVERSE % self.url_parts,
                           args=reverse_args)
        return '%s?%s' % (endpoint, self.querydict.urlencode())

    def get_delete_url(self):
        return self._get_admin_url(view='delete')

    def get_manage_url(self):
        """
        Our changelist doesn't fit with the _get_admin_url pattern, so rather
        than make it more extensible, we'll just do our work here.

        :return: URL + any querystring, as appropriate.
        :rtype: string
        """
        self.url_parts.update(view='changelist')
        endpoint = reverse(MODELADMIN_REVERSE % self.url_parts,
                           args=[self.content_type, self.content_id])
        return '%s?%s' % (endpoint, self.querydict.urlencode())

    def get_change_url(self):
        return self._get_admin_url(view='change')

    def get_add_url(self):
        return self._get_admin_url(view='add')

    def get_history_url(self):
        return self._get_admin_url(view='history')

    def get_move_url(self):
        return self._get_admin_url(view='move')

    def get_absolute_url(self):
        try:
            if self.exists:
                return self._get_admin_url(view='change')
            return self._get_admin_url(view='add')
        except NoReverseMatch:
            logger.warning("{me!r} couldn't find get the URL for the "
                           "necessary modeladmin".format(me=self), exc_info=1)
            return None

    def __getattr__(self, attr):
        """Pass lookups back to the object, if provided."""
        if self.exists and not attr.startswith('_'):
            return getattr(self.chunk, attr)
        raise AttributeError
