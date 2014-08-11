"""
mail.py

"""

from flask import abort, url_for
from flask.ext.restful import Resource, marshal_with, reqparse
from google.appengine.api import mail
from mail_safe_test import app
from mail_safe_test.auth import current_user, user_required
from mail_safe_test.resources.contact import ContactModel
from mail_safe_test.resources.doc import DocModel
from mail_safe_test.resources.link import LinkModel
from uuid import uuid4

parser = reqparse.RequestParser()
parser.add_argument('doc_id', type = int, location = 'json', required = True)
parser.add_argument('list', type = str, location = 'json')

class Mail(Resource):
    method_decorators = [user_required]

    def post(self):
        user=current_user()
        args = parser.parse_args()
        doc = DocModel.query_by_id(user, args.doc_id)
        if not doc:
            print "doc not found"
            abort(404)

        contacts = ContactModel.query_by_owner(user)
        future_links = []
        emails = []
        for contact in contacts:
            uid = uuid4().get_hex()
            link = LinkModel(id=uid, contact=contact.key, doc=doc.key)
            future_links.append(link.put_async())
            url = url_for('/link/', key_id=link.key.id())
            emails += self.generate_email(contact.email, contact.first_name,
                                          user.first_name, url)

        for email in emails:
            mail.send_mail(**email)
        for future in future_links:
            future.get_result()  # Make sure the put completed.
        return {'result': 'sent'}

    def generate_email(self, to_email, to_name, from_name, link_url):
        subject = "A MailSafe Message From %s" % from_name
        message = """Dear %s,\n
            you have received a message from %s through MailSafe.\n
            Please click on the following link to view their message:\n
            %s\n
            The MailSafe Team""" % (to_name, from_name, link_url)
        from_email = app.config.get('SERVER_EMAIL')
        yield {'sender': from_email,
               'subject': subject,
               'body': message,
               'to':to_email}

