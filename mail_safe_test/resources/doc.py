"""
doc.py

"""

from flask import request, Response, abort, make_response
from flask.ext.restful import Resource, fields, marshal_with, reqparse
from google.appengine.ext import ndb, blobstore
from mail_safe_test.custom_fields import NDBUrl
from mail_safe_test.auth import current_user, user_required, admin_required, UserModel

#   public exports
doc_fields = {
    'title': fields.String,
    'content': fields.String,
    'date': fields.DateTime,
    # TODO - Should status be an integer or string?
    'status': fields.Integer,
    'uri': NDBUrl('/user/doc/')
}
def parser(required_status):
    parser = reqparse.RequestParser()
    parser.add_argument('title', type = str, location = 'json')
    parser.add_argument('content', type = str, location = 'json')
    parser.add_argument('status', type = int, required = required_status, location = 'json')
    return parser

class DocModel(ndb.Model):
    title = ndb.StringProperty()
    content = ndb.StringProperty()
    date = ndb.DateTimeProperty(auto_now_add=True)
    status = ndb.IntegerProperty()

    @classmethod
    def query_by_id(cls, user_id, doc_id):
        doc_key = ndb.Key(UserModel, user_id, DocModel, doc_id)
        return doc_key.get()

    @classmethod
    def query_by_owner(cls, user):
        return DocModel.query(ancestor=user.key).fetch()

class DocListAPI(Resource):
    method_decorators = [user_required]
    doc_list_fields = {'docs': fields.List(fields.Nested(doc_fields))}

    def __init__(self):
        # TODO - Should we require a status from the front-end or default it to "Draft" if one is not provided?
        self.post_parser = parser(False)
        super(DocListAPI, self).__init__()
        
    @marshal_with(doc_list_fields)
    def get(self):
        user = current_user()
        docs = DocModel.query_by_owner(user)
        return {'docs': docs}

    @marshal_with(doc_fields)
    def post(self):
        user = current_user()
        args = self.post_parser.parse_args()
        doc = DocModel(parent=ndb.Key(UserModel, user.key.id()), **args)
        doc.put()
        return doc

    @marshal_with(doc_list_fields)
    def delete(self):
        user = current_user()
        ndb.delete_multi(DocModel.query(ancestor=user.key).fetch(keys_only=True))
        docs = DocModel.query_by_owner(user)
        return {'docs': docs}

class DocAPI(Resource):
    method_decorators = [user_required]

    def __init__(self):
        self.put_parser = parser(False)
        super(DocAPI, self).__init__()

    @marshal_with(doc_fields)
    def get(self, key_id):
        user = current_user()
        doc = DocModel.query_by_id(user.key.id(), key_id)
        if doc is None:
            abort(404)
        return doc
    
    @marshal_with(doc_fields)
    def put(self, key_id):
        user = current_user()
        doc = DocModel.query_by_id(user.key.id(), key_id)
        if doc is None:
            abort(404)
        args = self.put_parser.parse_args()
        args = {k:v for (k, v) in args.items() if v is not None}  # Remove empty arguments
        doc.populate(**args)
        doc.put()
        return doc

    def delete(self, key_id):
        user = current_user()
        doc = DocModel.query_by_id(user.key.id(), key_id)
        if doc is None:
            abort(404)
        doc.key.delete()
        return make_response("", 204)