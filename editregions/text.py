# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.translation import ugettext_lazy as _
from helpfulfields.text import modified_label

chunk_v = _('content block')
chunk_vplural = _('content blocks')

position_label = _('position')
position_help = _('position in which this content appears. 1 is highest.')
render_label = _('renderer')
render_help = _('how to render this chunk.')
# datetimes_fieldset_label = _('dates')

region_v = _('region')
region_vplural = _('regions')

#: Text for the exception raised by
#: :class:`~editregions.templatetags.editregion.EditRegionTag`. Only raised if
#: `DEBUG` is :data:`True`
ttag_no_obj = _('no object provided to the "%(tagname)s" template tag for'
                'region "%(region)s"')

#: Text for the exception raised by
#: :class:`~editregions.templatetags.editregion.EditRegionTag`. Only raised if
#: `DEBUG` is :data:`True`
ttag_not_model = _('"%(tagname)s" expected a Django model, got %(type)s'
                   'instead')

ttag_no_ancestors = _('%(obj)s must have `%(attr)s` to continue using'
                      '`%(thing)s`')

admin_chunktype_label = _('type')
admin_summary_label = _('summary')
admin_position_label = _('#')
admin_modified_label = modified_label
