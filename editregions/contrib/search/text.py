# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.translation import ugettext_lazy as _

advanced_options_label = _("advanced options")
max_num_label = _("display")
max_num_help = _("maximum number of items to render.")

connection_label = _("connection")
connection_help = _("which of the available search connections to use")

request_objects_label = _("fetch objects")
request_objects_help = _("if the template requires access to the database "
                         "objects, tick this to efficiently fetch the objects "
                         "up front.")

query_label = _("search for")
query_help = _("the search terms (or complex query) to use when finding the "
               "best matches.")

boost_label = _("prioritise")
boost_help = _("comma separated list of words which should be considered more "
               "important, when sorting the best matches.")
csv_validator_error = _("prioritised words should be comma separated")
