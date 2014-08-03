#!/usr/bin/env python
# encoding: utf-8
"""
tests.py

"""

from google.appengine.ext import ndb
from google.appengine.ext import testbed
from json import loads, dumps
from unittest import TestCase
from mail_safe_test import app
from mail_safe_test.auth import UserModel
from mail_safe_test.resources.doc import DocListAPI, DocAPI, DocModel

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

        self.user_id = '1'
        self.user_token = "valid_user"

        # Provision a valid user
        args = {"id": self.user_id,
                "first_name": "Testy",
                "last_name": "McTest",
                "email": "test@example.com" }
        user = UserModel(**args)
        user.put()
        self.auth = {'headers': {'Authorization': self.user_token}}

    def tearDown(self):
        self.testbed.deactivate()

#TODO create a success test case
    def test_doc_create(self):
        rv = self.app.post('/user/docs/',
            data=dumps({"content": "This is my revised testing document."}),
            headers={'Authorization': self.user_token}
            )
        self.assertEqual(200, rv.status_code)

    def test_doc_none_put(self):
        rv = self.app.put('/user/doc/25/',
            data=dumps({"content": "This is my revised testing document."}),
            headers={'Authorization': self.user_token})
        self.assertEqual(404, rv.status_code)

    def test_doc_id_none_get(self):
        rv = self.app.get('/user/doc/25/',
            headers={'Authorization': self.user_token})
        self.assertEqual(404, rv.status_code)

    def test_doc_id_none_delete(self):
        rv = self.app.delete('/user/doc/25/',
            headers={'Authorization': self.user_token})
        self.assertEqual(404, rv.status_code)
