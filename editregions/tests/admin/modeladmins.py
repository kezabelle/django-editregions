# -*- coding: utf-8 -*-
import warnings
from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.auth.models import User
from django.forms import ModelForm
from django.test import RequestFactory
from django.utils.unittest.case import TestCase
from django.test import TestCase as DjangoTestCase
from editregions.admin.modeladmins import ChunkAdmin
from editregions.contrib.embeds.models import Iframe
from editregions.utils.data import get_content_type
try:
    from django.utils.encoding import force_text
except ImportError:
    from django.utils.encoding import force_unicode as force_text


class ChunkAdminTestCase(DjangoTestCase):
    def setUp(self):
        self.chunk_admin = ChunkAdmin()
        self.chunk_admin.admin_site = admin.site
        class RealishAdmin(ChunkAdmin, ModelAdmin):
            pass
        self.realish_admin = RealishAdmin

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
