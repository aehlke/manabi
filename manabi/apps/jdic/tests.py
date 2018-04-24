# -*- coding: utf-8 -*-

import json

from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth.models import User
import urllib.request, urllib.parse, urllib.error
from django.conf import settings


#class JdicAudioTest(TestCase):
#    def setUp(self):
#        dojango_settings.DOJO_SECURE_JSON = False

#        self.user = User.objects.create_user(
#            'alex', 'w@w.com', 'w')
#        self.user.save()

#        self.login = self.client.login(
#            username='alex', password='w')
#        self.failUnless(self.login, 'Could not log in')

#        self.filename = urllib.quote(u'きょう - 今日.mp3'.encode('utf8'))

#    def tearDown(self):
#        dojango_settings.DOJO_SECURE_JSON = True


#    def test_filename_encoding(self):
#        self.assertEqual(self.filename,
#            '%E3%81%8D%E3%82%87%E3%81%86%20-%20%E4%BB%8A%E6%97%A5.mp3')

#    def _try_filename(self, filename):
#        'Returns json response as dict'
#        post_data = {'filename': filename}

#        res = self.client.post(
#            reverse('jdic_audio_file_exists'), post_data)

#        self.assertEqual(res.status_code, 200)
#        json_ = json.loads(res.content)
#        return json_

#    def test_audio_exists(self):
#        filename = self.filename
#        json = self._try_filename(filename)

#        self.assertTrue(json['success'])
#        self.assertTrue('data' in json.keys())
#        self.assertTrue(json['data'])

#    def test_audio_exists2(self):
#        filename = u'%E3%81%9F%E3%81%B9%E3%82%8B - %E9%A3%9F%E3%81%B9%E3%82%8B.mp3'

#        json = self._try_filename(filename)

#        self.assertTrue(json['success'])
#        self.assertTrue('data' in json.keys())
#        self.assertTrue(json['data'])

#    def test_audio_doesnt_exist(self):
#        json = self._try_filename('blah.mp3')

#        self.assertTrue(json['success'])
#        self.assertFalse(json['data'])


