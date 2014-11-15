# -*- coding: utf-8 -*-
import logging
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import F
from django.forms import Form, Media
try:
    from django.forms.utils import ErrorList
except ImportError:  # < Django 1.7 ... pragma: no cover
    from django.forms.util import ErrorList
from django.forms.fields import IntegerField, CharField
try:
    from django.utils.encoding import force_text
except ImportError:  # pragma: no cover ... < Django 1.5
    from django.utils.encoding import force_unicode as force_text
from editregions.utils.data import attach_configuration, get_configuration
from editregions.models import EditRegionChunk, EditRegionConfiguration
from editregions.admin.utils import shared_media
from editregions.utils.regions import validate_region_name

logger = logging.getLogger(__name__)


class EditRegionInlineForm(object):
    """
    Used by EditRegionInlineFormSet
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
    position = IntegerField(min_value=0)
    #: if region is set, then we're probably in an inline'd changelist, and
    #: we may be wanting to move region ...
    region = CharField(required=False, validators=[validate_region_name])

    def __init__(self, *args, **kwargs):
        super(MovementForm, self).__init__(*args, **kwargs)
        self.fields['pk'].max_value = self.get_model().objects.all().count()

    def get_model(self):
        return EditRegionChunk

    def clean(self):
        cd = super(MovementForm, self).clean()
        pk = cd.get('pk', None)
        model = self.get_model()
        try:
            if pk is None:
                raise model.DoesNotExist("Don't even bother querying")
            cd['pk'] = model.objects.get(pk=pk)
        except model.DoesNotExist as e:
            cd['pk'] = None
            name = force_text(self.get_model()._meta.verbose_name)
            msg = '{0} does not exist'.format(name)
            self._errors['pk'] = msg

        # rather than raise an error for an invalid region, just set it
        # back to whatever the region says it should be. Trust no-one.
        if 'region' in cd and cd['pk'] is not None:
            attach_configuration(cd['pk'].content_object,
                                 EditRegionConfiguration)
            erc = get_configuration(cd['pk'].content_object)
            if cd['region'] not in erc.config:
                msg = '{0} is not a valid region'.format(cd['region'])
                self._errors['region'] = msg
        return cd

    def save(self):
        """
        Updates the current object, and all other objects in the same region.
        """
        obj = self.cleaned_data['pk']
        old_position = obj.position
        old_region = obj.region
        new_position = max(self.cleaned_data['position'], 0)
        new_region = self.cleaned_data.get('region', old_region)
        return self.get_model().objects.move(
            obj=obj, from_position=old_position, to_position=new_position,
            from_region=old_region, to_region=new_region)

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
