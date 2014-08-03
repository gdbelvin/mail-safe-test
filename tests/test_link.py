"""
test_link.py

"""

from google.appengine.ext import ndb
from google.appengine.ext import testbed
from json import loads, dumps
from unittest import TestCase
from mail_safe_test import app
from mail_safe_test.auth import UserModel
from mail_safe_test.resources.doc import DocModel

def common_setUp(self):
    app.config['TESTING'] = True
    app.config['CSRF_ENABLED'] = False
    self.app = app.test_client()
    self.testbed = testbed.Testbed()
    self.testbed.activate()
    self.testbed.init_datastore_v3_stub()
    self.testbed.init_user_stub()
    self.testbed.init_memcache_stub()

class MailTest(TestCase):
    def setUp(self):
        common_setUp(self)

        # Create a user
        self.user_id = '1'
        self.user_token = 'valid_user'
        args = {'id': self.user_id,
                'first_name': 'Testy',
                'last_name': 'McTest',
                'email': 'test@example.com',
                }
        user = UserModel(**args)
        user.put()

        # Create a doc
        args = {'content': 'Test content',
                'status': 'sent',
                }
        doc = DocModel(parent=user.key, **args)
        doc.put()
        self.doc_id = str(doc.key.id())

        # TODO: Create a contact


    def tearDown(self):
        self.testbed.deactivate()

    def test_send_mail(self):
# Create doc
        url = '/user/mail/'
        data = {
                'doc_id': self.doc_id,
                #TODO: add list 'list': list_id
                }
        rv = self.app.post(url, data=dumps(data),
                content_type='application/json',
                headers={'Authorization': self.user_token}
                )
        self.assertEqual(200, rv.status_code)
