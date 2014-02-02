# -*- coding: utf-8 -*-
from collections import namedtuple
from django.contrib import admin
from django.contrib.admin.sites import NotRegistered
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
from django.template import Template, RequestContext, Context
from django.test import TestCase as DjangoTestCase, RequestFactory
from django.test.utils import override_settings
from editregions.contrib.embeds.models import Iframe
from editregions.models import EditRegionChunk
from editregions.templatetags.editregion import EditRegionTag
from editregions.utils.data import get_content_type
from editregions.utils.versioning import is_django_15plus


class TestUserAdmin(UserAdmin):
    def get_editregions_templates(self, obj):
        return ['fillable_editregion_template.html']


class EditRegionTemplateTagTestCase(DjangoTestCase):
    def setUp(self):
        self.ct = get_content_type(User)

    def test_render_one_chunk(self):
        iframe = Iframe(region='test', content_id=1, content_type=self.ct,
                        url='https://news.bbc.co.uk/', position=1)
        iframe.full_clean()
        iframe.pk = 1

        request = RequestFactory().get('/')
        ctx = RequestContext(request)
        ctx.update(EditRegionTag.chunk_iteration_context(
            index=0, value=iframe, iterable=[iframe]))
        output = EditRegionTag.render_one_chunk(context=ctx, chunk=iframe,
                                                renderer=None).strip()
        self.assertIn('<iframe ', output)
        self.assertIn('src="https://news.bbc.co.uk/"', output)
        self.assertIn('data-position="1"', output)
        self.assertIn('data-pk="1"', output)
        self.assertIn('data-region="test"', output)
        self.assertIn('</iframe>', output)

    def test_render_one_summary(self):
        iframe = Iframe(region='test', content_id=1, content_type=self.ct,
                        url='https://news.bbc.co.uk/', position=1)
        iframe.full_clean()

        request = RequestFactory().get('/')
        ctx = RequestContext(request)
        ctx.update(EditRegionTag.chunk_iteration_context(
            index=0, value=iframe, iterable=[iframe]))
        output = EditRegionTag.render_one_summary(context=ctx, chunk=iframe,
                                                  renderer=None).strip()
        self.assertEqual(output, 'https://news.bbc.co.uk/')

    def test_render_all_chunks(self):
        objs = []
        for x in range(0, 10):
            iframe = Iframe(region='test', content_id=1, content_type=self.ct,
                            url='https://news.bbc.co.uk/{0!s}'.format(x),
                            position=x)
            iframe.full_clean()
            iframe.pk = x
            objs.append(iframe)
        ctx = Context()
        chunks = EditRegionTag.render_all_chunks(context=ctx, found_chunks=objs)
        converted_chunks = list(chunks)
        self.assertEqual(10, len(converted_chunks))

        for num, obj in enumerate(converted_chunks):
            testable = obj.strip()
            pos = num + 1
            self.assertIn('src="https://news.bbc.co.uk/{0}"'.format(num),
                          testable)
            self.assertIn('data-position="{0}"'.format(pos), testable)
            self.assertIn('data-region="test"', testable)

    def test_render_all_chunks_yielding_nones(self):
        context = Context()
        chunks = [Iframe(pk=1, region='x'),
                  Iframe(pk=2, region='x'),
                  Iframe(pk=3, region='x'),
                  EditRegionChunk(pk=4, region='x'),
                  Iframe(pk=5, region='x')]
        chunks2 = list(EditRegionTag.render_all_chunks(context=context,
                                                       found_chunks=chunks))
        self.assertEqual(len(chunks2), len(chunks) - 1)

    def test_chunk_iteration_context(self):
        """
        Sample context:
        {'chunkloop': {'counter': 1,
               'counter0': 0,
               'first': True,
               'last': False,
               'next': 1,
               'next0': 0,
               'next_plugin': FakedChunk(region='test', position=2),
               'object': FakedChunk(region='test', position=1),
               'previous': None,
               'previous0': None,
               'previous_plugin': None,
               'region': 'test',
               'remaining_plugins': [FakedChunk(region='test', position=1),
                                     FakedChunk(region='test', position=2),
                                     FakedChunk(region='test', position=3),
                                     FakedChunk(region='test', position=4),
                                     FakedChunk(region='test', position=5),
                                     FakedChunk(region='test', position=6),
                                     FakedChunk(region='test', position=7),
                                     FakedChunk(region='test', position=8),
                                     FakedChunk(region='test', position=9)],
               'revcounter': 10,
               'revcounter0': 9,
               'total': 10,
               'used_plugins': []}}
        """
        FakeChunk = namedtuple('FakedChunk', ['region', 'position'])

        iterable = [FakeChunk(region='test', position=x) for x in range(0, 10)]
        first = iterable[0]
        last = iterable[-1]
        for offset, obj in enumerate(iterable):
            ctx = EditRegionTag.chunk_iteration_context(index=offset, value=obj,
                                                        iterable=iterable)
            self.assertEqual(ctx['chunkloop']['counter'], offset+1)
            self.assertEqual(ctx['chunkloop']['counter0'], offset)

            if obj == last:
                self.assertEqual(ctx['chunkloop']['next'], None)
                self.assertEqual(ctx['chunkloop']['next0'], None)
            else:
                self.assertEqual(ctx['chunkloop']['next'], offset+1)
                self.assertEqual(ctx['chunkloop']['next0'], offset)

            if obj == first:
                self.assertEqual(ctx['chunkloop']['previous'], None)
                self.assertEqual(ctx['chunkloop']['previous0'], None)
            else:
                self.assertEqual(ctx['chunkloop']['previous'], offset)
                self.assertEqual(ctx['chunkloop']['previous0'], offset - 1)

            self.assertEqual(ctx['chunkloop']['region'], 'test')
            self.assertEqual(ctx['chunkloop']['revcounter'],
                             len(iterable) - offset)
            self.assertEqual(ctx['chunkloop']['revcounter0'],
                             len(iterable) - (offset+1))
            self.assertEqual(ctx['chunkloop']['total'], len(iterable))

            # check the keys which track the loop history and future
            self.assertEqual(len(ctx['chunkloop']['used']), offset)
            self.assertEqual(ctx['chunkloop']['used'], iterable[0:offset])
            self.assertEqual(len(ctx['chunkloop']['remaining']),
                             len(iterable) - (offset+1))
            self.assertEqual(ctx['chunkloop']['remaining'], iterable[offset+1:])

    def test_usage(self):
        tmpl = Template("""
        output:
        {% load editregion %}
        {% editregion "test" obj %}
        {% editregion "test" obj as exposed %}
        {% for chunk in exposed %}
        {% endfor %}
        """)
        user = User(username='test', is_staff=True, is_active=True,
                    is_superuser=True)
        user.set_password('test')
        user.full_clean()
        user.save()
        user_content_type = get_content_type(User)

        # attach some chunks to the region in test
        for x in range(0, 10):
            iframe = Iframe(region='test', content_id=user.pk,
                            content_type=user_content_type,
                            url='https://news.bbc.co.uk/{0!s}'.format(x),
                            position=x)
            iframe.full_clean()
            iframe.save()

        # fix the admin in test
        try:
            admin.site.unregister(User)
        except NotRegistered:
            pass
        admin.site.register(User, TestUserAdmin)

        request = RequestFactory().get('/')
        request.user = user
        ctx = RequestContext(request)
        ctx.update({'obj': user})
        rendered = tmpl.render(ctx).strip()
        self.assertEqual(2206, len(rendered))

        tmpl = Template("""
        output:
        {% load editregion %}
        {% editregion "test" obj as exposed %}
        {% for chunk in exposed %}xxx:{{ chunk }}{% endfor %}
        """)
        rendered = tmpl.render(ctx).strip()
        self.assertIn('output:', rendered)
        for x in range(0, 10):
            self.assertIn('xxx:<iframe '.format(x), rendered)
            self.assertIn('src="https://news.bbc.co.uk/{0}"'.format(x),
                          rendered)
            self.assertIn('name="chunk-iframe-{0}"'.format(x+1), rendered)

    @override_settings(DEBUG=True)
    def test_blank_content_object_debug(self):
        """ in debug, error loudly to the user """
        tmpl = Template("""
        output:
        {% load editregion %}
        {% editregion "test" obj %}
        """)
        with self.assertRaisesRegexp(ValueError, "content_object was probably "
                                                 "'', check the context "
                                                 "provided"):
            tmpl.render(Context()).strip()

    @override_settings(DEBUG=False)
    def test_blank_content_object_production(self):
        """ in production, error silently to a logger """
        tmpl = Template("""
        output:
        {% load editregion %}
        {% editregion "test" obj %}
        """)
        self.assertEqual('output:', tmpl.render(Context()).strip())

    @override_settings(DEBUG=True)
    def test_none_content_object_debug(self):
        """ in debug, error loudly to the user """
        tmpl = Template("""
        output:
        {% load editregion %}
        {% editregion "test" None %}
        """)
        if is_django_15plus():
            with self.assertRaisesRegexp(ImproperlyConfigured,
                                         'no object provided to the "editregion" '
                                         'template tag forregion "test"'):
                tmpl.render(Context()).strip()
        else:
            with self.assertRaisesRegexp(ValueError,
                                         "content_object was probably '', "
                                         "check the context provided"):
                tmpl.render(Context()).strip()

    @override_settings(DEBUG=False)
    def test_none_content_object_production(self):
        """ in production, error silently to a logger """
        tmpl = Template("""
        output:
        {% load editregion %}
        {% editregion "test" None %}
        """)
        self.assertEqual('output:', tmpl.render(Context()).strip())

    def test_inheritance_without_get_ancestors(self):
        user = User(username='test', is_staff=True, is_active=True,
                    is_superuser=True)
        user.set_password('test')
        user.full_clean()
        user.save()

        try:
            admin.site.unregister(User)
        except NotRegistered:
            pass
        admin.site.register(User, TestUserAdmin)

        request = RequestFactory().get('/')
        request.user = user
        ctx = RequestContext(request)
        ctx.update({'obj': user})
        tmpl = Template("""
        output:
        {% load editregion %}
        {% editregion "test" obj inherit %}
        """)
        with self.settings(DEBUG=True):
            with self.assertRaises(ImproperlyConfigured):
                tmpl.render(ctx).strip()
        with self.settings(DEBUG=False):
            rendered = tmpl.render(ctx).strip()
            self.assertEqual('output:', rendered)

    def test_inheritance_with_get_ancestors(self):
        user = User(username='test', is_staff=True, is_active=True,
                    is_superuser=True)
        user.set_password('test')
        user.full_clean()
        user.save()
        parent_user = User(username='test2', is_staff=True, is_active=True,
                           is_superuser=True)
        parent_user.set_password('test')
        parent_user.full_clean()
        parent_user.save()

        for x in range(0, 10):
            iframe = Iframe(region='test', content_id=parent_user.pk,
                            content_type=get_content_type(User),
                            url='https://news.bbc.co.uk/{0!s}'.format(x),
                            position=x)
            iframe.full_clean()
            iframe.save()

        user.get_ancestors = lambda: [parent_user]

        try:
            admin.site.unregister(User)
        except NotRegistered:
            pass
        admin.site.register(User, TestUserAdmin)

        request = RequestFactory().get('/')
        request.user = user
        ctx = RequestContext(request)
        ctx.update({'obj': user})
        tmpl = Template("""
        output:
        {% load editregion %}
        {% editregion "test" obj inherit %}
        """)
        rendered = tmpl.render(ctx).strip()
        self.assertEqual(2206, len(rendered))
