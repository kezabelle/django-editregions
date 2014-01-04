# -*- coding: utf-8 -*-


def get_maximum_pk(pagemodel):
    """
    Used in the movement form to provide a maximum value for validation
    :param pagemodel: the model to filter on, usually `Page`
    """
    try:
        return pagemodel.objects.all().only('pk').order_by('-pk')[0].pk
    except AttributeError:
        # NoneType has no pk, so the maximum position is ...
        return 1


def get_next_chunks(pagemodel, obj, position, **kwargs):
    """
    returns any chunks that are "lower" (further down) than the given obj
    :param pagemodel: the model to filter on, usually `Page`
    :param obj: the thing whose chunks we want to know about.
    :param kwargs: other arguments to filter by
    """
    return pagemodel.objects.filter(content_type=obj.content_type,
                                    content_id=obj.content_id,
                                    position__gte=position,
                                    **kwargs)


def get_chunks_in_region_count(pagemodel, content_type, obj_id, region):
    return max(0, pagemodel.objects.filter(content_type=content_type,
                                           content_id=obj_id,
                                           region=region).only('pk').count())  # noqa


def set_new_position(model, pk, position):
    """
    Doesn't fire any signals.
    """
    return model.objects.filter(pk=pk).update(position=position)
