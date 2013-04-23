# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import functools
import logging
from django.core.exceptions import SuspiciousOperation, ValidationError
from django.core.urlresolvers import reverse
from django.forms import Media
from django.http import QueryDict
from django.utils.decorators import method_decorator, available_attrs
from django.utils.text import truncate_words
from editregions.utils.rendering import render_one_summary
from helpfulfields.admin import changetracking_readonlys, changetracking_fieldset
from editregions.utils.regions import validate_region_name
from adminlinks.templatetags.utils import MODELADMIN_REVERSE


logger = logging.getLogger(__name__)

# TODO: is this needed?
exclude_content_type_fields = ['content_type', 'content_id']

# TODO: is this needed?
datetimes_fields = changetracking_readonlys

# TODO: is this still needed?
datetimes_fieldset = changetracking_fieldset

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
        'editregions/js/jquery.ui.1-8-24.custom.js',
        # 'editregions/js/jquery.ui.core.js',
        # 'editregions/js/jquery.ui.widget.js',
        # 'editregions/js/jquery.ui.mouse.js',
        # 'editregions/js/jquery.ui.touch-punch.js',
        # 'editregions/js/jquery.ui.sortable.js',
        'editregions/js/dragging.js',
        'editregions/js/editing.js',
    ],
)


def guard_querystring(function):
    @functools.wraps(function, assigned=available_attrs(function))
    def wrapped(request, *args, **kwargs):
        fields_to_search = ('content_type', 'content_id', 'region')
        fields = {}
        for field in ('content_type', 'content_id'):
            fieldval = request.GET.get(field, 0)
            try:
                fields.update(field=int(fieldval))
            except (ValueError, TypeError) as e:
                # ValueError: got string which was unconvertable to integer.
                # TypeError: got none, shut up!
                msg = 'Invalid parameter "%s" with value: %s' % (field, fieldval)
                logger.warning(msg, extra={'status_code': 405,
                                           'request': request})
                # get out of this loop as early as possible.
                break

        regionval = request.GET.get('region', '__error__')
        try:
            validate_region_name(regionval)
            fields.update(region=regionval)
        except ValidationError as e:
            # invalid region name
            logger.warning('Invalid region value: %s' % regionval,
                           extra={'status_code': 405, 'request': request})

        if len(fields) < 3 or not all(fields.values()):
            missing_params = [x for x in fields_to_search if x not in fields]
            msg = ', '.join(missing_params)
            msg += ' missing from request'
            raise SuspiciousOperation(msg)
        else:
            return function(request, *args, **kwargs)
    return wrapped

guard_querystring_m = method_decorator(guard_querystring)

class AdminChunkWrapper(object):
    """
    An object for chunking an existing data type into, and getting out something
    we can reliably use in the admin widgets.
    """
    def __init__(self, opts, namespace, content_id, content_type, region, obj=None):
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
        try:
            self.content_type = content_type.pk
        except AttributeError as e:
            # if we got an error, it wasn't a ContentType, but the PK of
            # a content type ...
            self.content_type = content_type
        self.content_pk = content_id
        self.region = region
        self.label = opts.verbose_name
        self.exists = obj is not None
        self.chunk = obj

        self.module = opts.app_label
        if self.exists:
            self.module = obj._meta.app_label
        if self.region is not None:
            validate_region_name(region)

        self.url_parts = {
            'namespace': self.admin_namespace,
            'app': self.opts.app_label,
            'module': self.opts.module_name,
            'view': '__error__',
        }
        self.querydict = QueryDict('', mutable=True)
        self.querydict.update({
            'content_id': self.content_pk or 0,
            'content_type': self.content_type or 0,
            'region': self.region or '__error__',
        })

    def __unicode__(self):
        if self.exists:
            return '%(label)s: %(object)s' % {
                'label': self.label,
                'object': self.summary()
            }
        return self.label

    def summary(self):
        if self.exists:
            context = {
                'admin_summary': True,
            }
            return truncate_words(render_one_summary(context, self.chunk), 20)
        return ''

    def _get_admin_url(self, view='add'):
        self.url_parts.update(view=view)
        reverse_args = [self.chunk.pk] if self.exists else []
        endpoint = reverse(MODELADMIN_REVERSE % self.url_parts,
                           args=reverse_args)
        return '%s?%s' % (endpoint, self.querydict.urlencode())

    def get_delete_url(self):
        return self._get_admin_url(view='delete')

    def get_manage_url(self):
        return self._get_admin_url(view='changelist')

    def get_change_url(self):
        return self._get_admin_url(view='change')

    def get_add_url(self):
        return self._get_admin_url(view='add')

    def get_history_url(self):
        return self._get_admin_url(view='history')

    def get_move_url(self):
        return self._get_admin_url(view='move')

    def get_absolute_url(self):
        if self.exists:
            return self._get_admin_url(view='change')
        return self._get_admin_url(view='add')

    def __getattr__(self, attr):
        """Pass lookups back to the object, if provided."""
        if self.exists and not attr.startswith('_'):
            return getattr(self.chunk, attr)
        raise AttributeError
