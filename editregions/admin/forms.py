# -*- coding: utf-8 -*-
import logging
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import F
from django.forms import Form, Media
from django.forms.util import ErrorList
from django.forms.fields import IntegerField, CharField
try:
    from django.utils.encoding import force_text
except ImportError:  # < Django 1.5
    from django.utils.encoding import force_unicode as force_text
from editregions.utils.db import get_maximum_pk, get_next_chunks, set_new_position
from editregions.utils.data import attach_configuration, get_configuration
from editregions.utils.versioning import is_django_15plus
from editregions.models import EditRegionChunk, EditRegionConfiguration
from editregions.admin.utils import shared_media
from editregions.utils.regions import validate_region_name

logger = logging.getLogger(__name__)


class EditRegionInlineForm(object):
    """
    Used by EditRegionInlineForm
    """
    media = Media()


class EditRegionInlineFormSet(object):
    """
    A minimal representation of a FormSet as called by the Django inline
    admin code. The most importand bit is our media definition, everything else
    is literally just to appear correct.
    """
    initial_forms = []
    extra_forms = []
    media = shared_media
    empty_form = EditRegionInlineForm()
    errors = {}

    # used for constructing change messages
    new_objects = []
    changed_objects = []
    deleted_objects = []

    @classmethod
    def get_default_prefix(cls):
        return 'edit_region_chunk_formset'

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def get_queryset(self, *args, **kwargs):
        return self.kwargs['queryset']

    def is_valid(self, *args, **kwargs):
        return True

    def save(self, *args, **kwargs):
        return True

    def non_form_errors(self):
        return ErrorList()


class MovementForm(Form):
    """
    Move a chunk from one place to another.
    """
    pk = IntegerField(min_value=1)
    position = IntegerField(min_value=1)
    #: if region is set, then we're probably in an inline'd changelist, and
    #: we may be wanting to move region ...
    region = CharField(required=False, validators=[validate_region_name])
    obj_cache = None

    def __init__(self, *args, **kwargs):
        super(MovementForm, self).__init__(*args, **kwargs)

        try:
            self.fields['pk'].max_value = get_maximum_pk(self.Meta.model)
        except IndexError as e:
            # there probably aren't any objects in the DB yet, so the only thing
            # to move about is the minimum ... I think.
            self.fields['pk'].max_value = self.fields['pk'].min_value

        # TODO: maximum position should be count() of those in region for this
        # minus 1, I think.

    def clean(self):
        cd = super(MovementForm, self).clean()
        pk = cd.get('pk', 0)
        try:
            cd['pk'] = self.Meta.model.polymorphs.get_subclass(pk=pk)
        except ObjectDoesNotExist as e:
            cd['pk'] = None
            self._errors['pk'] = e.msg

        # rather than raise an error for an invalid region, just set it
        # back to whatever the region says it should be. Trust no-one.
        if 'region' in cd and cd['pk'] is not None:
            attach_configuration(cd['pk'].content_object,
                                 EditRegionConfiguration)
            erc = get_configuration(cd['pk'].content_object)
            if cd['region'] not in erc.config:
                cd['region'] = cd['pk'].region
        return cd

    def save(self):
        """
        Updates the current object, and all other objects in the same region.
        """
        obj = self.cleaned_data['pk']
        old_position = obj.position
        obj.position = self.cleaned_data['position']
        old_region = obj.region
        new_region = self.cleaned_data.get('region', obj.region)

        next_chunks = get_next_chunks(EditRegionChunk, position=obj.position,
                                      region=new_region)

        logger.debug('Push objects which should be affected, including the one '
                     'we in the position we need.')
        next_chunks.update(position=F('position') + 1)
        del next_chunks  # not required hereafter.

        # if we've moved region, we need to update at least a partial set of
        # positions on the old region ... we do it here, before saving the
        # new object into position, then handle updating the old region
        # last of all...
        old_chunks = None
        if old_region != new_region:
            logger.debug('object moved from {old} to {new}'.format(
                         old=old_region, new=new_region))
            obj.region = new_region
            old_chunks = get_next_chunks(EditRegionChunk, position=old_position,
                                         region=old_region)

        kwargs = {}
        if is_django_15plus():
            kwargs.update(update_fields=['region', 'position'])
        obj.save(**kwargs)

        if old_chunks is not None:
            logger.debug('all chunks in old region, which were after our moved '
                         'object, need to be shifted up by 1 to try and force '
                         'the positions into being contiguous again.')
            old_chunks.update(position=F('position') - 1)
        del old_chunks, old_region  # we're finished handling the previous.

        new_chunks = EditRegionChunk.objects.filter(content_type=obj.content_type,
                                                    content_id=obj.content_id,
                                                    region=new_region)
        # find all the existing objects and iterate over each of them,
        # doing an update (rather than save, to avoid changing the `modified`
        # field) if they're not in the correct position.
        for new_position, obj in enumerate(new_chunks.iterator(), 1):
            if obj.position != new_position:
                logger.debug('{obj!r} out of position, moving from'
                             '{obj.position} to {new_position}'.format(
                             obj=obj, new_position=new_position))
                set_new_position(EditRegionChunk, pk=obj.pk,
                                 position=new_position)
        return obj

    def change_message(self):
        obj = self.cleaned_data['pk']
        msg = 'Moved to position {obj.position} in region "{obj.region}"'.format(obj=obj)
        logger.info(msg)
        return obj, msg

    def parent_change_message(self):
        obj = self.cleaned_data['pk']
        msg = 'Moved {vname} (pk: {obj.pk}) to position {obj.position} in ' \
              'region "{obj.region}"'.format(vname=force_text(obj._meta.verbose_name),
                                             obj=obj)
        logger.info(msg)
        return obj.content_object, msg

    class Meta:
        model = EditRegionChunk
