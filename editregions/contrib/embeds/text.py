# -*- coding: utf-8 -*-
# All the text strings we need to mark for translation go in here.
# By putting them here, we can keep everything nice and tidy, and, bonus, we don't
# have to jump through long-winded hoops to get the verbose_name from a Model
# to be the label for an overridden Form field.
from __future__ import unicode_literals
from django.utils.translation import ugettext_lazy as _

iframe_vname = _('iframe')
iframe_vname_plural = _('iframes')
iframe_url_label = _('web address')
iframe_url_help = _('Required. The URL for the content you want to embed.')
iframe_dimensions_help = _('Optional. If the website allows for it, may be'
                           'used to set the dimensions of this iframe.')
iframe_name_label = _('HTML name')
iframe_name_help = _('Optional. May be used to reference the element in '
                     'JavaScript, or as the target for a link or form.')

iframe_details_fieldset_label = _('iframe details')
dimensions_fieldset_label = _('iframe dimensions')

feed_url_label = iframe_url_label
feed_url_help = iframe_url_help

feed_cache_fieldset_label = _('caching')
feed_cache_for_label = _('stale after')
feed_cache_for_help = _("Save the data into the server's cache for a period of "
                        "time, allowing the page to respond faster. After the "
                        "period has elapsed, the next page request will fetch "
                        "any new data.")

feed_vname = _('web feed')
feed_vname_plural = _('web feeds')

feed_cache_day = _('One day')
feed_cache_hday = _('Twelve hours')
feed_cache_qday = _('Six hours')
feed_cache_hour = _('One hour')


js_vname = _("JavaScript")
js_vname_plural = _("JavaScripts")
