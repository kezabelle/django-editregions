# -*- coding: utf-8 -*-
import json
import warnings
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
from django.utils.unittest.case import TestCase
from django.test import TestCase as DjangoTestCase
from editregions.admin.changelist import EditRegionChangeList
from editregions.admin.modeladmins import ChunkAdmin, EditRegionAdmin
from editregions.admin.utils import AdminChunkWrapper
from editregions.constants import REQUEST_VAR_CT, REQUEST_VAR_ID, REQUEST_VAR_REGION
from editregions.contrib.embeds.models import Iframe
from editregions.models import EditRegionChunk
from editregions.utils.data import get_content_type, get_modeladmin

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
        self.realish_admin = RealishAdmin
        try:
            admin.site.unregister(User)
        except NotRegistered:
            pass
        admin.site.register(User, TestUserAdmin)

    def test_get_model_perms(self):
        request = RequestFactory().get('/')
        results = self.chunk_admin.get_model_perms(request=request)
        self.assertEqual({}, results)

    def test_response_max(self):
        request = RequestFactory().get('/')
        results = self.chunk_admin.response_max(request=request, limit=1,
                                                found=1).content
        self.assertInHTML('<h2>Limit reached</h2>', results)
        # this doesn't work. No idea why. Stupid Django.
        # self.assertInHTML('Unable to add more than <b>1</b> to this region.',
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
        # self.assertInHTML('Please wait, saving changes', html)
        # self.assertInHTML('Add new content', html)
        # self.assertInHTML('Iframe', html)
        self.assertInHTML('<h3>Embeds</h3>', html)
        self.assertInHTML('<b>whee!:</b>', html)

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
        self.assertInHTML('<h3>Embeds</h3>', html)
        self.assertInHTML('<b>whee!:</b>', html)

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
        self.assertInHTML('<h3>Embeds</h3>', html)
        self.assertInHTML('<b>whee!:</b>', html)

    def test_render_into_region(self):
        with warnings.catch_warnings(record=True) as w:
            self.chunk_admin.render_into_region(obj={}, context={})
            self.assertEqual(len(w), 1)
            self.assertEqual(len(w), 1)
            warning = w[0]
            self.assertIsInstance(warning.message, RuntimeWarning)
            self.assertEqual(force_text(warning.message),
                             "`render_into_region` not implemented on "
                             "<class 'editregions.admin.modeladmins."
                             "ChunkAdmin'>")

    def test_render_into_region(self):
        with warnings.catch_warnings(record=True) as w:
            self.chunk_admin.render_into_summary(obj={}, context={})
            self.assertEqual(len(w), 1)
            self.assertEqual(len(w), 1)
            warning = w[0]
            self.assertIsInstance(warning.message, RuntimeWarning)
            self.assertEqual(force_text(warning.message),
                             "`render_into_summary` not implemented on "
                             "<class 'editregions.admin.modeladmins."
                             "ChunkAdmin'>")

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
        admin_instance = self.realish_admin(model=Iframe, admin_site=admin.site)

        with self.assertNumQueries(2):
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
        admin_instance = self.realish_admin(model=Iframe, admin_site=admin.site)

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
        admin_instance = self.realish_admin(model=Iframe, admin_site=admin.site)

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
        self.realish_admin = RealishAdmin
        try:
            admin.site.unregister(User)
        except NotRegistered:
            pass
        admin.site.register(User, TestUserAdmin)

    def test_leave_unchanged(self):
        request = RequestFactory().get('/')
        response_200 = HttpResponse(content='ok')
        admin_instance = self.realish_admin(model=Iframe, admin_site=admin.site)
        new_response = admin_instance.maybe_fix_redirection(
            request=request, response=response_200)
        # returned unchanged
        self.assertEqual('ok', new_response.content)
        self.assertEqual(200, new_response.status_code)

    def test_returned_data_changed(self):
        request = RequestFactory().get('/')
        admin_instance = self.realish_admin(model=Iframe, admin_site=admin.site)
        response_302 = HttpResponseRedirect(redirect_to='/admin_mountpoint/')
        new_response = admin_instance.maybe_fix_redirection(
            request=request, response=response_302)
        # returned early because it was a redirect, but we updated the
        # querystring anyway
        self.assertEqual(302, new_response.status_code)
        self.assertEqual('/admin_mountpoint/?_data_changed=1',
                         new_response['Location'])

    def test_to_other_url(self):
        user = User(username='test', is_staff=True, is_superuser=True,
                    is_active=True)
        user.set_password('test')
        user.full_clean()
        user.save()
        request = RequestFactory().get('/')
        response_302 = HttpResponseRedirect(redirect_to='/admin_mountpoint/')
        admin_instance = self.realish_admin(model=Iframe, admin_site=admin.site)
        new_response = admin_instance.maybe_fix_redirection(
            request=request, response=response_302, obj=user)
        # was a redirect, but not to a chunkadmin instance.
        self.assertEqual(302, new_response.status_code)
        self.assertEqual('/admin_mountpoint/?_data_changed=1',
                         new_response['Location'])

    def test_to_chunkadmin_instance(self):
        user = User(username='test', is_staff=True, is_superuser=True,
                    is_active=True)
        user.set_password('test')
        user.full_clean()
        user.save()
        admin_instance = self.realish_admin(model=Iframe, admin_site=admin.site)
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
        # was a redirect, to a chunkadmin instance
        self.assertEqual(301, new_response.status_code)
        self.assertEqual('/admin_mountpoint/auth/user/2/?_data_changed=1',
                         new_response['Location'])

    def test_autoclose_chunkadmin(self):
        user = User(username='test', is_staff=True, is_superuser=True,
                    is_active=True)
        user.set_password('test')
        user.full_clean()
        user.save()
        admin_instance = self.realish_admin(model=Iframe, admin_site=admin.site)
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
        # was a redirect, to a chunkadmin instance
        self.assertEqual(301, new_response.status_code)
        self.assertEqual('/admin_mountpoint/embeds/iframe/add/?region=test'
                         '&_data_changed=1&_autoclose=1&content_type=4'
                         '&content_id=2',
                         new_response['Location'])

    def test_continue_editing_parent_object(self):
        user = User(username='test', is_staff=True, is_superuser=True,
                    is_active=True)
        user.set_password('test')
        user.full_clean()
        user.save()
        admin_instance = self.realish_admin(model=Iframe, admin_site=admin.site)
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
        # was a redirect, to a chunkadmin instance
        self.assertEqual(301, new_response.status_code)
        self.assertEqual('/admin_mountpoint/auth/user/2/?_data_changed=1',
                         new_response['Location'])


class EditRegionAdminTestCase(DjangoTestCase):
    def setUp(self):
        self.admin = get_modeladmin(EditRegionChunk)

    def test_cover_init(self):
        our_admin = EditRegionAdmin(EditRegionChunk, admin.site)
        self.assertEqual(our_admin.list_display_links, (None,))

    def test_get_list_display_links(self):
        request = RequestFactory().get('/')
        expected = (None,)
        received = self.admin.get_list_display_links(request=request,
                                                     list_display=())
        self.assertEqual(expected, received)

    def test_get_list_display_links(self):
        request = RequestFactory().get('/')
        expected = [u'get_position', u'get_subclass_type',
                    u'get_subclass_summary', u'get_last_modified',
                    u'get_object_tools']
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
        self.assertEqual(expected, received)

    def test_get_changelist_link_html_directly(self):
        kwargs = {
            'func': 'get_changelist_link_html',
            'expected': ('<a href="/admin_mountpoint/embeds/iframe/1/?region='
                         'test&content_id=1&content_type=4" data-adminlinks='
                         '"autoclose" data-no-turbolink>x</a>'),
            'extra': {
                'data': 'x',
            }
        }
        self._test_changelist_display_methods(**kwargs)

    def test_get_region_name(self):
        kwargs = {
            'func': 'get_region_name',
            'expected': ('<a href="/admin_mountpoint/embeds/iframe/1/?region='
                         'test&content_id=1&content_type=4" data-adminlinks='
                         '"autoclose" data-no-turbolink>whee!</a>'),
            'extra': {}
        }
        self._test_changelist_display_methods(**kwargs)

    def test_get_subclass_type(self):
        kwargs = {
            'func': 'get_subclass_type',
            'expected': ('<a href="/admin_mountpoint/embeds/iframe/1/?region='
                         'test&content_id=1&content_type=4" data-adminlinks='
                         '"autoclose" data-no-turbolink>iframe</a>'),
            'extra': {}
        }
        self._test_changelist_display_methods(**kwargs)

    def test_get_subclass_summary(self):
        kwargs = {
            'func': 'get_subclass_summary',
            'expected': ('<a href="/admin_mountpoint/embeds/iframe/1/?region='
                         'test&content_id=1&content_type=4" data-adminlinks='
                         '"autoclose" data-no-turbolink>https://news.bbc.co'
                         '.uk/</a>'),
            'extra': {}
        }
        self._test_changelist_display_methods(**kwargs)

    def test_get_position(self):
        kwargs = {
            'func': 'get_position',
            'expected': ('<a href="/admin_mountpoint/embeds/iframe/1/?region='
                         'test&content_id=1&content_type=4" data-adminlinks='
                         '"autoclose" data-no-turbolink>2</a>'),
            'extra': {}
        }
        self._test_changelist_display_methods(**kwargs)

    def test_get_last_modified(self):
        pass

    def test_get_object_tools(self):
        kwargs = {
            'func': 'get_object_tools',
            'expected': ('<div class="drag_handle" data-pk="1" data-href="'
                         '/admin_mountpoint/editregions/editregionchunk/move/'
                         '"></div>&nbsp;<a class="delete_handle" href="'
                         '/admin_mountpoint/embeds/iframe/1/delete/?region='
                         'test&content_id=1&content_type=4" data-adminlinks='
                         '"autoclose" data-no-turbolink>Delete</a>'),
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
        self.assertEqual(json.loads(response.content), {
            u'pk': u'content block does not exist',
            u'position': [u'This field is required.']
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
                                             'pk': first_obj.pk})
        request.user = user
        response = self.admin.move_view(request=request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-type'], 'application/json')
        json_data = json.loads(response.content)
        self.assertIn('action', json_data)
        self.assertIn('html', json_data)
        self.assertEqual('move', json_data['action'])
        self.assertIn('<div class="region-inline-wrapper">',
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

    def test_get_admin_wrapper_class(self):
        self.assertEqual(self.admin.get_admin_wrapper_class(),
                         AdminChunkWrapper)

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
        self.assertIn('<div class="region-inline-wrapper">', received)
        self.assertIn('<h3>Embeds</h3>', received)
        self.assertIn('class="column-get_subclass_summary"', received)
        self.assertIn('<div class="region-inline-progress-wrapper">', received)

    def test_media_property(self):
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
            u'admin/js/jquery.rebind.js',
            u'adminlinks/js/jquery.fancyiframe.js',
            u'editregions/js/jquery.ui.1-10-3.custom.js',
            u'editregions/js/dragging.js'])
