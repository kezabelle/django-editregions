# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from collections import defaultdict
from itertools import groupby, chain
from operator import attrgetter
import logging
from django.core.urlresolvers import reverse, NoReverseMatch
import os
import re
from django.conf import settings
try:
    from django.contrib.contenttypes.fields import GenericForeignKey
except ImportError:  # pragma: no cover ... Django < 1.7
    from django.contrib.contenttypes.generic import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.db.models import (ForeignKey, Model, CharField,
                              PositiveIntegerField, DateTimeField)
from django.template import TemplateDoesNotExist
from django.template.loader import select_template
from django.template.context import Context
from django.utils.encoding import python_2_unicode_compatible, force_text

try:
    from django.utils.six import string_types
    from django.db.models.constants import LOOKUP_SEP
except ImportError:  # pragma: no cover ... Python 2, Django < 1.5
    from django.db.models.sql.constants import LOOKUP_SEP
    string_types = (basestring,)

try:
    from collections import OrderedDict as SortedDict
except ImportError:  # pragma: no cover ... Python < 2.7, Django < 1.7
    from django.utils.datastructures import SortedDict
try:
    from django.apps import apps
    get_model = apps.get_model
    get_app = apps.get_app_config
except ImportError:  # pragma: no cover ... Django < 1.7
    from django.db.models.loading import get_model, get_app
from model_utils.managers import InheritanceManager
from editregions.querying import EditRegionChunkManager
from editregions.text import chunk_v, chunk_vplural
from editregions.utils.data import get_modeladmin, get_content_type
from editregions.utils.regions import validate_region_name
from editregions.constants import SPLIT_CHUNKS_EVERY
from editregions.constants import REQUEST_VAR_CT
from editregions.constants import REQUEST_VAR_ID

logger = logging.getLogger(__name__)

try:
    import ujson as json
except ImportError:  # Haven't got an ultrajson package
    try:
        import json
    except ImportError:  # pragma: no cover ... Python < 2.6, Django < 1.6?
        from django.utils import simplejson as json


@python_2_unicode_compatible
class EditRegionChunk(Model):
    """
    Every edit region is made up of these, which serve as pointers for other
    models to key off.

    It may not be immeidiately obvious, because it uses abstract models, but
    this has *3* database indexes - the position, the content_id and the pk.
    """
    created = DateTimeField(auto_now_add=True)
    modified = DateTimeField(auto_now=True)

    content_type = ForeignKey(ContentType, related_name='+')
    # TODO: Do we actually need this index, if we're using index_together
    content_id = CharField(max_length=255, db_index=True, blank=False,
                           null=False)
    content_object = GenericForeignKey('content_type', 'content_id')

    region = CharField(max_length=75, validators=[validate_region_name])
    position = PositiveIntegerField(default=None, db_index=True)

    objects = EditRegionChunkManager()
    polymorphs = InheritanceManager()

    def __repr__(self):
        return '<{x.__module__}.{x.__class__.__name__} pk={x.pk}, ' \
               'region={x.region}, parent_type={x.content_type_id}, ' \
               'parent_id={x.content_id}, position={x.position}>'.format(x=self)

    def __str__(self):
        return 'pk={x.pk}, region={x.region}, position={x.position}'.format(
            x=self)

    class Meta:
        abstract = False
        ordering = ['position', '-modified']
        index_together = [
            # this index allows us to get all the regions & chunks for a
            # given object in one query without potentially doing a full
            # table scan, even though that is cheap to many many thousands
            # of chunks.
            ['content_type', 'content_id', 'region'],
        ]
        db_table = 'editregions_editregionchunk'
        verbose_name = chunk_v
        verbose_name_plural = chunk_vplural


fallback_region_name_re = re.compile(r'[_\W]+')


@python_2_unicode_compatible
class EditRegionConfiguration(object):

    __slots__ = ('config', 'raw_config', 'has_configuration',
                 '_previous_fetched_chunks', 'obj', 'ct', 'decoder',
                 'decoder_func', 'valid_templates')

    def __init__(self, obj=None):
        self.config = {}
        self.raw_config = {}
        self.valid_templates = ()
        self.has_configuration = False
        self._previous_fetched_chunks = None
        self.obj = None
        self.decoder = 'json'
        self.decoder_func = json.loads
        if obj is not None and getattr(self, 'obj', None) is None:
            self.configure(obj=obj)

    def __str__(self):
        return '<{mod}.{cls} for "{obj}" using "{decoder}" decoder>'.format(
            mod=self.__module__, cls=self.__class__.__name__,
            obj=force_text(self.obj), decoder=self.decoder
        )

    def __repr__(self):
        return ('<{mod}.{cls} for "{obj}" using "{decoder}" decoder to get '
                'config: "{data!s}">'.format(
                    mod=self.__module__, cls=self.__class__.__name__,
                    obj=force_text(self.obj), decoder=self.decoder,
                    data=self.config
                ))

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

    def tolist(self):
        return self.raw_config

    def get_absolute_url(self):
        try:
            url = reverse('admin:editregions_editregionchunk_changelist')
        except NoReverseMatch:
            return None
        return '{url}?{ct_name}={ct_value}&{obj_name}={obj_value}'.format(
            ct_name=REQUEST_VAR_CT, ct_value=self.ct.pk,
            obj_name=REQUEST_VAR_ID, obj_value=self.obj.pk,
            url=url)

    def is_valid_template(self, template_name):
        if not template_name:
            return False
        if not self.valid_templates:
            return False
        if template_name not in self.valid_templates:
            return False
        return True

    def set_template(self, template_name):
        template = self.get_first_valid_template(template_name)
        self.has_configuration = template is not None
        self.raw_config = self.decode_template_region_configuration(
            template_instance=template)
        self.config = self.get_template_region_configuration(
            raw_data=self.raw_config)

    def configure(self, obj):
        self.obj = obj
        self.ct = get_content_type(obj)
        modeladmin = get_modeladmin(self.obj)
        if hasattr(modeladmin, 'get_editregions_template_choices'):
            self.valid_templates = modeladmin.get_editregions_template_choices(
                obj=self.obj)
        possible_templates = modeladmin.get_editregions_templates(
            obj=self.obj)
        self.set_template(possible_templates)

    def get_first_valid_template(self, possible_templates):
        """
        Given a bunch of templates (tuple, list), find the first one in the
        settings dictionary. Assumes the incoming template list is ordered in
        discovery-preference order.
        """
        if isinstance(possible_templates, string_types):
            template_names = (possible_templates,)
        else:
            template_names = possible_templates

        serializer_template_names = ['{filename}.{serializer}'.format(
            filename=os.path.splitext(x)[0], serializer=self.decoder)
            for x in template_names if x.strip()]
        try:
            return select_template(serializer_template_names)
        except TemplateDoesNotExist:
            if settings.DEBUG:
                raise
            logger.exception('None of the following exist: {not_found}'.format(
                not_found=', '.join(serializer_template_names)
            ))
            return None

    def decode_template_region_configuration(self, template_instance):
        # if in production (DEBUG=False) and no template was found,
        # play nicely and don't error the whole request.
        if template_instance is None:
            return {}
        # avoid generating an empty Context instance by not calling .render()
        rendered_template = template_instance.render(
            context=Context({})).strip()
        if len(rendered_template) == 0:
            logger.warning("Template was empty after being rendered")
            return {}
        # Allow decoding to bubble up an error.
        parsed_template = self.decoder_func(rendered_template)
        return SortedDict(sorted(parsed_template.items()))

    def get_template_region_configuration(self, raw_data):
        desired_config = SortedDict()
        for key, config in raw_data.items():
            models = {}
            if 'models' in raw_data[key]:
                models = self.get_enabled_chunks_for_region(raw_data[key]['models'])
            fallback = re.sub(pattern=fallback_region_name_re, string=key,
                              repl=' ')
            name = raw_data[key].get('name', fallback)
            desired_config[key] = {'name': name, 'models': models}
        return desired_config

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

    @property
    def _fetch_chunks(self):
        if self._previous_fetched_chunks is not None:
            # previously this was using a cached_property decorator, but that
            # prevents me trying to be clever and use __slots__
            logger.info("Requesting previously fetched chunks")
            return self._previous_fetched_chunks

        logger.info("Requesting chunks")
        models = set()
        self._previous_fetched_chunks = defaultdict(list)
        parsed_config = tuple(self.config.items())

        # fail as early as possible if there's nothing to do.
        if len(parsed_config) < 1:
            return self._previous_fetched_chunks

        # calculate the maximum number of a) dict keys, b) models required in
        # the queryset.
        for region, subconfig in parsed_config:
            self._previous_fetched_chunks[region]  # this actually does assign the keys.
            klasses = subconfig.get('models', {}).keys()
            models |= set(klasses)
        models = tuple(models)

        if self.obj is None:
            if settings.DEBUG:
                raise ImproperlyConfigured("Tried to fetch chunks without "
                                           "having a valid `obj` for this "
                                           "EditRegionConfiguration instance")
            return self._previous_fetched_chunks

        kws = {
            'content_type': get_content_type(self.obj),
            'content_id': self.obj.pk,
        }
        # avoids doing an IN (?, ?) query if only one region exists
        # avoids doing *any* query if no regions exist.
        region_count = len(self._previous_fetched_chunks)
        if region_count < 1:
            return self._previous_fetched_chunks
        elif region_count == 1:
            # cast to list because PY3 is lame.
            kws.update(region=list(self._previous_fetched_chunks.keys())[0])
        else:
            kws.update(region__in=self._previous_fetched_chunks.keys())

        # populate the resultset, in the most efficient way possible for the
        # given models.
        model_count = len(models)
        if model_count == 1:
            chunks = models[0].objects.filter(**kws)
        elif model_count > 1:
            # this will do as few queries as possible. Ideally, just 1.
            chunks = self._fetch_subclasses(lookups=kws, models=models)
        else:
            chunks = EditRegionChunk.objects.none()

        index = 0
        for index, chunk in enumerate(chunks, start=1):
            if chunk.__class__ != EditRegionChunk:
                self._previous_fetched_chunks[chunk.region].append(chunk)
        logger.info("Requesting chunks resulted in {0} items".format(index))
        return self._previous_fetched_chunks

    def _fetch_subclasses(self, lookups, models):
        """
        If we have a lot of tables to join, to keep query time down, we
        instead do multiple smaller queries, to avoid some of the
        penalties described in https://github.com/elbaschid/mti-lightbulb
        """
        manager = EditRegionChunk.polymorphs
        # let model-utils calculate the dependencies.
        calculated_relations = manager.select_subclasses(*models).subclasses
        split_after = getattr(settings, 'EDITREGIONS_SPLIT_EVERY',
                              SPLIT_CHUNKS_EVERY)

        # figure out how many tables are going to end up joined
        tables_bases = (x.split(LOOKUP_SEP) for x in calculated_relations)
        tables = frozenset(chain(*tables_bases))

        if len(tables) > split_after:
            data = self._dissect_subclasses(relations=calculated_relations,
                                            split_after=split_after)
            # by this point, `data` should be a list of tuples, where
            # each tuple represents a subset of subclasses to ask for.
            chained_qs = chain(*(
                manager.filter(**lookups).select_subclasses(*subclass_set)
                for subclass_set in data if subclass_set))
            # because we're now not asking for all the correct subclasses,
            # we'll get back more results than we want, so we need to throw
            # out those which haven't been cast down.
            filtered_out_ercs = (x for x in chained_qs
                                 if x.__class__ != EditRegionChunk)
            sorted_qslike = sorted(filtered_out_ercs,
                                   key=attrgetter('position'))
            return sorted_qslike

        # few enough tables needed joining that we can just do one.
        return manager.filter(**lookups).select_subclasses(*models).iterator()

    def _dissect_subclasses(self, relations, split_after):
        """
        takes a list of relations for select_related/select_subclasses and
        splits them up based on a maximal number of tables to join at once.
        """
        def by_lookup_sep(x): return x.split(LOOKUP_SEP)  # noqa
        def by_root_relation(x): return by_lookup_sep(x)[0]  # noqa

        sorted_relations = sorted(relations, key=by_lookup_sep)
        # re-group the subclasses based on root tables.
        grouped_relations = groupby(sorted_relations, key=by_root_relation)
        # outgroups will contain tuples of relations for select_subclasses
        outgroups = []
        # tracking those which aren't grandchildren. Should be most relations.
        still_available = []
        for base_table, children in grouped_relations:
            children = tuple(children)
            if len(children) > 1:
                outgroups.append(children)
                logger.warning("You're being punished for using grandchildren "
                               "or deeper: {0!r}".format(children))
            else:
                still_available.extend(children)

        # cut up the non-grandchildren+ relations into groups of length N
        splitups = range(0, len(still_available), split_after)
        chunked_available = (tuple(still_available[i:i+split_after])
                             for i in splitups)
        outgroups.extend(chunked_available)
        # if there's only one left over, apply it to the previous one, as lon
        # as the split is greater than 1.
        if len(outgroups) > 1 and len(outgroups[-1]) == 1 and split_after > 1:
            last = outgroups.pop()
            outgroups[-1] += last
        return tuple(outgroups)

    def fetch_chunks(self):
        return self._fetch_chunks

    def fetch_chunks_for(self, region):
        return self._fetch_chunks.get(region, ())
