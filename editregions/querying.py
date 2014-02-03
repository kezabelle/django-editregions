# -*- coding: utf-8 -*-
from django.db.models.query import QuerySet


class EditRegionChunkQuerySet(QuerySet):
    def move(self, target, position, region=''):
        from editregions.admin.forms import MovementForm
        form = MovementForm(data={'position': position, 'pk': target,
                                  'region': region})
        if form.is_valid():
            return form.save()
        return form.errors
