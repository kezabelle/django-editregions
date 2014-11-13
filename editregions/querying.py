# -*- coding: utf-8 -*-
from collections import namedtuple
import logging
from django.db.models import Manager
from django.db.models import F
from editregions.utils.versioning import is_django_15plus


logger = logging.getLogger(__name__)


ReflowedData = namedtuple('ReflowedData', 'obj moved moved_pks from_position')
MultipleReflowedData = namedtuple('MultipleReflowedData', 'old new')


class EditRegionChunkManager(Manager):

    def get_region_chunks(self, content_type, content_id, region):
        return self.filter(content_type=content_type, content_id=content_id,
                           region=region)

    def get_region_chunks_from_position(self, content_type, content_id, region,
                                        position):
        region_chunks = self.get_region_chunks(content_type=content_type,
                                               content_id=content_id,
                                               region=region)
        return region_chunks.filter(position__gte=position)

    def move(self, obj, from_position, to_position, from_region, to_region):
        same_region = from_region == to_region
        same_position = from_position == to_position
        if same_region and same_position:
            raise ValueError("Cannot move `{pk!s}` because the given arguments "
                             "wouldn't do trigger a movement.")

        if not same_region:
            logger.debug("Moving into a different region")
            return self.move_between_regions(obj=obj,
                                             from_position=from_position,
                                             to_position=to_position,
                                             from_region=from_region,
                                             to_region=to_region)
        logger.debug("Moving within the same region")
        return self.move_within_region(obj=obj, region=from_region,
                                       from_position=from_position,
                                       to_position=to_position)

    def move_between_regions(self, obj, from_position, to_position, from_region,
                             to_region):
        reflow_new_region = self.reflow_region(from_position=to_position,
                                               region=to_region,
                                               obj=obj)

        obj.region = to_region
        obj.position = to_position
        kwargs = {}
        if is_django_15plus():  # pragma: no cover ... tests cover this.
            kwargs.update(update_fields=['position', 'region'])
        obj.save(**kwargs)

        reflow_old_region = self.reflow_region(from_position=from_position,
                                               region=from_region,
                                               obj=obj)

        return MultipleReflowedData(old=reflow_old_region,
                                    new=reflow_new_region)

    def move_within_region(self, obj, region, from_position, to_position):
        """
        shift everything greaterthan /equal to `to_permission` by 1
        insert into position `to_permission`
        reflow everything starting at `from_position`
        """
        next_chunks = self.get_region_chunks_from_position(
            content_type=obj.content_type, content_id=obj.content_id,
            region=region, position=to_position)
        next_chunks.update(position=F('position') + 1)

        obj.position = to_position
        kwargs = {}
        if is_django_15plus():  # pragma: no cover ... tests cover this.
            kwargs.update(update_fields=['position'])
        obj.save(**kwargs)

        return self.reflow_region(obj=obj, from_position=from_position)

    def reflow_region(self, obj, region, from_position):
        """
        Starting at `from_position` for a given region, iterate over each one
        and restore correct ordering, falling back to the modified date should
        I somehow let multiple objects end up with the same position.
        """
        need_reflowing = self.get_region_chunks_from_position(
            content_type=obj.content_type, content_id=obj.content_id,
            region=region, position=from_position)
        need_reflowing_ordered = need_reflowing.order_by('position', '-modified')  # noqa

        moved = set()
        reflow_iterable = enumerate(iterable=need_reflowing_ordered.iterator(),
                                    start=from_position)
        for to_position, _obj in reflow_iterable:
            if _obj.position == to_position:
                continue
            msg = '{obj!r} moving from `{obj.position}` to `{new_position}`'
            logger.debug(msg.format(obj=_obj, new_position=to_position))
            self.filter(pk=_obj.pk).update(position=to_position)
            moved.add(_obj.pk)

        return ReflowedData(obj=obj, moved=bool(moved), moved_pks=moved,
                            from_position=from_position)
