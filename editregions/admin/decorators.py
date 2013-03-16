# -*- coding: utf-8 -*-
import logging
from django.http import HttpResponseForbidden
from django.utils.decorators import method_decorator, available_attrs
from django.utils.functional import wraps

logger = logging.getLogger(__name__)

def guard_querystring(view_func, extra_fields=None):
    """The levels of indirection involved in this are phenomonal. WTF does it do?
    Note: upon consideration in the future,
    I may scrap this and revert to overriding methods on the classes I need.
    """
    def decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *args, **kwargs):
            import pdb; pdb.set_trace()
            if extra_fields is None:
                extra_fields = []
            fields = ['content_type', 'content_id', 'region'] + extra_fields
            get_params = [request.GET.get(field, None) for field in fields]
            if not all(get_params):
                logger.warning('Parameters missing from request: %s' % request.path,
                    extra={
                        'status_code': 405,
                        'request': request
                    }
                )
                return HttpResponseForbidden()
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

guard_querystring_m = method_decorator(guard_querystring)
