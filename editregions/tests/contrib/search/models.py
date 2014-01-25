# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.test.utils import override_settings
from django.utils.encoding import force_text
from editregions.contrib.search.models import (configured_haystack_connection,
                                               csv_validator, MoreLikeThis,
                                               SearchResults)
from editregions.utils.data import get_content_type


class HaystackConnectionsTestCase(TestCase):

    @override_settings(HAYSTACK_CONNECTIONS={})
    def test_no_configured_connections(self):
        with self.assertRaises(ValidationError):
            configured_haystack_connection('ghost')

    @override_settings(HAYSTACK_CONNECTIONS={'grerple': True})
    def test_configured_connection_exists(self):
        configured_haystack_connection('grerple')

    @override_settings(HAYSTACK_CONNECTIONS={'grerple': True})
    def test_chosen_connection_not_configured(self):
        with self.assertRaises(ValidationError):
            configured_haystack_connection('not_grerple')


class CsvValidatorTestCase(TestCase):
    def test_no_value(self):
        csv_validator('')

    def test_value_has_spaces_no_comma(self):
        with self.assertRaises(ValidationError):
            csv_validator('a b')

    def test_value_has_spaces_ends_with_comma(self):
        csv_validator('a b, cd,')


class MoreLikeThisTestCase(TestCase):
    def test_str(self):
        sample_user, created = User.objects.get_or_create(username='test')
        user_ct = get_content_type(sample_user)
        mlt = MoreLikeThis(position=1, content_type=user_ct,
                           content_id=sample_user.pk, region='test',
                           connection='default')
        mlt.full_clean()
        self.assertEqual('3 from "default"', force_text(mlt))


class SearchResultsTestCase(TestCase):
    def test_str(self):
        sample_user, created = User.objects.get_or_create(username='test')
        user_ct = get_content_type(sample_user)
        sr = SearchResults(position=1, content_type=user_ct,
                           content_id=sample_user.pk, region='test',
                           connection='default', max_num=3, query="goose fat")
        sr.full_clean()
        self.assertEqual('Up to 3 best matches for "goose fat"', force_text(sr))

    @override_settings(HAYSTACK_CONNECTIONS={'a': 1, 'b': 2})
    def test_str_alt_branch(self):
        sample_user, created = User.objects.get_or_create(username='test')
        user_ct = get_content_type(sample_user)
        sr = SearchResults(position=1, content_type=user_ct,
                           content_id=sample_user.pk, region='test',
                           connection='a', max_num=0, query="goose fat")
        sr.full_clean()
        self.assertEqual('', force_text(sr))

    def test_get_boosts(self):
        sample_user, created = User.objects.get_or_create(username='test')
        user_ct = get_content_type(sample_user)
        sr = SearchResults(position=1, content_type=user_ct,
                           content_id=sample_user.pk, region='test',
                           connection='default', query="goose fat",
                           boost='a,b,c')
        sr.full_clean()
        self.assertEqual(sr.get_boosts(), frozenset([
            ('b', 1.5),
            ('c', 1.5),
            ('a', 1.5)
        ]))

    def test_get_boosts_none(self):
        sample_user, created = User.objects.get_or_create(username='test')
        user_ct = get_content_type(sample_user)
        sr = SearchResults(position=1, content_type=user_ct,
                           content_id=sample_user.pk, region='test',
                           connection='default', query="goose fat",
                           boost=None)
        sr.full_clean()
        self.assertEqual(sr.get_boosts(), ())

    def test_get_boosts_blank(self):
        sample_user, created = User.objects.get_or_create(username='test')
        user_ct = get_content_type(sample_user)
        sr = SearchResults(position=1, content_type=user_ct,
                           content_id=sample_user.pk, region='test',
                           connection='default', query="goose fat",
                           boost='')
        sr.full_clean()
        self.assertEqual(sr.get_boosts(), ())

    def test_get_boosts_just_a_damn_comma(self):
        sample_user, created = User.objects.get_or_create(username='test')
        user_ct = get_content_type(sample_user)
        sr = SearchResults(position=1, content_type=user_ct,
                           content_id=sample_user.pk, region='test',
                           connection='default', query="goose fat",
                           boost=',')
        sr.full_clean()
        self.assertEqual(sr.get_boosts(), frozenset([]))

    def test_clean_healing(self):
        sample_user, created = User.objects.get_or_create(username='test')
        user_ct = get_content_type(sample_user)
        sr = SearchResults(position=1, content_type=user_ct,
                           content_id=sample_user.pk, region='test',
                           connection='default', query="     goose fat     ",
                           boost='aaaaaa')
        sr.full_clean()
        self.assertEqual(sr.boost, 'aaaaaa,')
        self.assertEqual(sr.query, 'goose fat')
