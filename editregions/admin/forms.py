# -*- coding: utf-8 -*-
from django.forms import Form, Media
from django.forms.util import ErrorList
from django.forms.fields import TypedChoiceField
from editregions.models import EditRegionChunk
from editregions.admin.utils import shared_media


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
    model = EditRegionChunk
    region = TypedChoiceField(coerce=unicode, choices=())

    def __init__(self, region, *args, **kwargs):
        super(MovementForm, self).__init__(*args, **kwargs)
        self.fields['region'].choices = ((1, 1,), (2, 2),)
