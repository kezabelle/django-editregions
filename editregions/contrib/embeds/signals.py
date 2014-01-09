# -*- coding: utf-8 -*-
from django.dispatch import Signal

feed_request_started = Signal(providing_args=['instance'])
feed_request_finished = Signal(providing_args=['instance', 'feed'])
