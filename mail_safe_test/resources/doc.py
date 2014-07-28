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
    'content': ndb.BlobProperty,
    'date': fields.DateTime,
    'status': ndb.IntegerProperty,
    'uri': NDBUrl('/user/doc/')
}

parser = reqparse.RequestParser()
parser.add_argument('content', type = str, location = 'json')
parser.add_argument('status', type = int, location = 'json')

class DocModel(ndb.Model):
    content = ndb.BlobProperty()
    date = ndb.DateTimeProperty(auto_now_add=True)
    status = ndb.StringProperty()

    @classmethod
    def query_by_id(cls, user, doc_id):
        doc_key = ndb.Key(UserModel, user, DocModel, doc_id)
        return doc_key.get()

    # @classmethod
    # def query_by_owner(cls, user):

class DocList(Resource):
    method_decorators = [user_required]
    doc_list_fields = {'docs': fields.List(fields.Nested(doc_fields))}

    @marshal_with(doc_list_fields)
    def get(self):
        user=current_user()
        docs = DocModel.query(ancestor=user.key).fetch()
        return {'docs': docs}

    @marshal_with(doc_list_fields)
    def delete(self):
        user=current_user()
        ndb.delete_multi(DocModel.query(ancestor=user.key).fetch())
        docs = DocModel.query().fetch()
        return {'docs': docs}

class Doc(Resource):
    method_decorators = [user_required]

    # Sydney check this, don't think is right
    def __init__(self):
        self.post_parser = parser.copy()
        self.post_parser.replace_argument(user, type = str, required = True, location = 'json')
        self.put_parser = parser.copy()
        super(DocAPI, self).__init__()

    @marshal_with(doc_fields)
    def get(self, doc_id):
        user=current_user()
        doc = DocModel.query_by_id(user, doc_id)
        if doc is None: 
            abort(404)
        return doc

    def delete(self, doc_id):
        user=current_user()
        doc = DocModel.query_by_id(user, doc_id)
        if doc is None:
            abort(404)
        doc.key.delete()
        return make_response("", 204)

    @marshal_with(doc_fields)
    def put(self, doc_id):
        user=current_user()
        doc = DocModel.query_by_id(user, doc_id)
        if doc is None:
            abort(404)
        args = parser.parse_args()
        doc.populate(**args)
        doc.put()
        return doc

    @marshal_with(doc_fields)
    def post(self):
        user = current_user()
        args = self.post_parser.parse_args()
        doc = DocModel(ancestor=user.key, **args)
        doc.put()
        return doc
