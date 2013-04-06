# -*- coding: utf-8 -*-
import logging
from django.core.urlresolvers import reverse
from django.forms import Media
from django.utils.http import urlencode
from django.utils.text import truncate_words
from editregions.utils.rendering import render_one_summary
from helpfulfields.admin import changetracking_readonlys, changetracking_fieldset


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
            'editregions/css/inlines.css',
            'editregions/css/changelist-extras.css',
        ]
    },
    js=[
        'admin/js/jquery.rebind.js',
        'editregions/js/jquery.ui.1-8-24.custom.js',
        # 'editregions/js/jquery.ui.core.js',
        # 'editregions/js/jquery.ui.widget.js',
        # 'editregions/js/jquery.ui.mouse.js',
        # 'editregions/js/jquery.ui.touch-punch.js',
        # 'editregions/js/jquery.ui.sortable.js',
        'editregions/js/dragging.js',
    ],
)

class AdminChunkWrapper(object):
    """ An object for chunking an existing data type into, and getting out something
    we can reliably use in the admin widgets.
    """
    def __init__(self, opts, namespace, content_id, content_type, region, obj=None):
        self.opts = opts
        self.admin_namespace = namespace
        self.content_type = content_type
        self.content_pk = content_id
        self.region = region
        self.label = opts.verbose_name
        self.exists = obj is not None
        self.chunk = obj

        self.module = opts.app_label
        if self.exists:
            self.module = obj._meta.app_label

    def __unicode__(self):
        if self.exists:
            return u'%(label)s: %(object)s' % {
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
        return u''

    def _get_admin_url(self, view=u'add'):
        url_parts = {
            'admin': self.admin_namespace,
            'app': self.opts.app_label,
            'model': self.opts.module_name,
            'view': view,
        }
        querystring_parts = {
            'content_id': self.content_pk,
            'content_type': self.content_type,
            'region': self.region,
        }
        reverse_args = [self.chunk.pk] if self.exists else []
        endpoint = reverse('%(admin)s:%(app)s_%(model)s_%(view)s' % url_parts,
            args=reverse_args)
        return u'%s?%s' % (endpoint, urlencode(querystring_parts))

    def get_delete_url(self):
        return self._get_admin_url(view=u'delete')

    def get_change_url(self):
        return self._get_admin_url(view=u'change')

    def get_add_url(self):
        return self._get_admin_url(view=u'add')

    def get_history_url(self):
        return self._get_admin_url(view=u'history')

    def get_move_url(self):
        import pdb; pdb.set_trace()
        return self._get_admin_url(view=u'move')

    def get_absolute_url(self):
        if self.exists:
            return self._get_admin_url(view=u'change')
        return self._get_admin_url(view=u'add')

    def __getattr__(self, attr):
        """Pass lookups back to the object, if provided."""
        if self.exists and not attr.startswith('_'):
            return getattr(self.chunk, attr)
        raise AttributeError
