# -*- coding: utf-8 -*-

def queryset_to_attr_map(queryset, attr):
    output = {}
    for obj in queryset:
        result = getattr(obj, attr)
        output[result] = obj
    return output

def convert_context_to_dict(context):
    dicts = context.dicts
    out = {}
    for d in dicts:
        for key, value in d.items():
            out[key] = value
    return out
