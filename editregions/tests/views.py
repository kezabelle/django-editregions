# -*- coding: utf-8 -*-
from django.http import HttpResponsePermanentRedirect, HttpResponseRedirect
from django.test import RequestFactory
from django.utils.unittest.case import TestCase
from editregions.views import FormSuccess, EditRegionResponseMixin


class PermanentRedirect(object):
    permanent = True
    message = 'HELLO'

    def render_to_response(self, *args, **kwargs):
        raise FormSuccess('http://example.com/', msg=self.message,
                          permanent=self.permanent)


class TemporaryRedirect(PermanentRedirect):
    permanent = False
    message = None


class FakeViewA(EditRegionResponseMixin, PermanentRedirect):
    pass


class FakeViewB(EditRegionResponseMixin, TemporaryRedirect):
    pass


class FormSuccessTestCase(TestCase):
    def test_usage(self):
        def _raiser():
            raise FormSuccess('http://example.com/', permanent=False)
        self.assertRaises(FormSuccess, callableObj=_raiser)


class EditRegionResponseMixinTestCase(TestCase):
    def test_redirection(self):
        view = FakeViewA()
        view.request = RequestFactory().get('/')
        response = view.render_to_response(context={})
        self.assertIsInstance(response, HttpResponsePermanentRedirect)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response['Location'], 'http://example.com/')

    def test_redirection_no_message(self):
        view = FakeViewB()
        view.request = RequestFactory().get('/')
        response = view.render_to_response(context={})
        self.assertIsInstance(response, HttpResponseRedirect)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], 'http://example.com/')
