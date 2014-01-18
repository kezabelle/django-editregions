# -*- coding: utf-8 -*-
import logging
from django.contrib import messages
from django.shortcuts import redirect

logger = logging.getLogger(__name__)


class FormSuccess(Exception):
    __slots__ = ['location', 'msg', 'message', 'permanent']

    def __init__(self, location, msg=None, permanent=False):
        self.location = location
        self.msg = msg
        self.message = msg
        self.permanent = permanent

    def has_message(self):
        return self.msg is not None

    def get_message(self):
        return self.msg

    def get_redirect(self):
        return redirect(self.location, permanent=self.permanent)

    def __eq__(self, other):
        return isinstance(other, FormSuccess) and all([
            self.location == other.location,
            self.permanent == other.permanent,
        ])

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        # 301 < 302
        return self.permanent and not other.permanent

    def __gt__(self, other):
        # 302 > 301
        return not self.permanent and other.permanent

    def __le__(self, other):
        # 301 == 301 OR 302 == 302 OR 301 < 302
        return any([self.permanent == other.permanent, self.__lt__(other)])

    def __ge__(self, other):
        # 301 == 301 OR 302 == 302 OR 302 > 301
        return any([self.permanent == other.permanent, self.__gt__(other)])

    def __contains__(self, item):
        return item == self.location


class EditRegionResponseMixin(object):
    """
    A mixin which allows for any view (or template, or template tag) which
    raises a :exc:`~editregions.views.FormSuccess` exception to avoid showing
    an error, and will instead redirect to a given ``location``, also
    setting a flash message.
    """
    def render_to_response(self, context, **response_kwargs):
        """
        Returns a response with a template rendered with the given context,
        or alternatively returns an HTTP redirect if it encountered a
        :exc:`~editregions.views.FormSuccess` error (what a misnomer!)
        """
        try:
            return super(EditRegionResponseMixin, self).render_to_response(
                context, **response_kwargs)
        except FormSuccess as e:
            if e.has_message():
                messages.success(self.request, e.get_message(),
                                 fail_silently=True)
            logger.debug('%(path)s raised `FormSuccess`, redirecting to '
                         'new endpoint %(new_path)s' % {
                             'path': self.request.path,
                             'new_path': e.location,
                         })
            return e.get_redirect()
