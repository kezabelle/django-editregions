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
from editregions.constants import REQUEST_VAR_REGION, REQUEST_VAR_ID, REQUEST_VAR_CT
from editregions.utils.rendering import render_one_summary
from helpfulfields.admin import changetracking_readonlys, changetracking_fieldset
from editregions.utils.regions import validate_region_name
from editregions.models import EditRegionChunk
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
        content_id = lookup.get(REQUEST_VAR_ID, '0')
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

        # attempt to accept either ContentType instances or primary keys
        # representing them.
        try:
            self.content_type = int(content_type.pk)
        except AttributeError as e:
            # Not an object, instead should be an integer
            self.content_type = content_type

        self.content_id = content_id
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

        # if the object already exists in the database, we're probably safe
        # to assume it's data is the most trustworthy.
        if self.exists:
            self.content_type = self.chunk.content_type.pk
            self.content_id = self.chunk.content_id
            self.region = self.chunk.region

        # update the querystring if they're not already in there.
        # possibly this is wrong, and should override any that are there?
        # I'm somewhat confused by it all now.
        for field in ('content_type', 'content_id', 'region'):
            if field not in self.querydict:
                self.querydict.update({field: getattr(self, field) or 0})

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
