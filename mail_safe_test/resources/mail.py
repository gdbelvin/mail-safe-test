"""
mail.py

"""

from flask import request, Response, abort, make_response
from flask.ext.restful import Resource, fields, marshal_with, reqparse
from google.appengine.ext import ndb, blobstore
from json import loads, dumps
from mail_safe_test.auth import current_user, user_required, admin_required, UserModel
from mail_safe_test.custom_fields import NDBUrl
from mail_safe_test.resources.contact import ContactModel
from mail_safe_test.resources.doc import DocModel

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

        users = ContactModel.query_by_owner(user)
        # Create links
        for user in users:
            uid = uid()
            link = LinkModel(key=uid, user=user, doc=doc)
            link.put()
