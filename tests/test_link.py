"""
test_link.py

"""

from google.appengine.ext import ndb
from google.appengine.ext import testbed
from json import loads, dumps
from unittest import TestCase
from mail_safe_test import app
from mail_safe_test.auth import UserModel
from mail_safe_test.resources.contact import ContactModel
from mail_safe_test.resources.doc import DocModel
from mail_safe_test.resources.link import LinkModel

def common_setUp(self):
    app.config['TESTING'] = True
    app.config['CSRF_ENABLED'] = False
    self.app = app.test_client()
    self.testbed = testbed.Testbed()
    self.testbed.activate()
    self.testbed.init_datastore_v3_stub()
    self.testbed.init_user_stub()
    self.testbed.init_memcache_stub()
    self.testbed.init_mail_stub()
    self.mail_stub = self.testbed.get_stub(testbed.MAIL_SERVICE_NAME)


class MailTest(TestCase):
    def setUp(self):
        common_setUp(self)

        # Create a user
        self.user_id = '1'
        self.user_token = 'valid_user'
        user_args = {'id': self.user_id,
                'first_name': 'Testy',
                'last_name': 'McTest',
                'email': 'test@example.com',
                }
        user = UserModel(**user_args)
        user.put()

        # Create a doc
        doc_args = {'content': 'Test content',
                'status': 'sent',
                }
        doc = DocModel(parent=user.key, **doc_args)
        doc.put()
        self.doc_id = str(doc.key.id())

        self.contact_args = {'email': 'contact1@test.com',
                            'phone': '1231231234'}
        contact = ContactModel(parent=user.key, **self.contact_args)
        contact.put()

    def tearDown(self):
        self.testbed.deactivate()

    def test_send_mail(self):
        num_links_before = LinkModel.query().count()
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
        num_users = 1
        # Correct number of links
        num_links_after = LinkModel.query().count()
        self.assertEqual(num_links_before + num_users, num_links_after)
        # Correct number of emails
        messages = self.mail_stub.get_sent_messages(to=self.contact_args['email'])
        self.assertEqual(1, len(messages))
        self.assertEqual(self.contact_args['email'], messages[0].to)

