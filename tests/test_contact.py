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
from mail_safe_test.resources.contact import ContactListAPI, ContactAPI, ContactModel

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

def verify_user_contact_count(self, user_id, contact_count):
    contacts = ContactModel.query(ancestor=ndb.Key(UserModel, user_id)).fetch()
    self.assertEqual(contact_count, len(contacts))

class NonAuthContactTestCases(TestCase):

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

        # Provision a contact for that user
        contact_fields = {
            'id': '12345',
            'first_name': "First",
            'last_name': "Contact",
            'email': "contact@example.com",
            'phone': "1234567890"
        }
        contact = ContactModel(parent=ndb.Key(UserModel, user.key.id()), **contact_fields)
        contact.put()

    def tearDown(self):
        self.testbed.deactivate()

    def test_contact_get_no_auth(self):
        rv = self.app.get('/user/contact/')
        self.assertEqual(404, rv.status_code)

    def test_contact_get_invalid_auth(self):
        rv = self.app.get('/user/contact/',
                headers = {'Authorization': 'invalid'})
        self.assertEqual(404, rv.status_code)
        
    def test_bad_contact_id_get_no_auth(self):
        rv = self.app.get('/user/contact/12/')
        self.assertEqual(404, rv.status_code)

    def test_bad_contact_id_get_invalid_auth(self):
        rv = self.app.get('/user/contact/12/',
                headers = {'Authorization': 'invalid'})
        self.assertEqual(404, rv.status_code)

    def test_contact_id_get_no_auth(self):
        rv = self.app.get('/user/contact/12345/')
        self.assertEqual(404, rv.status_code)

    def test_contact_id_get_invalid_auth(self):
        rv = self.app.get('/user/contact/12345/',
                headers = {'Authorization': 'invalid'})
        self.assertEqual(404, rv.status_code)
    
    def test_contact_post_no_auth(self):
        rv = self.app.post('/user/contact/12/',
                data='{"first_name": "Best", "last_name": "Friend", "email": "bestfriend@test.com", "phone": "1234567890"}',
                content_type='application/json')
        self.assertEqual(404, rv.status_code)
        verify_contact_count(self, 1)

    def test_contact_post_invalid_auth(self):
        rv = self.app.post('/user/contact/12/',
                data='{"first_name": "Best", "last_name": "Friend", "email": "bestfriend@test.com", "phone": "1234567890"}',
                headers = {'Authorization': 'invalid'})
        self.assertEqual(404, rv.status_code)
        verify_contact_count(self, 1)
        
    def test_contact_put_no_auth(self):
        rv = self.app.put('/user/contact/12345/',
                data='{"first_name": "Changed"}',
                content_type='application/json')
        self.assertEqual(404, rv.status_code)
        
    def test_contact_put_invalid_auth(self):
        rv = self.app.put('/user/contact/12345/',
                data='{"first_name": "Changed"}',
                content_type='application/json',
                headers = {'Authorization': 'invalid'})
        self.assertEqual(404, rv.status_code)
        
    def test_contact_delete_no_auth(self):
        rv = self.app.delete('/user/contact/12345/')
        self.assertEqual(404, rv.status_code)

    def test_contact_delete_invalid_auth(self):
        rv = self.app.delete('/user/contact/12345/',
                headers = {'Authorization': 'invalid'})
        self.assertEqual(404, rv.status_code)
        
    def test_contacts_get_no_auth(self):
        rv = self.app.get('/user/contacts/')
        self.assertEqual(404, rv.status_code)

    def test_contacts_get_invalid_auth(self):
        rv = self.app.get('/user/contacts/',
                headers = {'Authorization': 'invalid'})
        self.assertEqual(404, rv.status_code)
        
    def test_contacts_delete_no_auth(self):
        rv = self.app.delete('/user/contacts/')
        self.assertEqual(404, rv.status_code)

    def test_contacts_delete_invalid_auth(self):
        rv = self.app.delete('/user/contacts/',
            headers = {'Authorization': 'invalid'})
        self.assertEqual(404, rv.status_code)

class AuthUserContactTestCases(TestCase):

    def setUp(self):
        common_setUp(self)

        # Provision two valid users
        AuthUserContactTestCases.user1_id = '111111111111111111111'
        AuthUserContactTestCases.user1_token = "valid_user"

        AuthUserContactTestCases.user2_id = '111111111111111111112'
        AuthUserContactTestCases.user2_token = "valid_user2"

        args = {"id": AuthUserContactTestCases.user1_id,
                "first_name": "Testy",
                "last_name": "McTest",
                "email": "user@example.com" }
        user = UserModel(**args)
        user.put()
        
        args = {"id": AuthUserContactTestCases.user2_id,
                "first_name": "Testy",
                "last_name": "McTest",
                "email": "user@example.com" }
        user = UserModel(**args)
        user.put()

        # Provision a contact for both users
        contact_fields = {
            'id': '12345',
            'first_name': "First1",
            'last_name': "Contact1",
            'email': "contact1@example.com",
            'phone': "1234567890"
        }
        contact = ContactModel(parent=ndb.Key(UserModel, AuthUserContactTestCases.user1_id), **contact_fields)
        contact.put()

        contact_fields = {
            'id': '12345',
            'first_name': "First2",
            'last_name': "Contact2",
            'email': "contact2@example.com",
            'phone': "1234567890"
        }
        contact = ContactModel(parent=ndb.Key(UserModel, AuthUserContactTestCases.user2_id), **contact_fields)
        contact.put()

    def tearDown(self):
    	self.testbed.deactivate()

    def test_contact_id_none_get(self):
        rv = self.app.get('/contact/25/',
            headers={'Authorization': AuthUserContactTestCases.user1_token})
        self.assertEqual(404, rv.status_code)

    def test_contact_id_get(self):
        rv = self.app.get('/contact/12345/',
            headers={'Authorization': AuthUserContactTestCases.user1_token})
        self.assertEqual(200, rv.status_code)

    def test_contact_id_none_delete(self):
        rv = self.app.delete('/contact/25/',
            headers={'Authorization': AuthUserContactTestCases.user1_token})
        self.assertEqual(404, rv.status_code)
    
    def test_contact_post(self):
        verify_contact_count(self, 2)
        verify_user_contact_count(self, AuthUserContactTestCases.user1_id, 1)
        rv = self.app.post('/contact/00101010/',
                data='{"first_name": "Best", "last_name": "Friend", "email": "bestfriend@test.com", "phone": "1234567890"}',
                content_type='application/json',
                headers = {'Authorization': AuthUserContactTestCases.user1_token})
        self.assertEqual(200, rv.status_code)
        verify_contact_count(self, 3)
        verify_user_contact_count(self, AuthUserContactTestCases.user1_id, 2)
    
    def test_contact_post_duplicate(self):
        verify_contact_count(self, 2)
        verify_user_contact_count(self, AuthUserContactTestCases.user1_id, 1)
        rv = self.app.post('/contact/12345/',
                 data='{"first_name": "Best", "last_name": "Friend", "email": "bestfriend@test.com", "phone": "1234567890"}',
                 content_type='application/json',
                 headers = {'Authorization': AuthUserContactTestCases.user1_token})
        self.assertEqual(200, rv.status_code)
        verify_contact_count(self, 2)
        verify_user_contact_count(self, AuthUserContactTestCases.user1_id, 1)

    # def test_contact_post_missing_email(self):
    #     rv = self.app.post('/contact/',
    #             data='{"first_name": "Best", "last_name": "Friend", "phone": "1234567891"}',
    #             content_type='application/json',
    #             headers = {'Authorization': AuthUserContactTestCases.user1_token})
    #     self.assertEqual(404, rv.status_code)
    #     # verify_contact_count(self, 1)


    # # maybe add tests to verify the validity of email and phone? Not in the API currently though

    # # need tests for put but need to solve post problem first
    def test_contact_list_get(self):
         rv = self.app.get('/contacts/',
             headers = {'Authorization': AuthUserContactTestCases.user1_token})
         self.assertEqual(200, rv.status_code)
         data = loads(rv.data)
         self.assertEqual('First1', data['contacts'][0]['first_name'])
         self.assertEqual('Contact1', data['contacts'][0]['last_name'])
         self.assertEqual('contact1@example.com', data['contacts'][0]['email'])
         self.assertEqual('1234567890', data['contacts'][0]['phone'])

         rv = self.app.get('/contacts/',
             headers = {'Authorization': AuthUserContactTestCases.user2_token})
         self.assertEqual(200, rv.status_code)
         data = loads(rv.data)
         self.assertEqual('First2', data['contacts'][0]['first_name'])
         self.assertEqual('Contact2', data['contacts'][0]['last_name'])
         self.assertEqual('contact2@example.com', data['contacts'][0]['email'])
         self.assertEqual('1234567890', data['contacts'][0]['phone'])