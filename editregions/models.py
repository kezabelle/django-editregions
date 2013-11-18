# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging
import os
import re
from django.conf import settings
from django.core.cache import cache, DEFAULT_CACHE_ALIAS
from django.db.models.fields import CharField, PositiveIntegerField
from django.db.models.signals import post_save
from django.template import TemplateDoesNotExist
from django.template.loader import select_template
from django.template.context import Context
try:
    import json
except ImportError:
from django.utils import simplejson as json
from django.utils.datastructures import SortedDict
from django.db.models.loading import get_model
from editregions.constants import RENDERED_CACHE_KEY
from model_utils.managers import PassThroughManager, InheritanceManager
from editregions.querying import EditRegionChunkQuerySet
from editregions.text import chunk_v, chunk_vplural
from editregions.utils.data import get_content_type, get_modeladmin
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
        return 'pk={x.pk}, region={x.region}, position={x.position}'.format(x=self)

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


class EditRegionConfiguration(object):
    def __init__(self, obj):
        self.obj = obj
        self.modeladmin = get_modeladmin(self.obj)
        self.possible_templates = self.modeladmin.get_editregions_templates(
            obj=self.obj)
        self.template = self.get_first_valid_template()
        self.config = self.get_template_region_configuration()
        self.fallback_region_name_re = re.compile(r'[_\W]+')

    def get_first_valid_template(self):
        """
        Given a bunch of templates (tuple, list), find the first one in the
        settings dictionary. Assumes the incoming template list is ordered in
        discovery-preference order.
        """
        if isinstance(self.possible_templates, basestring):
            template_names = (self.possible_templates,)
        else:
            template_names = self.possible_templates
        try:
            return select_template('%s.json' % os.path.splitext(x)[0]
                                        for x in template_names)
        except TemplateDoesNotExist:
            if settings.DEBUG:
                raise
            return None

    def get_template_region_configuration(self):
        # if in production (DEBUG=False) and no JSON template was found,
        # play nicely and don't error the whole request.
        if self.template is None:
            return {}
        rendered_template = self.template.render(Context())
        parsed_template = json.loads(rendered_template)
        for key, config in parsed_template.items():
            if 'models' in parsed_template[key]:
                parsed_template[key]['models'] = self.get_enabled_chunks_for_region(parsed_template[key]['models'])

            if 'name' not in parsed_template[key]:
                logbits = {'region': key}
                logger.debug('No declared name for "%(region)s" in configuration, '
                             'falling back to using a regular expression' % logbits)
                parsed_template[key]['name'] = re.sub(
                    pattern=self.fallback_region_name_re, string=key, repl=' ')
        return parsed_template

    def get_enabled_chunks_for_region(self, model_mapping):
        """
        Get the list of available chunks. This allows chunks to exist in the database
        but get turned off after the fact, without deleting them.

        Returns an dictionary like object (specifically, a `SortedDict`) whose
        keys are the actual models, rather than dotted paths, and whose values are the
        counts for each chunk.
        """
        resolved = SortedDict()
        # Replace the dotted app_label/model_name combo with the actual model.
        for chunk, count in model_mapping.items():
            model = get_model(*chunk.split('.')[0:2])
            # Once we have a model and there's no stupid limit set,
            # add it to our new data structure.
            # Note that while None > 0 appears correct,
            # it isn't because None is a special value for infinite.
            if model is not None and (count is None or count > 0):
                resolved.update({model: count})
            if model is None:
                msg = 'Unable to load model "{cls}"'.format(cls=chunk)
                if settings.DEBUG:
                    raise ObjectDoesNotExist(msg)
                logger.error(msg)
        if len(resolved) == 0:
            logger.debug('No chunks types found for "%(region)s"' % {'region': name})
        return resolved

    def get_limits_for(region, chunk):
        """
        Try to figure out if this chunk type has a maximum limit in this region.
        Returns an integer or None.
        """
        try:
            return int(self.config[region]['models'][chunk])
        except KeyError:
            # Nope, no limit for this chunk.
            # Skipping down to returning None
            return None
