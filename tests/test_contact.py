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
from mail_safe_test.resources.contact import ContactList, Contact, ContactModel

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

def verify_contact_count(self, contact_count):
    contacts = ContactModel.query().fetch()
    self.assertEqual(contact_count, len(contacts))

class AuthUserContactTestCases(TestCase):

    def setUp(self):
        common_setUp(self)

        # Provision a valid user
        AuthUserContactTestCases.user_id = '111111111111111111111'
        AuthUserContactTestCases.user_token = "valid_user"

        args = {"id": AuthUserContactTestCases.user_id,
                "first_name": "Testy",
                "last_name": "McTest",
                "email": "user@example.com" }
        user = UserModel(**args)
        user.put()

    def tearDown(self):
    	self.testbed.deactivate()

    # def test_contact_none_put(self):
    #     rv = self.app.put('/contact/25/',
    #         data='{"email": "changed@example.com"}',
    #         content_type='application/json')
    #     self.assertEqual(404, rv.status_code) 

    # def test_contact_id_none_get(self):
    #     rv = self.app.get('/contact/25/',
    #         headers={'Authorization':AuthUserContactTestCases.user_token})
    #     self.assertEqual(404, rv.status_code)

    # def test_contact_id_none_delete(self):
    #     rv = self.app.delete('/contact/25/')
    #     self.assertEqual(404, rv.status_code)

    def test_contact_post(self):
        verify_contact_count(self, 0)
        rv = self.app.post('/contact/',
                data='{"first_name": "Best", "last_name": "Friend", "email": "bestfriend@test.com", "phone": "1234567891"}',
                content_type='application/json',
                headers = {'Authorization': AuthUserContactTestCases.user_token})
        self.assertEqual(200, rv.status_code)
        verify_contact_count(self, 1)
        
    # def test_contact_post_duplicate(self):
    #     # verify_contact_count(self, 1)
    #     rv = self.app.post('/contact/',
    #             data='{"first_name": "Best", "last_name": "Friend", "email": "bestfriend@test.com", "phone": "1234567891"}',
    #             content_type='application/json',
    #             headers = {'Authorization': AuthUserContactTestCases.user_token})
    #     self.assertEqual(404, rv.status_code)
    #     # verify_contact_count(self, 1)

    # def test_contact_post_missing_email(self):
    #     rv = self.app.post('/contact/',
    #             data='{"first_name": "Best", "last_name": "Friend", "phone": "1234567891"}',
    #             content_type='application/json',
    #             headers = {'Authorization': AuthUserContactTestCases.user_token})
    #     self.assertEqual(404, rv.status_code)
    #     # verify_contact_count(self, 1)


    # # maybe add tests to verify the validity of email and phone? Not in the API currently though

    # # need tests for put but need to solve post problem first

    # def test_contact_list_get(self):
    #     rv = self.app.get('/contacts/',
    #         headers = {'Authorization': AuthUserContactTestCases.user_token})
    #     self.assertEqual(200, rv.status_code)
    #     data = loads(rv.data)
    #     self.assertEqual('Best', data['contacts'][0]['first_name'])
    #     self.assertEqual('Friend', data['contacts'][0]['last_name'])
    #     self.assertEqual('bestfriend@test.com', data['contacts'][0]['email'])
    #     self.assertEqual('1234567891', data['contacts'][0]['phone'])


        

