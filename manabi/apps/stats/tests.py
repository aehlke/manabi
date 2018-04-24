# -*- coding: utf-8 -*-
import urllib.request, urllib.parse, urllib.error
import json

from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from django.conf import settings
from manabi.test_helpers import ManabiTestCase, create_sample_data, create_user


#class StatsTest(ManabiTestCase):
#    def after_setUp(self):
#        self.user = create_user()
#        create_sample_data(facts=30, user=self.user)
#        self.review_cards(self.user)

#    def test_reps_view(self):
#        res = self.get(reverse('graphs_repetitions'), user=self.user)
#        self.assertStatus(200, res)

#        self.assertApiSuccess(res)
#        self.assertTrue('series' in res.json['data'])
#        from manabi.apps.flashcards.models import CardHistory
#        user_items = CardHistory.objects.of_user(self.user)
#        import sys
#        self.assertTrue(any([series['data'] for series in res.json['data']['series']]))

#    def test_due_counts_view(self):
#        res = self.get(reverse('graphs_due_counts'), user=self.user)
#        self.assertStatus(200, res)

#        self.assertApiSuccess(res)
#        json_ = json.loads(res.content)
#        self.assertTrue('series' in json_['data'])

