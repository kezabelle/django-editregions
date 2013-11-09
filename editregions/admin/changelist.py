# -*- coding: utf-8 -*-
import logging

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from editregions.constants import (REQUEST_VAR_REGION, REQUEST_VAR_CT,
                                   REQUEST_VAR_ID)
from django.contrib.admin.views.main import ChangeList
from editregions.utils.data import get_content_type
from editregions.models import EditRegionConfiguration


logger = logging.getLogger(__name__)


class EditRegionChangeList(ChangeList):

    def __init__(self, *args, **kwargs):
        """
        Stash a bunch of extra stuff on the changelist. Note that this used to
        be inlined in the EditRegionChunk ModelAdmin.
        """
        super(EditRegionChangeList, self).__init__(*args, **kwargs)
        try:
            request = kwargs['request']
            logger.debug('"request" taken from kwargs')
        except KeyError as e:
            request = args[0]
            logger.debug('"request" assumed to be in args')

        self.available_chunks = self.model_admin.get_changelist_filters(request.GET)
        self.formset = None
        self.region = request.GET.get(REQUEST_VAR_REGION, None)
        self.parent_content_type = request.GET.get(REQUEST_VAR_CT, None)
        self.parent_content_id = request.GET.get(REQUEST_VAR_ID, None)
        self.querydict = request.GET.copy()

        parent_obj = (get_content_type(self.parent_content_type).model_class()
                      .objects.get(pk=self.parent_content_id))
        erc = EditRegionConfiguration(parent_obj)
        self.template = erc.template
        self.get_region_display = erc.config[self.region]['name']
