# -*- coding: utf-8 -*-
from django.contrib.contenttypes.models import ContentType
from django.db.models.fields import CharField, PositiveIntegerField
from django.db.models.fields.related import ForeignKey
from editregions.text import render_label, render_help
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
    render_content_type = ForeignKey(ContentType, verbose_name=render_label,
        help_text=render_help, related_name='+')

    def __repr__(self):
        return u'%(cls)r attached to %(content_object)s via region "%(region)s"' % {
            'content_object': unicode(self.content_object),
            'region': self.region,
            'cls': self.__class__,
        }

    def __unicode__(self):
        ct = ContentType.objects.get_for_id(self.content_type_id).model_class()
        return u'attached to %(content_object)s via region "%(region)s"' % {
            'content_object': unicode(ct._meta.verbose_name),
            'region': self.region,
            }

    class Meta:
        abstract = False
        ordering = ['position']
