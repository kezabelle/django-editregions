# -*- coding: utf-8 -*-
from django.contrib.contenttypes.generic import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db.models.base import Model
from django.db.models.fields import DateTimeField, CharField, PositiveIntegerField
from django.db.models.fields.related import ForeignKey
from editregions.text import render_label, render_help
from editregions.utils.regions import validate_region_name




class CreatedModifiedBase(Model):
    """
    Abstract model for extending custom models with an audit of when things were
    changed. By extention, allows us to use get_latest_by to establish the most
    recent things.
    """
    created = DateTimeField(auto_now_add=True)
    modified = DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class GenericBase(Model):
    """
    For handling generic relations, here's an abstract base model.
    """
    content_type = ForeignKey(ContentType, related_name='+')
    content_id = CharField(max_length=255, db_index=True)
    content_object = GenericForeignKey('content_type', 'content_id')

    class Meta:
        abstract = True


class EditRegionChunk(CreatedModifiedBase, GenericBase):
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
