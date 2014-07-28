#!/usr/bin/env python
# encoding: utf-8
"""
tests.py

"""

from google.appengine.ext import ndb
from google.appengine.ext import testbed
from json import loads
from unittest import TestCase
from mail_safe_test import app
from mail_safe_test.auth import UserModel
from mail_safe_test.resources.doc import DocList, Doc, DocModel

def common_setUp(self):
    # Flask apps testing. See: http://flask.pocoo.org/docs/testing/
    app.config['TESTING'] = True
    app.config['CSRF_ENABLED'] = False
    self.app = app.test_client()
    # Setup app engine test bed. See: http://code.google.com/appengine/docs/python/tools/localunittesting.html#Introducing_the_Python_Testing_Utilities
    self.testbed = testbed.Testbed()
    self.testbed.activate()
    self.testbed.init_datastore_v3_stub()
    self.testbed.init_user_stub()
    self.testbed.init_memcache_stub()

class AuthUserDocTestCases(TestCase):

    def setUp(self):
        common_setUp(self)

        AuthUserDocTestCases.user_id = '111111111111111111111'
        AuthUserDocTestCases.user_token = "valid_user"

        # Provision a valid user
        args = {"id": AuthUserDocTestCases.user_id,
                "first_name": "Testy",
                "last_name": "McTest",
                "email": "test@example.com" }
        user = UserModel(**args)
        user.put()

    def tearDown(self):
        self.testbed.deactivate()

    def test_doc_none_put(self):
        rv = self.app.put('/doc/25/',
            data='{"content": "This is my revised testing document."}')
        self.assertEqual(404, rv.status_code)

    def test_doc_id_none_get(self):
        rv = self.app.get('/doc/25/')
        self.assertEqual(404, rv.status_code)

    def test_doc_id_none_delete(self):
        rv = self.app.delete('/doc/25/')
        self.assertEqual(404, rv.status_code)
