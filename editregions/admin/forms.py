# -*- coding: utf-8 -*-
from django.db.models import F
from django.forms import Form, Media
from django.forms.util import ErrorList
from django.forms.fields import IntegerField, CharField
from django.utils.encoding import force_unicode
from editregions.models import EditRegionChunk
from editregions.admin.utils import shared_media
from editregions.utils.chunks import get_chunks_for_region
from editregions.utils.regions import (validate_region_name,
                                       get_regions_for_template, get_first_valid_template)


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
            self.fields['pk'].max_value = (self.Meta.model.objects.all().only('pk')
                                           .order_by('-pk')[0].pk)
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
        except self.Meta.model.DoesNotExist as e:
            cd['pk'] = None
            self._errors['pk'] = e.msg

        # rather than raise an error for an invalid region, just set it
        # back to whatever the region says it should be. Trust no-one.
        if 'region' in cd and cd['pk'] is not None:
            templates = cd['pk'].content_object.get_region_groups()
            template = get_first_valid_template(templates)
            regions = get_regions_for_template(template)
            if cd['region'] not in regions:
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

        next_chunks = get_chunks_for_region(content_type=obj.content_type,
                                            content_id=obj.content_id,
                                            region=new_region,
                                            position__gte=obj.position)
        # push those that should be affected, down by 1 each. Including the one
        # in the position we want!
        next_chunks.update(position=F('position') + 1)

        # if we've moved region, we need to update at least a partial set of
        # positions on the old region ... we do it here, before saving the
        # new object into position, then handle updating the old region
        # last of all...
        old_chunks = None
        if old_region != new_region:
            obj.region = new_region
            old_chunks = get_chunks_for_region(content_type=obj.content_type,
                                               content_id=obj.content_id,
                                               region=old_region,
                                               position__gte=old_position)

        # we don't mind updating the `modified` field for this one, because
        # we moved it explicitly, and we may've also changed region ...
        obj.save()

        all_chunks = get_chunks_for_region(content_type=obj.content_type,
                                           content_id=obj.content_id,
                                           region=new_region)
        # find all the existing objects and iterate over each of them,
        # doing an update (rather than save, to avoid changing the `modified`
        # field) if they're not in the correct position.
        for new_position, obj in enumerate(all_chunks.iterator(), 1):
            if obj.position != new_position:
                get_chunks_for_region(pk=obj.pk).update(position=new_position)

        # having moved region, update the old one to fix the contiguous
        # positions, hopefully just by shifting them all up 1.
        if old_chunks is not None:
            old_chunks.update(position=F('position') - 1)
        return obj

    def change_message(self):
        obj = self.cleaned_data['pk']
        data = (obj.position, obj.region)
        msg = 'Moved to position %d in region "%s"' % data
        return obj, msg

    def parent_change_message(self):
        obj = self.cleaned_data['pk']
        data = (force_unicode(obj._meta.verbose_name), obj.pk, obj.position,
                obj.region)
        msg = 'Moved %s (pk:%s) to position %d in region "%s"' % data
        return obj.content_object, msg

    class Meta:
        model = EditRegionChunk
