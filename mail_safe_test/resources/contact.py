"""
contact.py

"""

from flask import request, Response, abort, make_response
from flask.ext.restful import Resource, fields, marshal_with, reqparse
from google.appengine.ext import ndb
from mail_safe_test.custom_fields import NDBUrl
from mail_safe_test.auth import current_user, user_required, admin_required, UserModel

# Public exports
contact_fields = {
    'first_name': fields.String,
    'last_name': fields.String,
    'email': fields.String,
    'phone': fields.String,
    'uri': NDBUrl('/user/contact/')
}

# Create an instance of a RequestParser with the correct arguments
def parser(required_email, required_phone):
    parser = reqparse.RequestParser()
    parser.add_argument('first_name', type = str, location = 'json')
    parser.add_argument('last_name', type = str, location = 'json')
    parser.add_argument('email', type = str, required = required_email, location = 'json')
    parser.add_argument('phone', type = str, required = required_phone, location = 'json')
    return parser

class ContactModel(ndb.Model):
    first_name = ndb.StringProperty()
    last_name = ndb.StringProperty()
    email = ndb.StringProperty()
    phone = ndb.StringProperty()
    created = ndb.DateTimeProperty(auto_now_add=True)

    @classmethod
    def query_by_id(cls, user_id, key_id):
        contact_key = ndb.Key(UserModel, user_id, ContactModel, key_id)
        return contact_key.get()

    @classmethod
    def query_by_owner(cls, user):
        return ContactModel.query(ancestor=user.key).fetch()

class ContactListAPI(Resource):
    method_decorators = [user_required]
    contact_list_fields = {'contacts': fields.List(fields.Nested(contact_fields))}

    def __init__(self):
        self.post_parser = parser(True, True)
        super(ContactListAPI, self).__init__()

    @marshal_with(contact_list_fields)
    def get(self):
        user = current_user()
        contacts = ContactModel.query_by_owner(user)
        return {'contacts': contacts}

    @marshal_with(contact_fields)
    def post(self):
        user = current_user()
        args = self.post_parser.parse_args()
        contact = ContactModel(parent=ndb.Key(UserModel, user.key.id()), **args)
        contact.put()
        return contact

    @marshal_with(contact_list_fields)
    def delete(self):
        user = current_user()
        ndb.delete_multi(ContactModel.query(ancestor=user.key).fetch(keys_only=True))
        contacts = ContactModel.query_by_owner(user)
        return {'contacts': contacts}

class ContactAPI(Resource):
    method_decorators = [user_required]

    def __init__(self):
        self.put_parser = parser(False, False)
        super(ContactAPI, self).__init__()

    @marshal_with(contact_fields)
    def get(self, key_id):
        user = current_user()
        contact = ContactModel.query_by_id(user.key.id(), key_id)
        if contact is None:
            abort(404)
        return contact

    @marshal_with(contact_fields)
    def put(self, key_id):
        user = current_user()
        contact = ContactModel.query_by_id(user.key.id(), key_id)
        if contact is None:
            abort(404)
        args = self.put_parser.parse_args()
        args = {k:v for (k, v) in args.items() if v is not None}  # Remove empty arguments
        contact.populate(**args)
        contact.put()
        return contact

    def delete(self, key_id):
        user = current_user()
        contact = ContactModel.query_by_id(user.key.id(), key_id)
        if contact is None:
            abort(404)
        contact.key.delete()
        return make_response("", 204)
