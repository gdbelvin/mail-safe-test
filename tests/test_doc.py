#!/usr/bin/env python
# encoding: utf-8
"""
test_doc.py

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
    self.testbed = testbed.Testbed()
    self.testbed.activate()
    self.testbed.init_datastore_v3_stub()
    self.testbed.init_user_stub()
    self.testbed.init_memcache_stub()

def setup_documents(self):
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

        # Provision a document for both users
        self.d_id = '12345'
        self.d_title = "A Title"
        self.d_content = "Hello. This is a test document. With content."
        self.d_status = 0
        document_fields = {
            'id': self.d_id,
            'title': self.d_title,
            'content': self.d_content,
            'status': self.d_status
        }
        document = DocModel(parent=ndb.Key(UserModel, self.user1_id), **document_fields)
        document.put()

        document_fields = {
            'id': '67890',
            'title': "Another Title",
            'content': "Howdy. This is a different test document. With other content. And exclamation points!",
            'status': 1
        }
        document = DocModel(parent=ndb.Key(UserModel, self.user2_id), **document_fields)
        document.put()

        self.document_count = 2
        
def verify_document_count(self, document_count):
    docs = DocModel.query().fetch()
    self.assertEqual(document_count, len(docs))

def verify_user_document_count(self, user_id, document_count):
    docs = DocModel.query(ancestor=ndb.Key(UserModel, user_id)).fetch()
    self.assertEqual(document_count, len(docs))

    
class NonAuthContactTestCases(TestCase):

    def setUp(self):
        common_setUp(self)
        setup_documents(self)
        verify_document_count(self, self.document_count)
        self.post_data = {
            'title': "Titleist",
            'content': "This is a short test document",
            'status': 0
        }
        self.put_data = {"status": "Published"}

        self.verifications = {}

        self.verifications[("GET", "/user/doc/")] = 404
        self.verifications[("PUT", "/user/doc/")] = 404
        self.verifications[("POST", "/user/doc/")] = 404
        self.verifications[("DELETE", "/user/doc/")] = 404

        self.verifications[("GET", "/user/doc/12/")] = 403
        self.verifications[("PUT", "/user/doc/12/")] = 403
        self.verifications[("POST", "/user/doc/12/")] = 405
        self.verifications[("DELETE", "/user/doc/12/")] = 403

        self.verifications[("GET", "/user/doc/12345/")] = 403
        self.verifications[("PUT", "/user/doc/12345/")] = 403
        self.verifications[("POST", "/user/doc/12345/")] = 405
        self.verifications[("DELETE", "/user/doc/12345/")] = 403

        self.verifications[("GET", '/user/docs/')] = 403
        self.verifications[("PUT", '/user/docs/')] = 405
        self.verifications[("POST", '/user/docs/')] = 403
        self.verifications[("DELETE", '/user/docs/')] = 403

    def tearDown(self):
        self.testbed.deactivate()

    def test_doc_create(self):
        rv = self.app.post('/user/docs/',
            data=dumps({"content": "This is my revised testing document."}),
            content_type='application/json',
            headers={'Authorization': self.user1_token}
            )
        self.assertEqual(200, rv.status_code)

    def test_doc_none_put(self):
        rv = self.app.put('/user/doc/25/',
            data=dumps({"content": "This is my revised testing document."}),
            content_type='application/json',
            headers={'Authorization': self.user1_token})

    def test_document_no_auth(self):
        errors=[]
        for request in self.verifications:
            method = request[0]
            url = request[1]
            response = self.verifications[request]

            if "GET" == method:
                rv = self.app.get(url)
                verify_document_count(self, self.document_count)
            elif "POST" == method:
                rv = self.app.post(url, data=dumps(self.post_data),
                                   content_type='application/json')
                verify_document_count(self, self.document_count)
            elif "PUT" == method:
                rv = self.app.put(url, data=dumps(self.put_data),
                                  content_type='application/json')
                verify_document_count(self, self.document_count)
            elif "DELETE" == method:
                rv = self.app.delete(url)
                verify_document_count(self, self.document_count)
            else:
                self.assertFalse(false, "This HTTP method is unsupported")

            if (response != rv.status_code):
                errors.append("%s %s returned %d" % (method, url, rv.status_code))
        self.assertFalse(len(errors) > 0, errors)

    def test_document_invalid_auth(self):
        auth = {'headers': {'Authorization': 'invalid'}}
        errors=[]
        for request in self.verifications:
            method = request[0]
            url = request[1]
            response = self.verifications[request]

            if "GET" == method:
                rv = self.app.get(url, **auth)
                verify_document_count(self, self.document_count)
            elif "POST" == method:
                rv = self.app.post(url, data=dumps(self.post_data),
                                   content_type='application/json', **auth)
                verify_document_count(self, self.document_count)
            elif "PUT" == method:
                rv = self.app.put(url, data=dumps(self.put_data),
                                  content_type='application/json', **auth)
                verify_document_count(self, self.document_count)
            elif "DELETE" == method:
                rv = self.app.delete(url, **auth)
                verify_document_count(self, self.document_count)
            else:
                self.assertFalse(false, "This HTTP method is unsupported")

            if (response != rv.status_code):
                errors.append("%s %s returned %d" % (method, url, rv.status_code))
        self.assertFalse(len(errors) > 0, errors)

class AuthUserDocTestCases(TestCase):

    def setUp(self):
        common_setUp(self)
        setup_documents(self)

        self.post_data = {
            'title': "Titleist",
            'content': "This is a short test document",
            'status': 0
        }
        self.put_data = {"status": "Published"}

    def tearDown(self):
        self.testbed.deactivate()

    def test_document_id_none_get(self):
        rv = self.app.get('/user/doc/25/',
                headers={'Authorization': self.user1_token})
        self.assertEqual(404, rv.status_code)

    def test_document_id_get(self):
        rv = self.app.get('/user/doc/12345/',
                headers={'Authorization': self.user1_token})
        self.assertEqual(200, rv.status_code)

        data = loads(rv.data)
        self.assertEqual(self.d_content, data['content'])
        self.assertEqual(self.d_status, data['status'])

    def test_document_id_get_other_user(self):
        rv = self.app.get('/user/doc/67890/',
                headers={'Authorization': self.user1_token})
        self.assertEqual(404, rv.status_code)

        rv = self.app.get('/user/doc/12345/',
                headers={'Authorization': self.user2_token})
        self.assertEqual(404, rv.status_code)

    def test_document_id_none_put(self):
        rv = self.app.put('/user/doc/25/',
                data=dumps(self.put_data),
                headers={'Authorization': self.user1_token})
        self.assertEqual(404, rv.status_code)

    def test_document_id_none_delete(self):
        rv = self.app.delete('/user/doc/25/',
                headers={'Authorization': self.user1_token})
        self.assertEqual(404, rv.status_code)

    def test_document_id_post(self):
        rv = self.app.post('/user/doc/00101010/',
                data=dumps(self.post_data),
                content_type='application/json',
                headers={'Authorization': self.user1_token})
        # Posts are only allowed for the list endpoint.
        self.assertEqual(405, rv.status_code)

    def test_document_post(self):
        verify_document_count(self, 2)
        verify_user_document_count(self, self.user1_id, 1)

        rv = self.app.post('/user/docs/',
                data=dumps(self.post_data),
                content_type='application/json',
                headers={'Authorization': self.user1_token})
        self.assertEqual(200, rv.status_code)

        data = loads(rv.data)
        self.assertEqual("Titleist", data['title'])
        self.assertEqual("This is a short test document", data['content'])
        self.assertEqual(0, data['status'])

        verify_document_count(self, 3)
        verify_user_document_count(self, self.user1_id, 2)

    def test_document_post_duplicate(self):
        verify_document_count(self, 2)
        verify_user_document_count(self, self.user1_id, 1)

        rv = self.app.post('/user/docs/',
                data=dumps(self.post_data),
                content_type='application/json',
                headers = {'Authorization': self.user1_token})
        self.assertEqual(200, rv.status_code)

        verify_document_count(self, 3)
        verify_user_document_count(self, self.user1_id, 2)

    def test_document_post_missing_title(self):
        verify_document_count(self, self.document_count)
        verify_user_document_count(self, self.user1_id, 1)

        post_data = self.post_data.copy()
        del(post_data['title'])

        rv = self.app.post('/user/docs/',
                data=dumps(post_data),
                content_type='application/json',
                headers={'Authorization': self.user1_token})
        self.assertEqual(200, rv.status_code)

        verify_document_count(self, 3)
        verify_user_document_count(self, self.user1_id, 2)

    def test_document_post_missing_content(self):
        verify_document_count(self, self.document_count)
        verify_user_document_count(self, self.user1_id, 1)

        post_data = self.post_data.copy()
        del(post_data['content'])

        rv = self.app.post('/user/docs/',
                data=dumps(post_data),
                content_type='application/json',
                headers={'Authorization': self.user1_token})
        self.assertEqual(200, rv.status_code)

        verify_document_count(self, 3)
        verify_user_document_count(self, self.user1_id, 2)

    def test_document_post_missing_content(self):
        verify_document_count(self, self.document_count)
        verify_user_document_count(self, self.user1_id, 1)

        post_data = self.post_data.copy()
        del(post_data['content'])

        rv = self.app.post('/user/docs/',
                data=dumps(post_data),
                content_type='application/json',
                headers={'Authorization': self.user1_token})
        self.assertEqual(200, rv.status_code)

        verify_document_count(self, 3)
        verify_user_document_count(self, self.user1_id, 2)

    def test_document_post_missing_status(self):
        verify_document_count(self, self.document_count)
        verify_user_document_count(self, self.user1_id, 1)

        post_data = self.post_data.copy()
        del(post_data['status'])

        rv = self.app.post('/user/docs/',
                data=dumps(post_data),
                content_type='application/json',
                headers={'Authorization': self.user1_token})
        self.assertEqual(200, rv.status_code)

        verify_document_count(self, 3)
        verify_user_document_count(self, self.user1_id, 2)

    def test_document_put(self):
        rv = self.app.put('/user/doc/12345/',
                data='{"content": "Changed"}',
                content_type='application/json',
                headers={'Authorization': self.user1_token})
        self.assertEqual(200, rv.status_code)

        data = loads(rv.data)
        self.assertEqual(self.d_title, data['title'])
        self.assertEqual("Changed", data['content'])
        self.assertEqual(self.d_status, data['status'])

    def test_document_put_all_fields(self):
        rv = self.app.put('/user/doc/12345/',
                data='{"content": "Changed", "title": "A Different Title", "status": 1}',
                content_type='application/json',
                headers = {'Authorization': self.user1_token})
        self.assertEqual(200, rv.status_code)

        data = loads(rv.data)
        self.assertEqual("A Different Title", data['title'])
        self.assertEqual("Changed", data['content'])
        self.assertEqual(1, data['status'])

    def test_document_list_get(self):
        rv = self.app.get('/user/docs/',
                headers={'Authorization': self.user1_token})
        self.assertEqual(200, rv.status_code)
        data = loads(rv.data)
        self.assertEqual(self.d_title, data['docs'][0]['title'])
        self.assertEqual(self.d_content, data['docs'][0]['content'])
        self.assertEqual(self.d_status, data['docs'][0]['status'])

        rv = self.app.get('/user/docs/',
                headers={'Authorization': self.user2_token})
        self.assertEqual(200, rv.status_code)

        data = loads(rv.data)
        self.assertEqual("Another Title", data['docs'][0]['title'])
        self.assertEqual("Howdy. This is a different test document. With other content. And exclamation points!", data['docs'][0]['content'])
        self.assertEqual(1, data['docs'][0]['status'])

    def test_document_list_delete(self):
        verify_document_count(self, 2)
        verify_user_document_count(self, self.user1_id, 1)
        verify_user_document_count(self, self.user2_id, 1)

        rv = self.app.delete('/user/docs/',
                headers={'Authorization': self.user1_token})
        self.assertEqual(200, rv.status_code)

        data = loads(rv.data)
        self.assertEqual([], data['docs'])

        verify_document_count(self, 1)
        verify_user_document_count(self, self.user1_id, 0)
        verify_user_document_count(self, self.user2_id, 1)
