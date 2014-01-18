# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from collections import defaultdict
import logging
import os
import re
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db.models.fields import CharField, PositiveIntegerField
from django.template import TemplateDoesNotExist
from django.template.loader import select_template
from django.template.context import Context
from django.utils.encoding import python_2_unicode_compatible
from django.utils.functional import cached_property

try:
    from django.utils.six import string_types
except ImportError:  # pragma: no cover ... Python 2, Django < 1.5
    string_types = basestring,

try:
    import ujson as json
except ImportError:  # Haven't got an ultrajson package
    try:
        import json
    except ImportError:  # pragma: no cover ... Python < 2.6, Django < 1.6?
        from django.utils import simplejson as json

from django.utils.datastructures import SortedDict
from django.db.models.loading import get_model, get_app
from model_utils.managers import PassThroughManager, InheritanceManager
from editregions.querying import EditRegionChunkQuerySet
from editregions.text import chunk_v, chunk_vplural
from editregions.utils.data import get_modeladmin, get_content_type
from editregions.utils.regions import validate_region_name
from helpfulfields.models import Generic, ChangeTracking

logger = logging.getLogger(__name__)


@python_2_unicode_compatible
class EditRegionChunk(ChangeTracking, Generic):
    """
    Every edit region is made up of these, which serve as pointers for other
    models to key off.

    It may not be immeidiately obvious, because it uses abstract models, but
    this has *3* database indexes - the position, the content_id and the pk.
    """
    region = CharField(max_length=75, validators=[validate_region_name])
    position = PositiveIntegerField(default=None, db_index=True)

    objects = PassThroughManager.for_queryset_class(EditRegionChunkQuerySet)()
    polymorphs = InheritanceManager()

    def __repr__(self):
        return '<{x.__module__}.{x.__class__.__name__} pk={x.pk}, ' \
               'region={x.region}, parent_type={x.content_type_id}, ' \
               'parent_id={x.content_id}, position={x.position}>'.format(x=self)

    def __str__(self):
        return 'pk={x.pk}, region={x.region}, position={x.position}'.format(
            x=self)

    def move(self, requested_position):
        from editregions.admin.forms import MovementForm
        form = MovementForm(data={'position': requested_position, 'pk': self.pk})
        if form.is_valid():
            return form.save()
        return form.errors
    move.alters_data = True

    def clean(self):
        super(EditRegionChunk, self).clean()
        if self.position is None or self.position == 0:
            self.position = 1
        if self.content_id is None:
            raise ValidationError("{0.__class__} requires `content_id` to be "
                                  "the parent object's primary key")

    class Meta:
        abstract = False
        ordering = ['position']
        db_table = 'editregions_editregionchunk'
        verbose_name = chunk_v
        verbose_name_plural = chunk_vplural


class EditRegionConfiguration(object):
    fallback_region_name_re = re.compile(r'[_\W]+')
    config = {}
    has_configuration = False
    possible_templates = ()
    template = None
    obj = None
    modeladmin = None

    def __init__(self, obj=None):
        if obj is not None and getattr(self, 'obj', None) is None:
            self.configure(obj=obj)

    def __get__(self, instance, owner):
        if not hasattr(self, 'obj'):
            self.configure(instance)

    def configure(self, obj):
        self.obj = obj
        self.modeladmin = get_modeladmin(self.obj)
        self.possible_templates = self.modeladmin.get_editregions_templates(
            obj=self.obj)
        self.template = self.get_first_valid_template()
        self.has_configuration = self.template is not None
        self.config = self.get_template_region_configuration()

    def get_first_valid_template(self):
        """
        Given a bunch of templates (tuple, list), find the first one in the
        settings dictionary. Assumes the incoming template list is ordered in
        discovery-preference order.
        """
        if isinstance(self.possible_templates, string_types):
            template_names = (self.possible_templates,)
        else:
            template_names = self.possible_templates

        json_template_names = ['%s.json' % os.path.splitext(x)[0]
                               for x in template_names]
        try:
            return select_template(json_template_names)
        except TemplateDoesNotExist:
            if settings.DEBUG:
                raise
            logger.exception('None of the following exist: {not_found}'.format(
                not_found=', '.join(json_template_names)
            ))
            return None

    def get_template_region_configuration(self):
        # if in production (DEBUG=False) and no JSON template was found,
        # play nicely and don't error the whole request.
        if self.template is None:
            return {}
        rendered_template = self.template.render(Context()).strip()
        if len(rendered_template) == 0:
            logger.warning("Template was empty after being rendered")
            return {}
        # Allow JSON decoding to bubble up an error.
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
            app, modelname = chunk.split('.')[0:2]
            model = get_model(app_label=app, model_name=modelname)
            # Once we have a model and there's no stupid limit set,
            # add it to our new data structure.
            # Note that while None > 0 appears correct,
            # it isn't because None is a special value for infinite.
            if model is not None and (count is None or int(count) > 0):
                resolved.update({model: count})
            if model is None:
                msg = 'Unable to load model "{cls}" from app "{app}"'.format(
                    cls=modelname, app=app)
                if settings.DEBUG:
                    # request the *app* package, which may raise an explanatory
                    # exception for us ...
                    get_app(app)
                    # app exists, but the model doesn't.
                    raise ImproperlyConfigured(msg)
                logger.error(msg)
        if len(resolved) == 0:
            logger.debug('No chunks types found from `model_mapping` '
                         '{map!r}'.format(map=model_mapping))
        return resolved

    def get_limits_for(self, region, chunk):
        """
        Try to figure out if this chunk type has a maximum limit in this region.
        Returns an integer or None.
        """
        try:
            return int(self.config[region]['models'][chunk])
        except KeyError:
            # Nope, no limit for this chunk.
            # Skipping down to returning None
            return 0
        except TypeError:
            # chunk limit was None
            return None

    @cached_property
    def _fetch_chunks(self):
        logger.info("Requesting chunks")
        models = set()
        regions = set()
        final_results = defaultdict(list)

        # figure out what models we need to ask for.
        for region, subconfig in self.config.items():
            regions.add(region)
            klasses = subconfig.get('models', {}).keys()
            models |= set(klasses)
        models = tuple(models)

        kws = {
            'content_type': get_content_type(self.obj),
            'content_id': self.obj.pk,
        }
        # avoids doing an IN (?, ?) query if only one region exists
        # avoids doing *any* query if no regions exist.
        region_count = len(regions)
        if region_count < 1:
            return final_results
        elif region_count == 1:
            kws.update(region=regions.pop())
        elif region_count > 1:
            kws.update(region__in=regions)

        # populate the resultset
        chunks = EditRegionChunk.polymorphs.filter(**kws).select_subclasses(*models)  # noqa
        index = 0
        for index, chunk in enumerate(chunks.iterator(), start=1):
            final_results[chunk.region].append(chunk)
        logger.info("Requesting chunks resulted in {0} items".format(index))
        return final_results

    def fetch_chunks(self):
        return self._fetch_chunks

    def fetch_chunks_for(self, region):
        return self._fetch_chunks.get(region, ())
