#!/usr/bin/env python
# encoding: utf-8
"""
test_user.py

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
    # Setup app engine test bed.
    # See: http://code.google.com/appengine/docs/python/tools/localunittesting.html#Introducing_the_Python_Testing_Utilities
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
            "email": "user@example.com"
        }
        self.put_data = {"first_name": "Changed"}

        self.verifications = {}

        self.verifications[("GET", "/user/")] = 403
        self.verifications[("PUT", "/user/")] = 403
        self.verifications[("POST", "/user/")] = 400
        self.verifications[("DELETE", "/user/")] = 403

        self.verifications[("GET", "/user/1/")] = 404
        self.verifications[("PUT", "/user/1/")] = 404
        self.verifications[("POST", "/user/1/")] = 404
        self.verifications[("DELETE", "/user/1/")] = 404

        self.verifications[("GET", "/admin/users/")] = 403
        self.verifications[("PUT", "/admin/users/")] = 405
        self.verifications[("POST", "/admin/users/")] = 405
        self.verifications[("DELETE", "/admin/users/")] = 403

    def tearDown(self):
        self.testbed.deactivate()

    def test_user_no_auth(self):
        errors=[]
        for request in self.verifications:
            method = request[0]
            url = request[1]
            response = self.verifications[request]

            if "GET" == method:
                rv = self.app.get(url)
                verify_user_count(self, 0)
            elif "POST" == method:
                rv = self.app.post(url, data=dumps(self.post_data),
                                   content_type='application/json')
                verify_user_count(self, 0)
            elif "PUT" == method:
                rv = self.app.put(url, data=dumps(self.put_data),
                                  content_type='application/json')
                verify_user_count(self, 0)
            elif "DELETE" == method:
                rv = self.app.delete(url)
                verify_user_count(self, 0)
            else:
                self.assertFalse(false, "This HTTP method is unsupported")

            if (response != rv.status_code):
                errors.append("%s %s returned %d" % (method, url, rv.status_code))
        self.assertFalse(len(errors) > 0, errors)

    def test_user_invalid_auth(self):
        auth = {'headers': {'Authorization': 'invalid'}}
        errors=[]
        for request in self.verifications:
            method = request[0]
            url = request[1]
            response = self.verifications[request]

            if "GET" == method:
                rv = self.app.get(url, **auth)
                verify_user_count(self, 0)
            elif "POST" == method:
                rv = self.app.post(url, data=dumps(self.post_data),
                                   content_type='application/json', **auth)
                verify_user_count(self, 0)
            elif "PUT" == method:
                rv = self.app.put(url, data=dumps(self.put_data),
                                  content_type='application/json', **auth)
                verify_user_count(self, 0)
            elif "DELETE" == method:
                rv = self.app.delete(url, **auth)
                verify_user_count(self, 0)
            else:
                self.assertFalse(false, "This HTTP method is unsupported")

            if (response != rv.status_code):
                errors.append("%s %s returned %d" % (method, url, rv.status_code))
        self.assertFalse(len(errors) > 0, errors)


class UserAuthUserTestCases(TestCase):

    def setUp(self):
        common_setUp(self)

        # Provision a valid user
        self.user_id = '1'
        self.user_token = "valid_user"

        self.user2_id = '2'
        self.user2_token = "valid_user2"

        args = {
            "id": self.user_id,
            "first_name": "Testy",
            "last_name": "McTest",
            "email": "user@example.com"
        }
        user = UserModel(**args)
        user.put()

        self.post_data = {
            "first_name": "Testy",
            "last_name": "McTest",
            "email": "user@example.com"
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

    # This test POSTs a unique email address with a unique token
    def test_user_post(self):
        data = self.post_data.copy()
        data['email'] = "test@test.com"
        verify_user_count(self, 1)
        rv = self.app.post('/user/',
                data=dumps(data),
                content_type='application/json',
                headers = {'Authorization': self.user2_token})
        self.assertEqual(200, rv.status_code)
        verify_user_count(self, 2)

        data = loads(rv.data)
        self.assertEqual(self.post_data['first_name'], data['first_name'])
        self.assertEqual(self.post_data['last_name'], data['last_name'])
        self.assertEqual("test@test.com", data['email'])
        
    # This test POSTs a duplicate email address with a unique token
    # NOTE: This shouldn't be possible unless we store the provided
    # email address but authenticate with a different adress.
    def test_user_post_duplicate_data(self):
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
        
    # This test POSTs a unique email address with a duplicate token
    def test_user_post_duplicate_users(self):
        data = self.post_data.copy()
        data['email'] = "test@test.com"
        verify_user_count(self, 1)
        rv = self.app.post('/user/',
                data=dumps(data),
                content_type='application/json',
                headers = {'Authorization': self.user_token})
        self.assertEqual(409, rv.status_code)
        verify_user_count(self, 1)

    # This test POSTs a duplicate email address with a duplicate token
    def test_user_post_duplicate_users(self):
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
    
    def test_user_put_all_fields(self):
        rv = self.app.put('/user/',
            data='{"first_name": "Changed", "last_name": "McChange", "email": "changed@example.com"}',
            content_type='application/json',
            headers = {'Authorization': self.user_token})
        self.assertEqual(200, rv.status_code)

        data = loads(rv.data)
        self.assertEqual('Changed', data['first_name'])
        self.assertEqual('McChange', data['last_name'])
        self.assertEqual('changed@example.com', data['email'])

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
        self.admin_id = '3'
        self.admin_token = "valid_admin"

        args = {
            "id": self.admin_id,
            "first_name": "Admin",
            "last_name": "McAdmin",
            "email": "admin@example.com",
            "admin": True
        }
        user = UserModel(**args)
        user.put()
        
        # Provision a valid user
        self.user_id = '1'
        self.user_token = "valid_user"

        args = {
            "id": self.user_id,
            "first_name": "Testy",
            "last_name": "McTest",
            "email": "user@example.com"
        }
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

    def test_admin_user_put_all_fields(self):
        verify_user_count(self, 2)
        rv = self.app.put('/admin/user/' + self.user_id + '/',
                data='{"first_name": "Changed", "last_name": "McChange", "email": "changed@example.com"}',
                content_type='application/json',
                headers = {'Authorization': self.admin_token})
        self.assertEqual(200, rv.status_code)

        data = loads(rv.data)
        self.assertEqual('Changed', data['first_name'])
        self.assertEqual('McChange', data['last_name'])
        self.assertEqual('changed@example.com', data['email'])
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
