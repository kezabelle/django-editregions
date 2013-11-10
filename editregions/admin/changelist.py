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
        try:
            request = kwargs['request']
            logger.debug('"request" taken from kwargs')
        except KeyError as e:
            request = args[0]
            logger.debug('"request" assumed to be in args')

        self.available_chunks = self.get_changelist_filters(
            request_querydict=request.GET, obj=parent_obj, conf=parent_erc)
        self.formset = None
        self.region = request.GET.get(REQUEST_VAR_REGION, None)
        self.parent_content_type = request.GET.get(REQUEST_VAR_CT, None)
        self.parent_content_id = request.GET.get(REQUEST_VAR_ID, None)
        self.querydict = request.GET.copy()

        # parent_obj = (get_content_type(self.parent_content_type).model_class()
        #               .objects.get(pk=self.parent_content_id))
        self.template = parent_erc.template
        self.get_region_display = parent_erc.config[self.region]['name']
        # self.query_set = self.query_set.select_subclasses()

    def get_changelist_filters(self, request_querydict, obj, conf):
        """
        Get the list of chunks for the changelist sidebar.
        Should only get called with a decent querydict, hopefully.

        :return: list of available chunk types
        """
        region = request_querydict[REQUEST_VAR_REGION]
        ct = request_querydict[REQUEST_VAR_CT]
        # pk = request_querydict[REQUEST_VAR_ID]
        # try:
        #     parent_obj = get_model_class(ct).objects.get(pk=pk)
        # except ObjectDoesNotExist as e:
        #     return HttpResponseBadRequest('something went wrong')
        # erc = EditRegionConfiguration(parent_obj)
        AdminChunkWrapper = self.model_admin.get_admin_wrapper_class()
        filters = [AdminChunkWrapper(**{
            'opts': x._meta,
            'namespace': self.model_admin.admin_site.app_name,
            'region': region,
            'content_type': ct,
            'content_id': obj.pk,
        }) for x in conf.config[region]['models']]
        if len(filters) == 0:
            msg = "region '{region}' has zero chunk types configured".format(
                region=region)
            logger.warning(msg)
        return filters
