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
    from collections import OrderedDict as SortedDict
except ImportError:
    from django.utils.datastructures import SortedDict
try:
    from django.apps import apps
    get_model = apps.get_model
    get_app = apps.get_app_config
except ImportError:
    from django.db.models.loading import get_model, get_app
from model_utils.managers import PassThroughManager, InheritanceManager
from editregions.querying import EditRegionChunkQuerySet
from editregions.text import chunk_v, chunk_vplural
from editregions.utils.data import get_modeladmin, get_content_type
from editregions.utils.regions import validate_region_name
from helpfulfields.models import Generic, ChangeTracking

logger = logging.getLogger(__name__)

try:
    import ujson as json
except ImportError:  # Haven't got an ultrajson package
    try:
        import json
    except ImportError:  # pragma: no cover ... Python < 2.6, Django < 1.6?
        from django.utils import simplejson as json

try:
    import yaml
    CAN_USE_YAML_DECODER = True
except ImportError:  # pragma: no cover ... will raise an exception later.
    CAN_USE_YAML_DECODER = False

try:
    import toml
    CAN_USE_TOML_DECODER = True
except ImportError:  # pragma: no cover ... will raise an exception later.
    CAN_USE_TOML_DECODER = False


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
    decoder = 'json'

    def __init__(self, obj=None, decoder=None):
        if decoder is not None:
            self.decoder = decoder
        if self.decoder == 'json':
            self.decoder_func = json.loads
        elif self.decoder == 'yaml' and CAN_USE_YAML_DECODER:
            self.decoder_func = yaml.safe_load
        elif self.decoder == 'toml' and CAN_USE_TOML_DECODER:
            self.decoder_func = toml.loads
        else:
            raise ImproperlyConfigured("Unable to use the requested "
                                       "deserialization format")
        if obj is not None and getattr(self, 'obj', None) is None:
            self.configure(obj=obj)

    def __eq__(self, other):
        return all([
            self.has_configuration == other.has_configuration,
            self.config == other.config,
        ])

    def __lt__(self, other):
        return len(self.config) < len(other.config)

    def __le__(self, other):
        return len(self.config) <= len(other.config)

    def __gt__(self, other):
        return len(self.config) > len(other.config)

    def __ge__(self, other):
        return len(self.config) >= len(other.config)

    def __nonzero__(self):
        return self.has_configuration and len(self.config) > 0

    __bool__ = __nonzero__

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

        serializer_template_names = ['{filename}.{serializer}'.format(
            filename=os.path.splitext(x)[0], serializer=self.decoder)
            for x in template_names]
        try:
            return select_template(serializer_template_names)
        except TemplateDoesNotExist:
            if settings.DEBUG:
                raise
            logger.exception('None of the following exist: {not_found}'.format(
                not_found=', '.join(serializer_template_names)
            ))
            return None

    def get_template_region_configuration(self):
        # if in production (DEBUG=False) and no template was found,
        # play nicely and don't error the whole request.
        if self.template is None:
            return {}
        rendered_template = self.template.render(Context()).strip()
        if len(rendered_template) == 0:
            logger.warning("Template was empty after being rendered")
            return {}
        # Allow decoding to bubble up an error.
        parsed_template = self.decoder_func(rendered_template)
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
            try:
                model = get_model(app_label=app, model_name=modelname)
            except LookupError as e:
                logger.exception("Unable to find requested model")
                model = None
            # Once we have a model and there's no stupid limit set,
            # add it to our new data structure.
            # Note that while None > 0 appears correct,
            # it isn't because None/False is a special value for infinite.
            infinity_or_valid_limit = (count is None or count is False or
                                       int(count) > 0)
            if model is not None and infinity_or_valid_limit:
                resolved.update({model: None if count is False else count})
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
        final_results = defaultdict(list)

        # figure out what models we need to ask for.
        for region, subconfig in self.config.items():
            final_results[region]  # this actually does assign the keys.
            klasses = subconfig.get('models', {}).keys()
            models |= set(klasses)
        models = tuple(models)

        if self.obj is None:
            if settings.DEBUG:
                raise ImproperlyConfigured("Tried to fetch chunks without "
                                           "having a valid `obj` for this "
                                           "EditRegionConfiguration instance")
            return final_results

        kws = {
            'content_type': get_content_type(self.obj),
            'content_id': self.obj.pk,
        }
        # avoids doing an IN (?, ?) query if only one region exists
        # avoids doing *any* query if no regions exist.
        region_count = len(final_results)
        if region_count < 1:
            return final_results
        elif region_count == 1:
            kws.update(region=list(final_results.keys())[0])
        else:
            kws.update(region__in=final_results.keys())

        # populate the resultset
        model_count = len(models)
        if model_count == 1:
            chunks = models[0].objects.filter(**kws)
        elif model_count > 1:
            chunks = EditRegionChunk.polymorphs.filter(**kws).select_subclasses(*models)  # noqa
        else:
            chunks = EditRegionChunk.objects.none()

        index = 0
        for index, chunk in enumerate(chunks.iterator(), start=1):
            final_results[chunk.region].append(chunk)
        logger.info("Requesting chunks resulted in {0} items".format(index))
        return final_results

    def fetch_chunks(self):
        return self._fetch_chunks

    def fetch_chunks_for(self, region):
        return self._fetch_chunks.get(region, ())
