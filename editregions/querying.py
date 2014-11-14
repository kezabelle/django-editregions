# -*- coding: utf-8 -*-
from collections import namedtuple
import logging
from django.db.models import Manager
from django.utils.timezone import now
from editregions.signals import different_region_move_completed
from editregions.signals import same_region_move_completed
from editregions.signals import move_completed


logger = logging.getLogger(__name__)


ReflowedPositions = namedtuple('ReflowPositions',
                               'before after moved_from moved_to')
ReflowedData = namedtuple('ReflowedData', 'obj positions')
MultipleReflowedData = namedtuple('MultipleReflowedData', 'old new')


class EditRegionChunkManager(Manager):
    use_for_related_fields = True

    def get_region_chunks(self, content_type, content_id, region):
        return self.filter(content_type=content_type, content_id=content_id,
                           region=region).order_by('position', '-modified')

    def move(self, obj, from_position, to_position, from_region, to_region):
        if to_position < 0:
            raise ValueError("Invalid target position; minimum position is 0")

        same_region = from_region == to_region
        same_position = from_position == to_position

        if same_region and same_position:
            raise ValueError("Cannot move `{obj!r}` because the given "
                             "arguments wouldn't do trigger a "
                             "movement.".format(obj=obj))

        if not same_region:
            logger.debug("Moving into a different region")
            moved = self.move_between_regions(
                obj=obj, to_position=to_position, from_region=from_region,
                to_region=to_region)
            different_region_move_completed.send(sender=self.model,
                                                 instance=obj,
                                                 reflowed_previous=moved.old,
                                                 reflowed_current=moved.new)
        else:
            logger.debug("Moving within the same region")
            moved = self.move_within_region(obj=obj, region=from_region,
                                            insert_position=to_position)
            same_region_move_completed.send(sender=self.model, instance=obj,
                                            reflowed=moved)
        move_completed.send(sender=self.model, instance=obj)
        return moved

    def _calculate_positions(self, obj, region, insert_position=None):
        region_chunks = list(self.get_region_chunks(
            content_type=obj.content_type, content_id=obj.content_id,
            region=region))
        pks_by_index = tuple(x.pk for x in region_chunks)

        to_remove = None
        if obj.pk in pks_by_index:
            to_remove = pks_by_index.index(obj.pk)
        if to_remove is not None:
            del region_chunks[to_remove]

        if insert_position is not None:
            region_chunks.insert(insert_position, obj)
        pks_by_index_after_moving = tuple(x.pk for x in region_chunks)

        return ReflowedPositions(before=pks_by_index, moved_from=to_remove,
                                 moved_to=insert_position,
                                 after=pks_by_index_after_moving)

    def move_between_regions(self, obj, to_position, from_region,
                             to_region):
        """
        find the chunk in the old region and remove it, reflowing those left.
        find and insert the chunk into the new region and reflow those ...
        """
        previous_reflow = self.move_within_region(obj=obj, region=from_region,
                                                  insert_position=None)

        new_reflow = self.move_within_region(obj=obj, region=to_region,
                                             insert_position=to_position)
        reflow_container = MultipleReflowedData(old=previous_reflow,
                                                new=new_reflow)
        return reflow_container

    def move_within_region(self, obj, region, insert_position):
        positions = self._calculate_positions(obj=obj, region=region,
                                              insert_position=insert_position)

        self._reflow_pks(pks=positions.after, moved_pk=obj.pk,
                         region=region)
        reflow = ReflowedData(obj=obj, positions=positions)
        return reflow

    def _reflow_pks(self, pks, moved_pk, region):
        for offset, chunk_pk in enumerate(pks, 0):
            kwargs = {'position': offset, 'region': region}
            # only "modify" the requested one.
            if chunk_pk == moved_pk:
                kwargs.update(modified=now())
            self.model.objects.filter(pk=chunk_pk).update(**kwargs)
        return True
