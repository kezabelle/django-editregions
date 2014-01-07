# -*- coding: utf-8 -*-
import logging
from django.contrib.contenttypes.generic import GenericInlineModelAdmin
from editregions.admin.forms import EditRegionInlineFormSet
from editregions.constants import REQUEST_VAR_CT, REQUEST_VAR_ID
from editregions.models import EditRegionChunk, EditRegionConfiguration
from editregions.utils.data import (get_modeladmin, attach_configuration,
                                    get_configuration)

logger = logging.getLogger(__name__)


class EditRegionInline(GenericInlineModelAdmin):
    model = EditRegionChunk
    can_delete = False
    extra = 0
    max_num = 0
    ct_field = REQUEST_VAR_CT
    ct_fk_field = REQUEST_VAR_ID
    template = 'admin/editregions/edit_inline/none.html'

    def get_formset(self, request, obj=None, **kwargs):
        # sidestep validation which wants to inherit from BaseModelFormSet
        self.formset = EditRegionInlineFormSet
        fset = super(EditRegionInline, self).get_formset(request, obj,
                                                         **kwargs)
        modeladmin = get_modeladmin(EditRegionChunk, self.admin_site.name)
        if obj is not None and request.method == 'POST':
            # As I won't remember why we have to do this, later, this is the
            # traceback which not doing it caused:
            # https://gist.github.com/kezabelle/40653a0ad1ffd8fc77ba
            # Basically, the template gets changed half way through the request
            # because of the different points at which objects are saved.
            # By not relying on the new instance (with the changed template)
            # instead using the one in the DB (with the old template) we can
            # ensure the regions line up correctly.
            logger.info('Editing an %(obj)r; we may be changing the region '
                        'group being used, so re-grabbing the DB version')
            obj = obj.__class__.objects.get(pk=obj.pk)
        config = None
        if obj is not None:
            attach_configuration(obj, EditRegionConfiguration)
            config = get_configuration(obj)
            fset.has_editregions = config.has_configuration
        fset.region_changelists = modeladmin.get_changelists_for_object(
            request=request, obj=obj, config=config)
        return fset

    def get_fieldsets(self, *args, **kwargs):
        """
        avoid re-calling get_formset()
        """
        # res = super(EditRegionInline, self).get_fieldsets(*args, **kwargs)
        return [(None, {'fields': ['region', 'position']})]
