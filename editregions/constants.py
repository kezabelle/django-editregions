# -*- coding: utf-8 -*-
from django.conf import settings

# Configuration dictionary for all regions.
# May be an empty dictionary, or a complex data structure following the following
# conventions, largely inspired by the CMS_PLACEHOLDER_CONF from `django-CMS`:
# EDIT_REGIONS = {
#     'template_region_name': _('Pretty, localized region name'),
#     'chunks': {
#         'ChunkType1': None,
#         'ChunkType2SonOfChunk': 3,
#         'Chunk3': 14,
#     }
# }
# Note that it differs by having the `limits` and `plugins` merged into one
# dictionary, whose keys are chunks/plugins, and whose values are the maximum
# allowed in the region. None is a special value to indicate infinity.
EDIT_REGIONS = getattr(settings, 'EDIT_REGIONS', {})

