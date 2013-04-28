# -*- coding: utf-8 -*-
from django.db.models.fields import CharField, PositiveIntegerField
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
