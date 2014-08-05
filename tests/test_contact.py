#!/usr/bin/env python
# encoding: utf-8
"""
test_contact.py

"""

from google.appengine.ext import ndb
from google.appengine.ext import testbed
from json import loads, dumps
from unittest import TestCase
from mail_safe_test import app
from mail_safe_test.auth import UserModel
from mail_safe_test.resources.contact import ContactListAPI, ContactAPI, ContactModel

def common_setUp(self):
    # Flask apps testing. See: http://flask.pocoo.org/docs/testing/
    app.config['TESTING'] = True
    app.config['CSRF_ENABLED'] = False
    self.app = app.test_client()
    # Setup app engine test bed. See:
    # http://code.google.com/appengine/docs/python/tools/localunittesting.html#Introducing_the_Python_Testing_Utilities
    self.testbed = testbed.Testbed()
    self.testbed.activate()
    self.testbed.init_datastore_v3_stub()
    self.testbed.init_user_stub()
    self.testbed.init_memcache_stub()

def setup_contacts(self):
        # Provision two valid users
        self.user1_id = '1'
        self.user1_token = "valid_user"

        self.user2_id = '2'
        self.user2_token = "valid_user2"

        args = {
            "id": self.user1_id,
            "first_name": "Testy",
            "last_name": "McTest",
            "email": "user@example.com"
        }
        user = UserModel(**args)
        user.put()

        args["id"] = self.user2_id
        user = UserModel(**args)
        user.put()

        # Provision a contact for both users
        self.c_id = '12345'
        self.c_fname = "Firstname"
        self.c_lname = "Lastname"
        self.c_email = "contact1@example.com"
        self.c_phone = "1234567890"
        contact_fields = {
            'id': self.c_id,
            'first_name': self.c_fname,
            'last_name': self.c_lname,
            'email': self.c_email,
            'phone': self.c_phone
        }
        contact = ContactModel(parent=ndb.Key(UserModel, self.user1_id), **contact_fields)
        contact.put()

        contact_fields = {
            'id': '00000',
            'first_name': "First2",
            'last_name': "Contact2",
            'email': "contact2@example.com",
            'phone': "1234567890"
        }
        contact = ContactModel(parent=ndb.Key(UserModel, self.user2_id), **contact_fields)
        contact.put()

        self.c_num = 2

def verify_contact_count(self, contact_count):
    contacts = ContactModel.query().fetch()
    self.assertEqual(contact_count, len(contacts))

def verify_user_contact_count(self, user_id, contact_count):
    contacts = ContactModel.query(ancestor=ndb.Key(UserModel, user_id)).fetch()
    self.assertEqual(contact_count, len(contacts))

class NonAuthContactTestCases(TestCase):

    def setUp(self):
        common_setUp(self)
        setup_contacts(self)
        verify_contact_count(self, self.c_num)
        self.post_data = {
            "first_name": "Best",
            "last_name": "Friend",
            "email": "bestfriend@test.com",
            "phone": "1234567890"
        }
        self.put_data = {"first_name": "Changed"}
        
        self.verifications = {}

        self.verifications[("GET", "/user/contact/")] = 404
        self.verifications[("PUT", "/user/contact/")] = 404
        self.verifications[("POST", "/user/contact/")] = 404
        self.verifications[("DELETE", "/user/contact/")] = 404

        self.verifications[("GET", "/user/contact/12/")] = 403
        self.verifications[("PUT", "/user/contact/12/")] = 403
        self.verifications[("POST", "/user/contact/12/")] = 405
        self.verifications[("DELETE", "/user/contact/12/")] = 403

        self.verifications[("GET", "/user/contact/12345/")] = 403
        self.verifications[("PUT", "/user/contact/12345/")] = 403
        self.verifications[("POST", "/user/contact/12345/")] = 405
        self.verifications[("DELETE", "/user/contact/12345/")] = 403

        self.verifications[("GET", '/user/contacts/')] = 403
        self.verifications[("PUT", '/user/contacts/')] = 405
        self.verifications[("POST", '/user/contacts/')] = 403
        self.verifications[("DELETE", '/user/contacts/')] = 403

    def tearDown(self):
        self.testbed.deactivate()

    def test_contact_no_auth(self):
        errors=[]
        for request in self.verifications:
            method = request[0]
            url = request[1]
            response = self.verifications[request]

            if "GET" == method:
                rv = self.app.get(url)
                verify_contact_count(self, self.c_num)
            elif "POST" == method:
                rv = self.app.post(url, data=dumps(self.post_data),
                                   content_type='application/json')
                verify_contact_count(self, self.c_num)
            elif "PUT" == method:
                rv = self.app.put(url, data=dumps(self.put_data),
                                  content_type='application/json')
                verify_contact_count(self, self.c_num)
            elif "DELETE" == method:
                rv = self.app.delete(url)
                verify_contact_count(self, self.c_num)
            else:
                self.assertFalse(false, "This HTTP method is unsupported")

            if (response != rv.status_code):
                errors.append("%s %s returned %d" % (method, url, rv.status_code))
        self.assertFalse(len(errors) > 0, errors)

    def test_contact_invalid_auth(self):
        auth = {'headers': {'Authorization': 'invalid'}}
        errors=[]
        for request in self.verifications:
            method = request[0]
            url = request[1]
            response = self.verifications[request]

            if "GET" == method:
                rv = self.app.get(url, **auth)
                verify_contact_count(self, self.c_num)
            elif "POST" == method:
                rv = self.app.post(url, data=dumps(self.post_data),
                                   content_type='application/json', **auth)
                verify_contact_count(self, self.c_num)
            elif "PUT" == method:
                rv = self.app.put(url, data=dumps(self.put_data),
                                  content_type='application/json', **auth)
                verify_contact_count(self, self.c_num)
            elif "DELETE" == method:
                rv = self.app.delete(url, **auth)
                verify_contact_count(self, self.c_num)
            else:
                self.assertFalse(false, "This HTTP method is unsupported")

            if (response != rv.status_code):
                errors.append("%s %s returned %d" % (method, url, rv.status_code))
        self.assertFalse(len(errors) > 0, errors)
        
class UserAuthContactTestCases(TestCase):

    def setUp(self):
        common_setUp(self)
        setup_contacts(self)
        self.post_data = {
            "first_name": "Best",
            "last_name": "Friend",
            "email": "bestfriend@test.com",
            "phone": "1234567890"
        }
        self.put_data={"first_name": "Changed"}

    def tearDown(self):
    	self.testbed.deactivate()

    def test_contact_id_none_get(self):
        rv = self.app.get('/user/contact/25/',
                headers={'Authorization': self.user1_token})
        self.assertEqual(404, rv.status_code)

    def test_contact_id_get(self):
        rv = self.app.get('/user/contact/12345/',
                headers={'Authorization': self.user1_token})
        self.assertEqual(200, rv.status_code)

        data = loads(rv.data)
        self.assertEqual(self.c_fname, data['first_name'])
        self.assertEqual(self.c_lname, data['last_name'])
        self.assertEqual(self.c_email, data['email'])
        self.assertEqual(self.c_phone, data['phone'])

    def test_contact_id_get_other_user(self):
        rv = self.app.get('/user/contact/00000/',
                headers={'Authorization': self.user1_token})
        self.assertEqual(404, rv.status_code)

        rv = self.app.get('/user/contact/12345/',
                headers={'Authorization': self.user2_token})
        self.assertEqual(404, rv.status_code)
        
    def test_contact_id_none_put(self):
        rv = self.app.put('/user/contact/25/',
                data=self.put_data,
                headers={'Authorization': self.user1_token})
        self.assertEqual(404, rv.status_code)

    def test_contact_id_none_delete(self):
        rv = self.app.delete('/user/contact/25/',
                headers={'Authorization': self.user1_token})
        self.assertEqual(404, rv.status_code)

    def test_contact_id_post(self):
        rv = self.app.post('/user/contact/00101010/',
                data=dumps(self.post_data),
                content_type='application/json',
                headers={'Authorization': self.user1_token})
        # Posts are only allowed for the list endpoint.
        self.assertEqual(405, rv.status_code)

    def test_contact_post(self):
        verify_contact_count(self, 2)
        verify_user_contact_count(self, self.user1_id, 1)

        rv = self.app.post('/user/contacts/',
                data=dumps(self.post_data),
                content_type='application/json',
                headers={'Authorization': self.user1_token})
        self.assertEqual(200, rv.status_code)

        data = loads(rv.data)
        self.assertEqual('Best', data['first_name'])
        self.assertEqual('Friend', data['last_name'])
        self.assertEqual('bestfriend@test.com', data['email'])
        self.assertEqual('1234567890', data['phone'])

        verify_contact_count(self, 3)
        verify_user_contact_count(self, self.user1_id, 2)

    def test_contact_post_duplicate(self):
        verify_contact_count(self, 2)
        verify_user_contact_count(self, self.user1_id, 1)

        rv = self.app.post('/user/contacts/',
                data=dumps(self.post_data),
                content_type='application/json',
                headers = {'Authorization': self.user1_token})
        # BUG (gdbelvin 8/2/14) - This verification currently fails
        # because the email address is not required to be unique and
        # thus the insertion successfully creates a duplicate contact
        self.assertEqual(409, rv.status_code, "Gary needs to decide if duplicate contacts are allowed")

        verify_contact_count(self, 2)
        verify_user_contact_count(self, self.user1_id, 1)

    def test_contact_post_missing_email(self):
        verify_contact_count(self, self.c_num)
        verify_user_contact_count(self, self.user1_id, 1)

        post_data = self.post_data.copy()
        del(post_data['email'])

        rv = self.app.post('/user/contacts/',
                data=dumps(post_data),
                content_type='application/json',
                headers={'Authorization': self.user1_token})
        self.assertEqual(400, rv.status_code)

        verify_contact_count(self, 2)
        verify_user_contact_count(self, self.user1_id, 1)

    def test_contact_post_missing_phone(self):
        verify_contact_count(self, 2)
        verify_user_contact_count(self, self.user1_id, 1)

        post_data = self.post_data.copy()
        del(post_data['phone'])

        rv = self.app.post('/user/contacts/',
                data=dumps(post_data),
                content_type='application/json',
                headers={'Authorization': self.user1_token})
        self.assertEqual(400, rv.status_code)

        verify_contact_count(self, 2)
        verify_user_contact_count(self, self.user1_id, 1)

    # maybe add tests to verify the validity of email and phone? Not in
    # the API currently though

    def test_contact_put(self):
        rv = self.app.put('/user/contact/12345/',
                data=dumps(self.put_data),
                content_type='application/json',
                headers={'Authorization': self.user1_token})
        self.assertEqual(200, rv.status_code)

        data = loads(rv.data)
        self.assertEqual('Changed', data['first_name'])
        self.assertEqual(self.c_lname, data['last_name'])
        self.assertEqual(self.c_email, data['email'])
        self.assertEqual(self.c_phone, data['phone'])

    def test_contact_put_all_fields(self):
        rv = self.app.put('/user/contact/12345/',
                data='{"first_name": "Changed", "last_name": "McChanged", "email": "changed@example.com", "phone": "0987654321"}',
                content_type='application/json',
                headers = {'Authorization': self.user1_token})
        self.assertEqual(200, rv.status_code)
        
        data = loads(rv.data)
        self.assertEqual('Changed', data['first_name'])
        self.assertEqual('McChanged', data['last_name'])
        self.assertEqual('changed@example.com', data['email'])
        self.assertEqual('0987654321', data['phone'])
        
    def test_contact_list_get(self):
        rv = self.app.get('/user/contacts/',
                headers={'Authorization': self.user1_token})
        self.assertEqual(200, rv.status_code)
        data = loads(rv.data)
        self.assertEqual(self.c_fname, data['contacts'][0]['first_name'])
        self.assertEqual(self.c_lname, data['contacts'][0]['last_name'])
        self.assertEqual(self.c_email, data['contacts'][0]['email'])
        self.assertEqual(self.c_phone, data['contacts'][0]['phone'])

        rv = self.app.get('/user/contacts/',
                headers={'Authorization': self.user2_token})
        self.assertEqual(200, rv.status_code)
        data = loads(rv.data)
        self.assertEqual('First2', data['contacts'][0]['first_name'])
        self.assertEqual('Contact2', data['contacts'][0]['last_name'])
        self.assertEqual('contact2@example.com', data['contacts'][0]['email'])
        self.assertEqual('1234567890', data['contacts'][0]['phone'])
    
    def test_contact_list_delete(self):
        verify_contact_count(self, 2)
        verify_user_contact_count(self, self.user1_id, 1)
        verify_user_contact_count(self, self.user2_id, 1)

        rv = self.app.delete('/user/contacts/',
                headers={'Authorization': self.user1_token})
        self.assertEqual(200, rv.status_code)

        data = loads(rv.data)
        self.assertEqual([], data['contacts'])
        
        verify_contact_count(self, 1)
        verify_user_contact_count(self, self.user1_id, 0)
        verify_user_contact_count(self, self.user2_id, 1)