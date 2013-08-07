# -*- coding: utf-8 -*-
import logging
from django.core.cache import cache, DEFAULT_CACHE_ALIAS
from django.db.models.fields import CharField, PositiveIntegerField
from django.db.models.signals import post_save
from editregions.constants import RENDERED_CACHE_KEY
from model_utils.managers import PassThroughManager, InheritanceManager
from editregions.querying import EditRegionChunkQuerySet
from editregions.text import chunk_v, chunk_vplural
from editregions.utils.data import get_content_type
from editregions.utils.regions import validate_region_name
from helpfulfields.models import Generic, ChangeTracking

logger = logging.getLogger(__name__)


class EditRegionChunk(ChangeTracking, Generic):
    """
    Every edit region is made up of these, which serve as pointers for other
    models to key off.

    It may not be immeidiately obvious, because it uses abstract models, but
    this has *3* database indexes - the position, the content_id and the pk.
    """
    region = CharField(max_length=75, validators=[validate_region_name])
    position = PositiveIntegerField(default=None, db_index=True)
    #subcontent_type = ForeignKey(ContentType, verbose_name=render_label,
    #                             help_text=render_help, related_name='+')

    objects = PassThroughManager.for_queryset_class(EditRegionChunkQuerySet)()
    polymorphs = InheritanceManager()

    def __repr__(self):
        return '<{x.__module__}.{x.__class__.__name__} pk={x.pk},' \
               'region={x.region}, parent_type={x.content_type_id}, ' \
               'parent_id={x.content_id}, position={x.position}'.format(x=self)

    def __unicode__(self):
        return 'Chunk'

    def move(self, requested_position):
        from editregions.admin.forms import MovementForm
        form = MovementForm(data={'position': requested_position, 'pk': self.pk})
        if form.is_valid():
            return form.save()
        return form.errors
    move.alters_data = True

    class Meta:
        abstract = False
        ordering = ['position']
        db_table = 'editregions_editregionchunk'
        verbose_name = chunk_v
        verbose_name_plural = chunk_vplural
