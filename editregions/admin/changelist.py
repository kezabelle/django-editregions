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
        parent_erc = kwargs.pop('parent_conf')
        parent_obj = kwargs.pop('parent_obj')
        super(EditRegionChangeList, self).__init__(*args, **kwargs)
        request = kwargs.pop('request')

        self.region = request.GET.get(REQUEST_VAR_REGION, None)
        self.parent_content_type = request.GET.get(REQUEST_VAR_CT, None)
        self.parent_content_id = request.GET.get(REQUEST_VAR_ID, None)

        self.available_chunks = self.get_changelist_filters(
            request_querydict=request.GET, obj=parent_obj, conf=parent_erc)
        self.formset = None
        self.template = parent_erc.template
        self.get_region_display = parent_erc.config[self.region]['name']

    def get_changelist_filters(self, request_querydict, obj, conf):
        """
        Get the list of chunks for the changelist sidebar.
        Should only get called with a decent querydict, hopefully.

        :return: list of available chunk types
        """
        assert str(obj.pk) == str(self.parent_content_id), "Hmmm"

        AdminChunkWrapper = self.model_admin.get_admin_wrapper_class()
        if 'models' in conf.config[self.region]:
            filters = list(AdminChunkWrapper(**{
                'opts': x._meta,
                'namespace': self.model_admin.admin_site.app_name,
                'region': self.region,
                'content_type': self.parent_content_type,
                'content_id': obj.pk,
            }) for x in conf.config[self.region]['models'])
        else:
            filters = ()
        if len(filters) == 0:
            msg = "region '{region}' has zero chunk types configured".format(
                region=self.region)
            logger.warning(msg)
        return filters
