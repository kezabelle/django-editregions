# -*- coding: utf-8 -*-
from helpfulfields.querysets import ChangeTrackingQuerySet


class EditRegionChunkQuerySet(ChangeTrackingQuerySet):
    def move(self, target, position, region=''):
        from editregions.admin.forms import MovementForm
        form = MovementForm(data={'position': position, 'pk': target,
                                  'region': region})
        if form.is_valid():
            return form.save()
        return form.errors
