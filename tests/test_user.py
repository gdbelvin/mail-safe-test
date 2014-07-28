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
        self.post_data = {
            "first_name": "Testy",
            "last_name": "McTest",
            "email": "user@example.com",
            }

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
                data=dumps(self.post_data),
                content_type='application/json')
        self.assertEqual(400, rv.status_code)
        verify_user_count(self, 0)

    def test_user_post_invalid_auth(self):
        rv = self.app.post('/user/',
                data=dumps(self.post_data),
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
        self.user_id = '1'
        self.user_token = "valid_user"

        self.user2_id = '2'
        self.user2_token = "valid_user2"

        args = {"id": self.user_id,
                "first_name": "Testy",
                "last_name": "McTest",
                "email": "user@example.com" }
        user = UserModel(**args)
        user.put()

        self.post_data = {
            "first_name": "Testy",
            "last_name": "McTest",
            "email": "user@example.com",
            }


    def tearDown(self):
        self.testbed.deactivate()

    def test_user_get(self):
        rv = self.app.get('/user/',
            headers = {'Authorization': self.user_token})
        self.assertEqual(200, rv.status_code)

    def test_user_id_get(self):
        rv = self.app.get('/user/1/',
            headers = {'Authorization': self.user_token})
        self.assertEqual(404, rv.status_code)

    def test_user_post(self):
        verify_user_count(self, 1)
        rv = self.app.post('/user/',
                data=dumps(self.post_data),
                content_type='application/json',
                headers = {'Authorization': self.user2_token})
        self.assertEqual(200, rv.status_code)
        verify_user_count(self, 2)

        data = loads(rv.data)
        self.assertEqual(self.post_data['first_name'], data['first_name'])
        self.assertEqual(self.post_data['last_name'], data['last_name'])
        self.assertEqual(self.post_data['email'], data['email'])

    def test_user_post_duplicate(self):
        verify_user_count(self, 1)
        rv = self.app.post('/user/',
                data=dumps(self.post_data),
                content_type='application/json',
                headers = {'Authorization': self.user_token})
        self.assertEqual(409, rv.status_code)
        verify_user_count(self, 1)

    def test_user_post_missing_email(self):
        data = self.post_data.copy()
        data.pop('email')
        rv = self.app.post('/user/',
                data=dumps(data),
                content_type='application/json',
                headers = {'Authorization': self.user2_token})
        self.assertEqual(400, rv.status_code)
        verify_user_count(self, 1)

    def test_user_post_invalid_email(self):
        data = self.post_data.copy()
        data['email'] = 1
        rv = self.app.post('/user/', data=dumps(data),
                content_type='application/json',
                headers = {'Authorization': self.user2_token})
        self.assertEqual(400, rv.status_code)
        verify_user_count(self, 1)

        data['email'] = 'notanemail'
        rv = self.app.post('/user/', data=dumps(data),
                content_type='application/json',
                headers = {'Authorization': self.user2_token})
        self.assertEqual(400, rv.status_code)

    def test_user_put(self):
        rv = self.app.put('/user/',
            data='{"first_name": "Changed"}',
            content_type='application/json',
            headers = {'Authorization': self.user_token})
        self.assertEqual(200, rv.status_code)

        data = loads(rv.data)
        self.assertEqual('Changed', data['first_name'])
        self.assertEqual('McTest', data['last_name'])
        self.assertEqual('user@example.com', data['email'])

    def test_user_delete(self):
        verify_user_count(self, 1)
        rv = self.app.delete('/user/',
            headers = {'Authorization': self.user_token})
        self.assertEqual(204, rv.status_code)
        verify_user_count(self, 0)

    def test_user_delete_other_user(self):
        verify_user_count(self, 1)
        rv = self.app.delete('/user/',
            headers = {'Authorization': self.user2_token})
        self.assertEqual(403, rv.status_code)
        verify_user_count(self, 1)

    def test_user_delete_twice(self):
        verify_user_count(self, 1)
        rv = self.app.delete('/user/',
            headers = {'Authorization': self.user_token})
        self.assertEqual(204, rv.status_code)
        verify_user_count(self, 0)

        rv = self.app.delete('/user/',
            headers = {'Authorization': self.user_token})
        self.assertEqual(403, rv.status_code)
        verify_user_count(self, 0)

    def test_admin_users_get(self):
        rv = self.app.get('/admin/users/',
            headers = {'Authorization': self.user2_token})
        self.assertEqual(403, rv.status_code)
        
    def test_admin_users_delete(self):
        verify_user_count(self, 1)
        rv = self.app.delete('/admin/users/',
            headers = {'Authorization': self.user_token})
        self.assertEqual(403, rv.status_code)
        verify_user_count(self, 1)
        
    def test_admin_user_id_get(self):
        rv = self.app.get('/admin/user/3/',
            headers = {'Authorization': self.user_token})
        self.assertEqual(403, rv.status_code)
        

class AdminAuthUserTestCases(TestCase):

    def setUp(self):
        common_setUp(self)

        # Provision a valid admin user
        self.admin_id = "3"
        self.admin_token = "valid_admin"

        args = {"id": self.admin_id,
                "first_name": "Admin",
                "last_name": "McAdmin",
                "email": "admin@example.com",
                "admin": True }
        user = UserModel(**args)
        user.put()
        
        # Provision a valid user
        self.user_id = '1'
        self.user_token = "valid_user"

        args = {"id": self.user_id,
                "first_name": "Testy",
                "last_name": "McTest",
                "email": "user@example.com" }
        user = UserModel(**args)
        user.put()

    def tearDown(self):
        self.testbed.deactivate()

    def test_admin_users_get(self):
        rv = self.app.get('/admin/users/',
            headers = {'Authorization': self.admin_token})
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
            headers = {'Authorization': self.admin_token})
        self.assertEqual(200, rv.status_code)
        verify_user_count(self, 0)
        data = loads(rv.data)
        self.assertEqual([], data['users']);
    
    def test_admin_user_id_get(self):
        rv = self.app.get('/admin/user/' + self.user_id + '/',
            headers = {'Authorization': self.admin_token})
        self.assertEqual(200, rv.status_code)

        data = loads(rv.data)
        self.assertEqual('Testy', data['first_name'])
        self.assertEqual('McTest', data['last_name'])
        self.assertEqual('user@example.com', data['email'])
        
    def test_admin_user_id_get_invalid(self):
        rv = self.app.get('/admin/user/11/',
            headers = {'Authorization': self.admin_token})
        self.assertEqual(404, rv.status_code)
        
    def test_admin_user_put(self):
        verify_user_count(self, 2)
        rv = self.app.put('/admin/user/' + self.user_id + '/',
                data='{"first_name": "Changed"}',
                content_type='application/json',
                headers = {'Authorization': self.admin_token})
        self.assertEqual(200, rv.status_code)

        data = loads(rv.data)
        self.assertEqual('Changed', data['first_name'])
        self.assertEqual('McTest', data['last_name'],)
        self.assertEqual('user@example.com', data['email'])
        verify_user_count(self, 2)

    def test_admin_user_put_invalid(self):
        verify_user_count(self, 2)
        rv = self.app.put('/admin/user/11/',
                data='{"first_name": "Testy", "last_name": "McTest", "email": "test@test.com"}',
                content_type='application/json',
                headers = {'Authorization': self.admin_token})
        self.assertEqual(404, rv.status_code)
        verify_user_count(self, 2)

    def test_admin_user_id_delete(self):
        verify_user_count(self, 2)
        rv = self.app.delete('/admin/user/' + self.user_id + '/',
            headers = {'Authorization': self.admin_token})
        self.assertEqual(204, rv.status_code)
        verify_user_count(self, 1)

    def test_admin_user_id_delete_invalid(self):
        verify_user_count(self, 2)
        rv = self.app.delete('/admin/user/11/',
            headers = {'Authorization': self.admin_token})
        self.assertEqual(404, rv.status_code)
        verify_user_count(self, 2)
