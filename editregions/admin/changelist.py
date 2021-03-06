# -*- coding: utf-8 -*-
import logging

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from editregions.admin.utils import AdminChunkWrapper
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
        configured_region = parent_erc.config.get(self.region, {})
        self.get_region_display = configured_region.get('name', 'ERROR')

    def __repr__(self):
        return ('<{x.__module__}.{x.__class__.__name__} '
                'region={x.region}, '
                'parent_content_type={x.parent_content_type}, '
                'parent_content_id={x.parent_content_id}, '
                'region_display={x.get_region_display}>').format(x=self)

    def get_changelist_filters(self, request_querydict, obj, conf):
        """
        Get the list of chunks for the changelist sidebar.
        Should only get called with a decent querydict, hopefully.

        :return: list of available chunk types
        """
        filters = ()
        # make sure the region exists, that it has values, and that it has
        # a models key.
        can_get_models = (self.region in conf.config,
                          conf.config.get(self.region, False),
                          conf.config.get(self.region, {}).get('models'))
        if all(can_get_models):
            filters = list(AdminChunkWrapper(**{
                'opts': x._meta,
                'namespace': self.model_admin.admin_site.name,
                'region': self.region,
                'content_type': self.parent_content_type,
                'content_id': obj.pk,
            }) for x in conf.config[self.region]['models'])
        if len(filters) == 0:
            msg = "region '{region}' has zero chunk types configured".format(
                region=self.region)
            logger.warning(msg)
        return filters
