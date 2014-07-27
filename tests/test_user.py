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

def verify_user_count(self, user_count):
    users = UserModel.query().fetch()
    self.assertEqual(user_count, len(users))

class NonAuthUserTestCases(TestCase):

    def setUp(self):
        common_setUp(self)

    def tearDown(self):
        self.testbed.deactivate()

    def test_user_get_no_auth(self):
        rv = self.app.get('/user/')
        self.assertEqual(403, rv.status_code)

    def test_user_get_invalid_auth(self):
        rv = self.app.get('/user/',
                headers = {'Authorization': 'invalid'})
        self.assertEqual(403, rv.status_code)

    def test_user_id_get_no_auth(self):
        rv = self.app.get('/user/1/')
        self.assertEqual(404, rv.status_code)

    def test_user_id_get_invalid_auth(self):
        rv = self.app.get('/user/1/',
                headers = {'Authorization': 'invalid'})
        self.assertEqual(404, rv.status_code)
    
    def test_user_post_no_auth(self):
        rv = self.app.post('/user/',
                data='{"first_name": "Testy", "last_name": "McTest", "email": "user@example.com"}',
                content_type='application/json')
        self.assertEqual(400, rv.status_code)
        verify_user_count(self, 0)

    def test_user_post_invalid_auth(self):
        rv = self.app.post('/user/',
                data='{"first_name": "Testy", "last_name": "McTest", "email": "user@example.com"}',
                headers = {'Authorization': 'invalid'})
        self.assertEqual(400, rv.status_code)
        verify_user_count(self, 0)
        
    def test_user_put_no_auth(self):
        rv = self.app.put('/user/',
                data='{"first_name": "Changed"}',
                content_type='application/json')
        self.assertEqual(403, rv.status_code)
        
    def test_user_put_invalid_auth(self):
        rv = self.app.put('/user/',
                data='{"first_name": "Changed"}',
                content_type='application/json',
                headers = {'Authorization': 'invalid'})
        self.assertEqual(403, rv.status_code)
        
    def test_user_delete_no_auth(self):
        rv = self.app.delete('/user/')
        self.assertEqual(403, rv.status_code)

    def test_user_delete_invalid_auth(self):
        rv = self.app.delete('/user/',
                headers = {'Authorization': 'invalid'})
        self.assertEqual(403, rv.status_code)

    def test_users_get_no_auth(self):
        rv = self.app.get('/admin/users/')
        self.assertEqual(403, rv.status_code)

    def test_users_get_invalid_auth(self):
        rv = self.app.get('/admin/users/',
                headers = {'Authorization': 'invalid'})
        self.assertEqual(403, rv.status_code)
        
    def test_users_delete_no_auth(self):
        rv = self.app.delete('/admin/users/')
        self.assertEqual(403, rv.status_code)

    def test_users_delete_invalid_auth(self):
        rv = self.app.delete('/admin/users/',
            headers = {'Authorization': 'invalid'})
        self.assertEqual(403, rv.status_code)

class UserAuthUserTestCases(TestCase):

    def setUp(self):
        common_setUp(self)

        # Provision a valid user
        UserAuthUserTestCases.user_id = '111111111111111111111'
        UserAuthUserTestCases.user_token = "valid_user"

        UserAuthUserTestCases.user2_id = '111111111111111111112'
        UserAuthUserTestCases.user2_token = "valid_user2"

        args = {"id": UserAuthUserTestCases.user_id,
                "first_name": "Testy",
                "last_name": "McTest",
                "email": "user@example.com" }
        user = UserModel(**args)
        user.put()

    def tearDown(self):
        self.testbed.deactivate()

    def test_user_get(self):
        rv = self.app.get('/user/',
            headers = {'Authorization': UserAuthUserTestCases.user_token})
        self.assertEqual(200, rv.status_code)

    def test_user_id_get(self):
        rv = self.app.get('/user/1/',
            headers = {'Authorization': UserAuthUserTestCases.user_token})
        self.assertEqual(404, rv.status_code)
        
    def test_user_post(self):
        verify_user_count(self, 1)
        rv = self.app.post('/user/',
                data='{"first_name": "Testy", "last_name": "McTest", "email": "test@test.com"}',
                content_type='application/json',
                headers = {'Authorization': UserAuthUserTestCases.user2_token})
        self.assertEqual(200, rv.status_code)
        verify_user_count(self, 2)

        data = loads(rv.data)
        self.assertEqual('Testy', data['first_name'])
        self.assertEqual('McTest', data['last_name'])
        # BUG (gdbelvin 7/14/14): This verification currently fails because the request parsing code
        # ignores the POST data in favor of the validated email address in the token
        self.assertEqual('test@test.com', data['email'], "Gary needs to rationalize the persisted email address") 
        
    def test_user_post_duplicate(self):
        verify_user_count(self, 1)
        rv = self.app.post('/user/',
                data='{"first_name": "Testy", "last_name": "McTest", "email": "user@example.com"}',
                content_type='application/json',
                headers = {'Authorization': UserAuthUserTestCases.user_token})
        self.assertEqual(409, rv.status_code)
        verify_user_count(self, 1)

    def test_user_post_missing_email(self):
        rv = self.app.post('/user/',
                data='{"first_name": "Testy", "last_name": "McTest"}',
                content_type='application/json',
                headers = {'Authorization': UserAuthUserTestCases.user2_token})
        self.assertEqual(400, rv.status_code)
        verify_user_count(self, 1)
    
    # BUG (gdbelvin 7/14/14): This verification currently fails because the request parsing code
    # ignores the POST data in favor of the validated email address in the token. We need to
    # determine the correct handling scheme and if trusting the cookie, that OAuth token will 
    # always contain a valid email address.
    def test_user_post_invalid_email(self):
        rv = self.app.post('/user/',
                data='{"first_name": "Testy", "last_name": "McTest", "email": "1"}',
                content_type='application/json',
                headers = {'Authorization': UserAuthUserTestCases.user2_token})
        self.assertEqual(400, rv.status_code, "Gary needs to rationalize the persisted email address")
        verify_user_count(self, 1)

        rv = self.app.post('/user/',
                data='{"first_name": "Testy", "last_name": "McTest", "email": "notanemail"}',
                content_type='application/json',
                headers = {'Authorization': UserAuthUserTestCases.user2_token})
        self.assertEqual(400, rv.status_code, "Gary needs to rationalize the persisted email address")
        verify_user_count(self, 1)

    def test_user_put(self):
        rv = self.app.put('/user/',
            data='{"first_name": "Changed"}',
            content_type='application/json',
            headers = {'Authorization': UserAuthUserTestCases.user_token})
        self.assertEqual(200, rv.status_code)
        
        # BUG (gdbelvin 7/12/14): This verification currently fails because the request parsing code
        # assigns None to all unspecified request values, updating all entries with None in the DB.
        data = loads(rv.data)
        self.assertEqual('Changed', data['first_name'])
        self.assertEqual('McTest', data['last_name'], "Gary needs to fix request parsing for PUT")
        self.assertEqual('user@example.com', data['email'])
        
    def test_user_delete(self):
        verify_user_count(self, 1)
        rv = self.app.delete('/user/',
            headers = {'Authorization': UserAuthUserTestCases.user_token})
        self.assertEqual(204, rv.status_code)
        verify_user_count(self, 0)
        
    def test_user_delete_other_user(self):
        verify_user_count(self, 1)
        rv = self.app.delete('/user/',
            headers = {'Authorization': UserAuthUserTestCases.user2_token})
        self.assertEqual(403, rv.status_code)
        verify_user_count(self, 1)
        
    def test_user_delete_twice(self):
        verify_user_count(self, 1)
        rv = self.app.delete('/user/',
            headers = {'Authorization': UserAuthUserTestCases.user_token})
        self.assertEqual(204, rv.status_code)
        verify_user_count(self, 0)

        rv = self.app.delete('/user/',
            headers = {'Authorization': UserAuthUserTestCases.user_token})
        self.assertEqual(403, rv.status_code)
        verify_user_count(self, 0)

    def test_admin_users_get(self):
        rv = self.app.get('/admin/users/',
            headers = {'Authorization': UserAuthUserTestCases.user2_token})
        self.assertEqual(403, rv.status_code)
        
    def test_admin_users_delete(self):
        verify_user_count(self, 1)
        rv = self.app.delete('/admin/users/',
            headers = {'Authorization': UserAuthUserTestCases.user_token})
        self.assertEqual(403, rv.status_code)
        verify_user_count(self, 1)
        
    def test_admin_user_id_get(self):
        rv = self.app.get('/admin/user/111111111111111111111/',
            headers = {'Authorization': UserAuthUserTestCases.user_token})
        self.assertEqual(403, rv.status_code)
        

class AdminAuthUserTestCases(TestCase):

    def setUp(self):
        common_setUp(self)

        # Provision a valid admin user
        AdminAuthUserTestCases.admin_id = "222222222222222222222"
        AdminAuthUserTestCases.admin_token = "valid_admin"

        args = {"id": AdminAuthUserTestCases.admin_id,
                "first_name": "Admin",
                "last_name": "McAdmin",
                "email": "admin@example.com",
                "admin": True }
        user = UserModel(**args)
        user.put()
        
        # Provision a valid user
        AdminAuthUserTestCases.user_id = '111111111111111111111'
        AdminAuthUserTestCases.user_token = "valid_user"

        args = {"id": AdminAuthUserTestCases.user_id,
                "first_name": "Testy",
                "last_name": "McTest",
                "email": "user@example.com" }
        user = UserModel(**args)
        user.put()

    def tearDown(self):
        self.testbed.deactivate()

    def test_admin_users_get(self):
        rv = self.app.get('/admin/users/',
            headers = {'Authorization': AdminAuthUserTestCases.admin_token})
        self.assertEqual(200, rv.status_code)

        data = loads(rv.data)
        self.assertEqual('Testy', data['users'][0]['first_name'])
        self.assertEqual('McTest', data['users'][0]['last_name'])
        self.assertEqual('user@example.com', data['users'][0]['email'])

        self.assertEqual('Admin', data['users'][1]['first_name'])
        self.assertEqual('McAdmin', data['users'][1]['last_name'])
        self.assertEqual('admin@example.com', data['users'][1]['email'])

    def test_admin_users_delete(self):
        verify_user_count(self, 2)
        rv = self.app.delete('/admin/users/',
            headers = {'Authorization': AdminAuthUserTestCases.admin_token})
        self.assertEqual(200, rv.status_code)
        verify_user_count(self, 0)
        data = loads(rv.data)
        self.assertEqual([], data['users']);
    
    def test_admin_user_id_get(self):
        rv = self.app.get('/admin/user/' + AdminAuthUserTestCases.user_id + '/',
            headers = {'Authorization': AdminAuthUserTestCases.admin_token})
        self.assertEqual(200, rv.status_code)

        data = loads(rv.data)
        self.assertEqual('Testy', data['first_name'])
        self.assertEqual('McTest', data['last_name'])
        self.assertEqual('user@example.com', data['email'])
        
    def test_admin_user_id_get_invalid(self):
        rv = self.app.get('/admin/user/11/',
            headers = {'Authorization': AdminAuthUserTestCases.admin_token})
        self.assertEqual(404, rv.status_code)
        
    def test_admin_user_put(self):
        verify_user_count(self, 2)
        rv = self.app.put('/admin/user/' + AdminAuthUserTestCases.user_id + '/',
                data='{"first_name": "Changed"}',
                content_type='application/json',
                headers = {'Authorization': AdminAuthUserTestCases.admin_token})
        self.assertEqual(200, rv.status_code)

        # BUG (gdbelvin 7/12/14): This verification currently fails because the request parsing code
        # assigns None to all unspecified request values, updating all entries with None in the DB.
        data = loads(rv.data)
        self.assertEqual('Changed', data['first_name'])
        self.assertEqual('McTest', data['last_name'], "Gary needs to fix request parsing for PUT")
        self.assertEqual('user@example.com', data['email'])
        verify_user_count(self, 2)

    def test_admin_user_put_invalid(self):
        verify_user_count(self, 2)
        rv = self.app.put('/admin/user/11/',
                data='{"first_name": "Testy", "last_name": "McTest", "email": "test@test.com"}',
                content_type='application/json',
                headers = {'Authorization': AdminAuthUserTestCases.admin_token})
        self.assertEqual(404, rv.status_code)
        verify_user_count(self, 2)

    def test_admin_user_id_delete(self):
        verify_user_count(self, 2)
        rv = self.app.delete('/admin/user/' + AdminAuthUserTestCases.user_id + '/',
            headers = {'Authorization': AdminAuthUserTestCases.admin_token})
        self.assertEqual(204, rv.status_code)
        verify_user_count(self, 1)

    def test_admin_user_id_delete_invalid(self):
        verify_user_count(self, 2)
        rv = self.app.delete('/admin/user/11/',
            headers = {'Authorization': AdminAuthUserTestCases.admin_token})
        self.assertEqual(404, rv.status_code)
        verify_user_count(self, 2)