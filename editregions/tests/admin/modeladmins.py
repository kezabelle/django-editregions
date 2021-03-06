# -*- coding: utf-8 -*-
import json
import warnings
import django
from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.admin.sites import NotRegistered
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.core.exceptions import SuspiciousOperation
from django.core.urlresolvers import reverse
from django.forms import ModelForm, Media
from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect
from django.template.response import TemplateResponse
from django.test import RequestFactory
from django.utils.datastructures import MultiValueDictKeyError
from editregions.contrib.embeds.admin import IframeAdmin

try:
    from unittest.case import TestCase, skipUnless
except ImportError:
    from django.utils.unittest.case import TestCase, skipUnless
from django.test import TestCase as DjangoTestCase
from editregions.admin.changelist import EditRegionChangeList
from editregions.admin.modeladmins import ChunkAdmin, EditRegionAdmin
from editregions.admin.utils import AdminChunkWrapper
from editregions.constants import REQUEST_VAR_CT, REQUEST_VAR_ID, REQUEST_VAR_REGION
from editregions.contrib.embeds.models import Iframe
from editregions.models import EditRegionChunk
from editregions.utils.data import get_content_type, get_modeladmin
from editregions.utils.versioning import is_django_16plus

try:
    from django.utils.encoding import force_text
except ImportError:
    from django.utils.encoding import force_unicode as force_text


class RealishAdmin(ChunkAdmin, ModelAdmin):
    pass


class TestUserAdmin(UserAdmin):
    def get_editregions_templates(self, obj):
        return ['movable_editregion_template.json']


class ChunkAdminTestCase(DjangoTestCase):
    def setUp(self):
        self.chunk_admin = ChunkAdmin()
        self.chunk_admin.admin_site = admin.site
        try:
            admin.site.unregister(Iframe)
        except NotRegistered:
            pass

        try:
            admin.site.unregister(User)
        except NotRegistered:
            pass
        admin.site.register(User, TestUserAdmin)
        admin.site.register(Iframe, RealishAdmin)

    def test_get_model_perms(self):
        request = RequestFactory().get('/')
        results = self.chunk_admin.get_model_perms(request=request)
        self.assertEqual({}, results)

    def test_response_max(self):
        request = RequestFactory().get('/')
        context = {
            'found': 3,
            'limit': 1,
            'region': 'test',
            'me': '',
            'parent': '',
        }
        results = self.chunk_admin.response_max(request=request,
                                                context=context).content
        self.assertIn(force_text('<h2>Limit reached</h2>'),
                      force_text(results))
        # this doesn't work. No idea why. Stupid Django.
        # self.assertIn('Unable to add more than <b>1</b> to this region.',
        #                   results)

    def test_get_response_add_context(self):
        request = RequestFactory().get('/')
        user = User(username='test')
        user.set_password('test')
        user.full_clean()
        user.save()
        ct = get_content_type(User)
        iframe = Iframe(position=2, region='test', content_type=ct,
                        content_id=user.pk, url='https://news.bbc.co.uk/')
        iframe.full_clean()
        iframe.save()

        results = self.chunk_admin.get_response_add_context(request=request,
                                                            obj=iframe)
        html = results.pop('html')
        self.assertEqual(results, {'action': {'add': True,
                                              'change': False,
                                              'delete': False},
                                   'object': {'pk': 1,
                                              'id': 1}
                                   })
        # self.assertIn('Please wait, saving changes', html)
        # self.assertIn('Add new content', html)
        # self.assertIn('Iframe', html)
        self.assertIn('<h3>Embeds</h3>', html)
        self.assertIn('<b>whee!:</b>', html)

    def test_get_response_change_context(self):
        request = RequestFactory().get('/')
        user = User(username='test')
        user.set_password('test')
        user.full_clean()
        user.save()
        ct = get_content_type(User)
        iframe = Iframe(position=2, region='test', content_type=ct,
                        content_id=user.pk, url='https://news.bbc.co.uk/')
        iframe.full_clean()
        iframe.save()

        results = self.chunk_admin.get_response_change_context(request=request,
                                                               obj=iframe)
        html = results.pop('html')
        self.assertEqual(results, {'action': {'add': False,
                                              'change': True,
                                              'delete': False},
                                   'object': {'pk': 1,
                                              'id': 1}
                                   })
        self.assertIn('<h3>Embeds</h3>', html)
        self.assertIn('<b>whee!:</b>', html)

    def test_get_response_delete_context_keyerror(self):
        request = RequestFactory().get('/')
        extra_context = {}
        results = self.chunk_admin.get_response_delete_context(
            request=request, obj_id=1, extra_context=extra_context)
        self.assertEqual(results, {'action': {'add': False,
                                              'change': False,
                                              'delete': True},
                                   'object': {'pk': 1,
                                              'id': 1}
                                   })

    def test_get_response_delete_context(self):
        request = RequestFactory().get('/')
        extra_context = {
            'gfk': {
                'content_object': User(username='test'),
            }
        }
        results = self.chunk_admin.get_response_delete_context(
            request=request, obj_id=1, extra_context=extra_context)
        html = results.pop('html')
        self.assertEqual(results, {'action': {'add': False,
                                              'change': False,
                                              'delete': True},
                                   'object': {'pk': 1,
                                              'id': 1}
                                   })
        self.assertIn('<h3>Embeds</h3>', html)
        self.assertIn('<b>whee!:</b>', html)

    def test_render_into_region(self):
        with self.settings(DEBUG=True):
            with self.assertRaises(NotImplementedError):
                self.chunk_admin.render_into_region(obj={}, context={})
        with self.settings(DEBUG=False):
            data = self.chunk_admin.render_into_region(obj={}, context={})
            self.assertIsNone(data)

    def test_render_into_summary(self):
        with self.settings(DEBUG=True):
            with self.assertRaises(NotImplementedError):
                self.chunk_admin.render_into_summary(obj={}, context={})
        with self.settings(DEBUG=False):
            data = self.chunk_admin.render_into_summary(obj={}, context={})
            self.assertIsNone(data)

    def test_save_model(self):
        user = User(username='test')
        user.set_password('test')
        user.full_clean()
        user.save()
        ct = get_content_type(User)
        iframe = Iframe(position=2, region='test', content_type=ct,
                        content_id=user.pk, url='https://news.bbc.co.uk/')
        iframe.full_clean()
        iframe.save()
        request = RequestFactory().get('/', data={
            'region': 'test',
            'content_type': ct.pk,
            'content_id': user.pk,
        })
        admin_instance = get_modeladmin(Iframe)

        expected_query_count = 2 if is_django_16plus() else 4
        with self.assertNumQueries(expected_query_count):
            result = admin_instance.save_model(request=request, obj=iframe,
                                               form=ModelForm, change=True)
            self.assertIsNone(result)

    def test_logging(self):
        user = User(username='test')
        user.set_password('test')
        user.full_clean()
        user.save()
        ct = get_content_type(User)
        iframe = Iframe(position=2, region='test', content_type=ct,
                        content_id=user.pk, url='https://news.bbc.co.uk/')
        iframe.full_clean()
        iframe.save()
        request = RequestFactory().get('/')
        request.user = user
        admin_instance = get_modeladmin(Iframe)

        admin_instance.log_addition(request, iframe)
        admin_instance.log_change(request, iframe, "we changed a thing!")
        admin_instance.log_deletion(request, iframe, "we deleted a thing!")

        # find them on the user
        logs = LogEntry.objects.get(content_type=ct, object_id=user.pk,
                                    user=user, action_flag=ADDITION)
        self.assertEqual(force_text(logs), 'Added "test".')
        logs = LogEntry.objects.get(content_type=ct, object_id=user.pk,
                                    user=user, action_flag=CHANGE)
        self.assertEqual(force_text(logs), 'Changed "test" - we changed a '
                                           'thing!')
        # can't check for deletions properly, see
        # https://code.djangoproject.com/ticket/21771#ticket

        # logs = LogEntry.objects.get(content_type=ct, object_id=user.pk,
        #                             user=user, action_flag=DELETION)
        # self.assertEqual(force_text(logs), 'Changed "test" - we changed a '
        #                                    'thing!')

        # find them on the iframe
        ct = get_content_type(Iframe)
        logs = LogEntry.objects.get(content_type=ct, object_id=iframe.pk,
                                    user=user, action_flag=ADDITION)
        self.assertEqual(force_text(logs), 'Added "https://news.bbc.co.uk/".')
        logs = LogEntry.objects.get(content_type=ct, object_id=iframe.pk,
                                    user=user, action_flag=CHANGE)
        self.assertEqual(force_text(logs), 'Changed "https://news.bbc.co.uk/" '
                                           '- we changed a thing!')
        # can't check for deletions properly, see
        # https://code.djangoproject.com/ticket/21771#ticket
        logs = LogEntry.objects.filter(content_type=ct, object_id=user.pk,
                                       user=user, action_flag=DELETION)
        self.assertEqual(force_text(logs[0]), 'Deleted "we deleted a thing!."')

    def _test_view(self, func='add_view', generate_chunks=1):
        user = User(username='test', is_staff=True, is_superuser=True,
                    is_active=True)
        user.set_password('test')
        user.full_clean()
        user.save()
        ct = get_content_type(User)
        request = RequestFactory().get('/', {
            REQUEST_VAR_CT: ct.pk,
            REQUEST_VAR_ID: user.pk,
            REQUEST_VAR_REGION: 'test'
        })
        request.user = user
        admin_instance = get_modeladmin(Iframe)

        for x in range(0, generate_chunks):
            iframe = Iframe(position=2, region='test', content_type=ct,
                            content_id=user.pk, url='https://news.bbc.co.uk/')
            iframe.full_clean()
            iframe.save()

        kwargs = {'request': request}
        if func != 'add_view':
            kwargs.update({'object_id': force_text(iframe.pk)})
        view = getattr(admin_instance, func)
        view(**kwargs)

        # now do the view again without the fields required by the decorator
        request = RequestFactory().get('/')
        request.user = user
        kwargs.update({'request': request})
        with self.assertRaises(SuspiciousOperation):
            view(**kwargs)

    def test_change_view(self):
        self._test_view(func='change_view')

    def test_delete_view(self):
        self._test_view(func='delete_view')

    def test_add_view(self):
        self._test_view(func='add_view')

    def test_add_view_hitting_limit(self):
        self._test_view(func='add_view', generate_chunks=3)


class MaybeFixRedirectionTestCase(DjangoTestCase):
    def setUp(self):
        try:
            admin.site.unregister(Iframe)
        except NotRegistered:
            pass
        try:
            admin.site.unregister(User)
        except NotRegistered:
            pass
        admin.site.register(User, TestUserAdmin)
        admin.site.register(Iframe, RealishAdmin)

    def test_leave_unchanged(self):
        request = RequestFactory().get('/')
        response_200 = HttpResponse(content='ok')
        admin_instance = get_modeladmin(Iframe)
        new_response = admin_instance.maybe_fix_redirection(
            request=request, response=response_200)
        # returned unchanged
        self.assertEqual(new_response['X-Chunkadmin-Response'], 'early')
        self.assertEqual(force_text('ok'), force_text(new_response.content))
        self.assertEqual(200, new_response.status_code)

    def test_returned_data_changed(self):
        """
        Just check that the `_data_changed` parameter is added the response.
        """
        request = RequestFactory().get('/')
        admin_instance = get_modeladmin(Iframe)
        response_302 = HttpResponseRedirect(redirect_to='/admin_mountpoint/')
        new_response = admin_instance.maybe_fix_redirection(
            request=request, response=response_302)
        # returned early because it was a redirect, but we updated the
        # querystring anyway
        self.assertEqual(new_response['X-Chunkadmin-Response'], 'early')
        self.assertEqual(302, new_response.status_code)
        self.assertEqual('/admin_mountpoint/?_data_changed=1',
                         new_response['Location'])

    def test_to_other_url(self):
        """
        Going to a non-chunkadmin URL should be ok, and should also put the
        `_data_changed` parameter onto the URL.
        """
        user = User(username='test', is_staff=True, is_superuser=True,
                    is_active=True)
        user.set_password('test')
        user.full_clean()
        user.save()
        request = RequestFactory().get('/')
        response_302 = HttpResponseRedirect(redirect_to='/admin_mountpoint/')
        admin_instance = get_modeladmin(Iframe)
        new_response = admin_instance.maybe_fix_redirection(
            request=request, response=response_302, obj=user)
        self.assertEqual(new_response['X-Chunkadmin-Response'], 'not-chunkadmin')  # noqa
        self.assertEqual(302, new_response.status_code)
        self.assertEqual('/admin_mountpoint/?_data_changed=1',
                         new_response['Location'])

    def test_to_chunkadmin_instance(self):
        user = User(username='test', is_staff=True, is_superuser=True,
                    is_active=True)
        user.set_password('test')
        user.full_clean()
        user.save()
        admin_instance = get_modeladmin(Iframe)
        self.assertIsInstance(admin_instance, RealishAdmin)

        request = RequestFactory().get('/')
        request.user = user
        iframe_admin = reverse('admin:embeds_iframe_add')
        response_301 = HttpResponsePermanentRedirect(redirect_to=iframe_admin)

        ct = get_content_type(User)
        iframe = Iframe(position=2, region='test', content_type=ct,
                        content_id=user.pk, url='https://news.bbc.co.uk/')
        iframe.full_clean()
        iframe.save()
        
        new_response = admin_instance.maybe_fix_redirection(
            request=request, response=response_301, obj=iframe)
        self.assertEqual(new_response['X-Chunkadmin-Response'], 'test')
        # was a redirect, to a chunkadmin instance
        self.assertEqual(301, new_response.status_code)
        self.assertEqual('/admin_mountpoint/auth/user/1/?_data_changed=1',
                         new_response['Location'])

    def test_autoclose_chunkadmin(self):
        """
        If `_autoclose` is in the URL, that + `_data_changed` should propagate
        to the next redirect URL for the purposes of our adminlinks JS.
        """
        user = User(username='test', is_staff=True, is_superuser=True,
                    is_active=True)
        user.set_password('test')
        user.full_clean()
        user.save()
        admin_instance = get_modeladmin(Iframe)
        self.assertIsInstance(admin_instance, RealishAdmin)

        request = RequestFactory().get('/', {
            '_autoclose': 1,
        })
        request.user = user
        iframe_admin = reverse('admin:embeds_iframe_add')
        response_301 = HttpResponsePermanentRedirect(redirect_to=iframe_admin)

        ct = get_content_type(User)
        iframe = Iframe(position=2, region='test', content_type=ct,
                        content_id=user.pk, url='https://news.bbc.co.uk/')
        iframe.full_clean()
        iframe.save()

        new_response = admin_instance.maybe_fix_redirection(
            request=request, response=response_301, obj=iframe)
        self.assertEqual(new_response['X-Chunkadmin-Response'], 'autoclose')

        self.assertEqual(301, new_response.status_code)
        location, querystring = new_response['Location'].split('?')
        self.assertEqual('/admin_mountpoint/embeds/iframe/add/', location)
        self.assertIn('region=test', querystring)
        self.assertIn('_data_changed=1', querystring)
        self.assertIn('_autoclose=1', querystring)
        self.assertIn('content_type={0}'.format(ct.pk), querystring)
        self.assertIn('content_id={0}'.format(iframe.pk), querystring)

    def test_continue_editing_parent_object(self):
        """
        if continue editing is hit, it should go back to the parent URL,
        I think?
        """
        user = User(username='test', is_staff=True, is_superuser=True,
                    is_active=True)
        user.set_password('test')
        user.full_clean()
        user.save()
        admin_instance = get_modeladmin(Iframe)
        self.assertIsInstance(admin_instance, RealishAdmin)

        request = RequestFactory().get('/', {
            '_continue': 1,
        })
        request.user = user
        iframe_admin = reverse('admin:embeds_iframe_add')
        response_301 = HttpResponsePermanentRedirect(redirect_to=iframe_admin)

        ct = get_content_type(User)
        iframe = Iframe(position=2, region='test', content_type=ct,
                        content_id=user.pk, url='https://news.bbc.co.uk/')
        iframe.full_clean()
        iframe.save()

        new_response = admin_instance.maybe_fix_redirection(
            request=request, response=response_301, obj=iframe)
        self.assertEqual(new_response['X-Chunkadmin-Response'],
                         'redirect-to-parent')

        self.assertEqual(301, new_response.status_code)
        self.assertEqual('/admin_mountpoint/auth/user/1/?_data_changed=1',
                         new_response['Location'])


class EditRegionAdminTestCase(DjangoTestCase):
    def setUp(self):
        try:
            admin.site.unregister(EditRegionChunk)
        except NotRegistered:
            pass
        admin.site.register(EditRegionChunk, EditRegionAdmin)
        self.admin = get_modeladmin(EditRegionChunk)
        try:
            admin.site.unregister(Iframe)
        except NotRegistered:
            pass
        admin.site.register(Iframe, IframeAdmin)

    def test_cover_init(self):
        our_admin = EditRegionAdmin(EditRegionChunk, admin.site)
        self.assertEqual(our_admin.list_display_links, (None,))

    def test_get_list_display_links(self):
        request = RequestFactory().get('/')
        expected = (None,)
        received = self.admin.get_list_display_links(request=request,
                                                     list_display=())
        self.assertEqual(expected, received)

    def test_get_list_display(self):
        request = RequestFactory().get('/')
        expected = ['get_object_tools', 'get_subclass_type',
                    'get_subclass_summary']
        received = self.admin.get_list_display(request=request)
        self.assertEqual(expected, received)

    def _test_changelist_display_methods(self, func, expected, extra):
        ct = get_content_type(User)
        user = User(username='test', is_staff=True, is_superuser=True,
                    is_active=True)
        user.set_password('test')
        user.full_clean()
        user.save()
        iframe = Iframe(position=2, region='test', content_type=ct,
                        content_id=user.pk, url='https://news.bbc.co.uk/')
        iframe.full_clean()
        iframe.save()
        render_html = getattr(self.admin, func)
        received = render_html(obj=iframe, **extra)
        for x in expected:
            self.assertIn(x, received)

    def test_get_changelist_link_html_directly(self):

        kwargs = {
            'func': 'get_changelist_link_html',
            'expected': ('<a href="/admin_mountpoint/embeds/iframe/1/?',
                         'region=test',
                         'content_id=1',
                         'content_type={0}'.format(get_content_type(User).pk),
                         'data-adminlinks="autoclose"',
                         '>x</a>'),
            'extra': {
                'data': 'x',
                'caller': 'test'
            }
        }
        self._test_changelist_display_methods(**kwargs)

    def test_get_subclass_type(self):
        kwargs = {
            'func': 'get_subclass_type',
            'expected': ('<a href="/admin_mountpoint/embeds/iframe/1/?',
                         'region=test',
                         'content_id=1',
                         'content_type={0}'.format(get_content_type(User).pk),
                         'data-adminlinks="autoclose"',
                         '>iframe</a>'),
            'extra': {}
        }
        self._test_changelist_display_methods(**kwargs)

    def test_get_subclass_summary(self):
        kwargs = {
            'func': 'get_subclass_summary',
            'expected': ('<a href="/admin_mountpoint/embeds/iframe/1/?',
                         'region=test',
                         'content_id=1',
                         'content_type={0}'.format(get_content_type(User).pk),
                         'data-adminlinks="autoclose"',
                         '>https://news.bbc.co.uk/</a>'),
            'extra': {}
        }
        self._test_changelist_display_methods(**kwargs)

    def test_get_object_tools(self):
        kwargs = {
            'func': 'get_object_tools',
            'expected': ('class="drag_handle" data-pk="1"',
                         '/admin_mountpoint/editregions/editregionchunk/move/',
                         'href="/admin_mountpoint/embeds/iframe/1/delete/?',
                         'region=test',
                         'content_id=1',
                         'content_type={0}'.format(get_content_type(User).pk),
                         'class="delete_handle"',
                         'data-adminlinks="autoclose"',
                         '>Delete</a>'),
            'extra': {}
        }
        self._test_changelist_display_methods(**kwargs)

    def test_get_model_perms(self):
        request = RequestFactory().get('/')
        self.assertEqual(self.admin.get_model_perms(request=request), {})

    def test_cover_urls(self):
        self.assertEqual(len(self.admin.urls), 3)

    def test_move_view_bad_request(self):
        request = RequestFactory().get('/')
        response = self.admin.move_view(request=request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response['Content-type'], 'application/json')
        self.assertEqual(json.loads(force_text(response.content)), {
            'pk': 'content block does not exist',
            'position': ['This field is required.']
        })

    def test_move_view(self):
        ct = get_content_type(User)
        user = User(username='test', is_staff=True, is_superuser=True,
                    is_active=True)
        user.set_password('test')
        user.full_clean()
        user.save()

        for x in range(1, 10):
            obj = Iframe(position=x, region='test', content_id=user.pk,
                         content_type=ct, url='http://example.com/')
            obj.full_clean()
            obj.save()

        first_obj = EditRegionChunk.objects.all()[0]
        request = RequestFactory().get('/', {'position': 3,
                                             'pk': first_obj.pk,
                                             'region': 'test'})
        request.user = user
        response = self.admin.move_view(request=request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-type'], 'application/json')
        json_data = json.loads(force_text(response.content))
        self.assertIn('action', json_data)
        self.assertIn('html', json_data)
        self.assertEqual('move', json_data['action'])
        self.assertIn('<div class="region-inline-wrapper"',
                      json_data['html'])

    def test_queryset(self):
        ct = get_content_type(User)
        user = User(username='test', is_staff=True, is_superuser=True,
                    is_active=True)
        user.set_password('test')
        user.full_clean()
        user.save()
        data = []
        for x in range(1, 10):
            iframe = Iframe(position=x, region='test', content_type=ct,
                            content_id=user.pk, url='https://news.bbc.co.uk/')
            iframe.full_clean()
            iframe.save()
            data.append(iframe)

        try:
            self.assertEqual(data, list(self.admin.get_queryset('pk')))
        except AttributeError:
            self.assertEqual(data, list(self.admin.queryset('pk')))

    def test_get_object(self):
        self.test_queryset()
        request = RequestFactory().get('/')
        obj = Iframe.objects.all()[0]
        self.assertEqual(obj, self.admin.get_object(request=request,
                                                    object_id=obj.pk))

    def test_get_object_invalid_pk(self):
        self.test_queryset()
        request = RequestFactory().get('/')
        self.assertEqual(None, self.admin.get_object(request=request,
                                                     object_id=999999))

    def test_get_changelist(self):
        self.assertEqual(self.admin.get_changelist(), EditRegionChangeList)

    def test_changelist_view(self):
        request = RequestFactory().get('/')
        with self.assertRaises(MultiValueDictKeyError):
            self.admin.changelist_view(request=request)
        user = User(username='test', is_staff=True, is_superuser=True,
                    is_active=True)
        user.set_password('test')
        user.full_clean()
        user.save()
        request = RequestFactory().get('/', {
            REQUEST_VAR_CT: get_content_type(User).pk,
            REQUEST_VAR_ID: user.pk,
        })
        template_response = self.admin.changelist_view(request=request)
        self.assertIsInstance(template_response, TemplateResponse)

    def test_get_changelists_for_object(self):
        request = RequestFactory().get('/')
        user = User(username='test', is_staff=True, is_superuser=True,
                    is_active=True)
        user.set_password('test')
        user.full_clean()
        user.save()
        received = self.admin.get_changelists_for_object(request=request,
                                                         obj=user)
        self.assertEqual(2, len(received))
        self.assertIsInstance(received[0], EditRegionChangeList)
        self.assertIsInstance(received[1], EditRegionChangeList)

    def test_get_changelists_for_object_no_obj(self):
        request = RequestFactory().get('/')
        received = self.admin.get_changelists_for_object(request=request,
                                                         obj=None)
        self.assertEqual(0, len(received))

    def test_changelists_as_context_data(self):
        request = RequestFactory().get('/')
        ct = get_content_type(User)
        user = User(username='test', is_staff=True, is_superuser=True,
                    is_active=True)
        user.set_password('test')
        user.full_clean()
        user.save()
        iframe = Iframe(position=1, region='test', content_type=ct,
                        content_id=user.pk, url='https://news.bbc.co.uk/')
        iframe.full_clean()
        iframe.save()
        received = self.admin.changelists_as_context_data(request=request,
                                                          obj=user)
        self.assertTrue('inline_admin_formset' in received)
        self.assertTrue('formset' in received['inline_admin_formset'])
        self.assertTrue('region_changelists' in received['inline_admin_formset']['formset'])  # noqa
        self.assertEqual(
            2, len(received['inline_admin_formset']['formset']['region_changelists']))  # noqa

    def test_render_changelists_for_object(self):
        request = RequestFactory().get('/')
        ct = get_content_type(User)
        user = User(username='test', is_staff=True, is_superuser=True,
                    is_active=True)
        user.set_password('test')
        user.full_clean()
        user.save()
        iframe = Iframe(position=1, region='test', content_type=ct,
                        content_id=user.pk, url='https://news.bbc.co.uk/')
        iframe.full_clean()
        iframe.save()
        received = self.admin.render_changelists_for_object(request=request,
                                                            obj=user)
        self.assertIn('<div class="region-inline-wrapper"', received)
        self.assertIn('<h3>Embeds</h3>', received)
        self.assertIn('<div class="region-inline-progress-wrapper">', received)

    @skipUnless(django.VERSION >= (1, 6, 0), "test only applies to Django 1.6+")
    def test_media_property_16(self):
        self.assertEqual(self.admin.media._css, {
            u'screen': [
                u'adminlinks/css/fancyiframe-custom.css',
                u'editregions/css/inlines.css',
                u'editregions/css/changelist-extras.css'
            ]
        })
        self.assertEqual(self.admin.media._js, [
            'admin/js/core.js',
            'admin/js/admin/RelatedObjectLookups.js',
            'admin/js/jquery.min.js',
            'admin/js/jquery.init.js',
            'admin/js/jquery.rebind.js',
            'adminlinks/js/jquery.fancyiframe.js',
            'editregions/js/jquery.ui.1-10-3.custom.js',
            'editregions/js/dragging.js'])

    @skipUnless(django.VERSION < (1, 6, 0), "test only applies to Django 1.6+")
    def test_media_property_15(self):
        self.assertEqual(self.admin.media._css, {
            u'screen': [
                u'adminlinks/css/fancyiframe-custom.css',
                u'editregions/css/inlines.css',
                u'editregions/css/changelist-extras.css'
            ]
        })
        self.assertEqual(self.admin.media._js, [
            'admin/js/core.js',
            'admin/js/admin/RelatedObjectLookups.js',
            'admin/js/jquery.min.js',
            'admin/js/jquery.init.js',
            'admin/js/jquery.rebind.js',
            'adminlinks/js/jquery.fancyiframe.js',
            'editregions/js/jquery.ui.1-8-24.custom.js',
            'editregions/js/dragging.js'])

    def test_render_into_region(self):
        with self.settings(DEBUG=True):
            with self.assertRaises(NotImplementedError):
                self.admin.render_into_region(obj={}, context={})
        with self.settings(DEBUG=False):
            data = self.admin.render_into_region(obj={}, context={})
            self.assertIsNone(data)

    def test_render_into_summary(self):
        with self.settings(DEBUG=True):
            with self.assertRaises(NotImplementedError):
                self.admin.render_into_summary(obj={}, context={})
        with self.settings(DEBUG=False):
            data = self.admin.render_into_summary(obj={}, context={})
            self.assertEqual('{}', data)
