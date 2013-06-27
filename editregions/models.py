# -*- coding: utf-8 -*-
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
        return u'%(cls)r attached to %(content_object)s via region "%(region)s"' % {
            'content_object': unicode(self.content_object),
            'region': self.region,
            'cls': self.__class__,
        }

    def __unicode__(self):
        ct = get_content_type(self.content_type_id).model_class()
        return u'attached to %(content_object)s via region "%(region)s"' % {
            'content_object': unicode(ct._meta.verbose_name),
            'region': self.region,
        }

    def move(self, requested_position):
        from editregions.admin.forms import MovementForm
        form = MovementForm(data={'position': requested_position, 'pk': self.pk})
        if form.is_valid():
            return form.save()
        return form.errors

    class Meta:
        abstract = False
        ordering = ['position']
        db_table = 'editregions_editregionchunk'
        verbose_name = chunk_v
        verbose_name_plural = chunk_vplural


def remove_from_cache(instance, **kwargs):
    """
    Given an instance (a :class:`~editregions.models.EditRegionChunk` subclass)
    we construct a key using
    :attr:`~editregions.constants.EditRegionsConf.RENDERED_CACHE_KEY`
    and attempt to delete it from the default cache backend. We don't even
    care if it fails.

    We only care about the instance, so we're just smashing everything else
    into kwargs.
    """
    KEY = RENDERED_CACHE_KEY.format(content_type_id=instance.content_type_id,
                                    content_id=instance.content_id,
                                    region=instance.region)
    logger.debug('Clearing cache key {key!s} from the "{cache}" backend '
                 'because {obj!r} was saved'.format(key=KEY, obj=instance,
                                                    cache=DEFAULT_CACHE_ALIAS))
    cache.delete(KEY)

post_save.connect(receiver=remove_from_cache, sender=EditRegionChunk,
                  dispatch_uid='editregions_chunk_remove_from_cache')
