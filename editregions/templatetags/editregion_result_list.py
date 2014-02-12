# -*- coding: utf-8 -*-
from django.template import Library
from django.contrib.admin.templatetags.admin_list import (result_headers,
                                                          result_hidden_fields,
                                                          results)

register = Library()


@register.inclusion_tag("admin/editregions/change_list_results.html")
def editregion_result_list(cl):
    """
    This literally only exists to change the template and fix it properly.
    """
    headers = list(result_headers(cl))
    num_sorted_fields = 0
    for h in headers:  # pragma: no cover .. this was just copypasted from Django
        if h['sortable'] and h['sorted']:
            num_sorted_fields += 1
    return {'cl': cl,
            'result_hidden_fields': list(result_hidden_fields(cl)),
            'result_headers': headers,
            'num_sorted_fields': num_sorted_fields,
            'results': list(results(cl))}
