# -*- coding: utf-8 -*-
from django.core.exceptions import ValidationError
from django.forms import Form, Media
from django.forms.util import ErrorList
from django.forms.fields import TypedChoiceField, IntegerField
from editregions.models import EditRegionChunk
from editregions.admin.utils import shared_media
from editregions.utils.chunks import get_chunks_for_region
from editregions.utils.regions import validate_region_name, get_pretty_region_name


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
    region = TypedChoiceField(coerce=unicode, choices=(), required=False,
                              validators=[validate_region_name])
    obj_cache = None

    def __init__(self, *args, **kwargs):
        super(MovementForm, self).__init__(*args, **kwargs)
        # set the choices to be anything in the database already.
        # TODO: refactor this to be only regions available on the current template
        self.fields['region'].choices = ((x.region, get_pretty_region_name(x.region))
                                         for x in self.Meta.model.objects.all().only('region'))
        try:
            self.fields['pk'].max_value = (self.Meta.model.objects.all().only('pk')
                                           .order_by('-pk')[0].pk)
        except IndexError as e:
            # there probably aren't any objects in the DB yet, so the only thing
            # to move about is the minimum ... I think.
            self.fields['pk'].max_value = self.fields['pk'].min_value

        # TODO: maximum position should be count() of those in region for this
        # minus 1, I think.

    def clean_pk(self):
        """
        Checks we received a valid object identifier.
        """
        pk = self.cleaned_data.get('pk', 0)
        try:
            obj = self.Meta.model.objects.get(pk=pk).only('content_type',
                                                          'content_id', 'pk',
                                                          'region', 'position')
            self.obj_cache = obj
            return obj
        except self.Meta.model.DoesNotExist as e:
            raise ValidationError(e.msg)

    def save(self):
        """
        Updates the current object, and all other objects in the same region.
        """
        obj = self.cleaned_data['pk']
        obj.position = self.cleaned_data['position']
        obj.region = self.cleaned_data['region']

        chunks = get_chunks_for_region(content_type=obj.content_type,
                                       content_id=obj.content_id,
                                       region=obj.region)
        for position, chunk in enumerate(chunks, start=1):
            if position >= obj.position:
                chunk.position = obj.position + position
            else:
                chunk.position = position
            chunk.save()
        obj.save()
        return obj

    class Meta:
        model = EditRegionChunk
