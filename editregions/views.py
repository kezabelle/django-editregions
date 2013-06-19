# -*- coding: utf-8 -*-
import logging
from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic.base import TemplateResponseMixin

logger = logging.getLogger(__name__)

class FormSuccess(Exception):
    def __init__(self, location, msg=None, permanent=False):
        self.location = location
        self.msg = msg
        self.permanent = permanent


class EditRegionResponseMixin(TemplateResponseMixin):
    """
    A mixin which implements the standard
    :class:`~django.views.generic.base.TemplateResponseMixin` features, with the
    additional feature that any view (or template, or template tag) which
    raises a :exc:`~editregions.views.FormSuccess` exception will *not*
    error, and will instead redirect to a given ``location``, also
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
            if e.msg is not None:
                messages.success(self.request, e.msg)
            logger.debug('%(path)s raised `FormSuccess`, redirecting to '
                         'new endpoint %(new_path)s' % {
                             'path': self.request.path,
                             'new_path': e.location,
                         })
            return redirect(e.location, permanent=e.permanent)
