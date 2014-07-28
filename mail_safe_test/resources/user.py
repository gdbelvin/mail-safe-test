"""
user.py

"""

from flask import request, Response, abort, make_response
from flask.ext.restful import Resource, fields, marshal_with, reqparse
from google.appengine.ext import ndb
from mail_safe_test.custom_fields import NDBUrl
from mail_safe_test.auth import current_user, user_required, current_user_token_info, admin_required, UserModel

# Public exports
user_fields = {
    'first_name': fields.String,
    'last_name': fields.String,
    'email': fields.String,
    'created': fields.DateTime,
    'last_active': fields.DateTime,
    'uri': NDBUrl('/user/'),
}

admin_user_fields = user_fields.copy()
admin_user_fields['uri'] = NDBUrl('/admin/user/')

parser = reqparse.RequestParser()
parser.add_argument('first_name', type = str, location = 'json')
parser.add_argument('last_name', type = str, location = 'json')
parser.add_argument('email', type = str, location = 'json')

class AdminUserAPI(Resource):
    '''GET, PUT, DELETE on _other_ users'''
    method_decorators = [admin_required]

    @marshal_with(admin_user_fields)
    def get(self, key_id):
        user = ndb.Key(UserModel, key_id).get()
        if not user:
            abort(404)
        return user

    @marshal_with(admin_user_fields)
    def put(self, key_id):
        user = ndb.Key(UserModel, key_id).get()
        if not user:
            abort(404)
        args = parser.parse_args()
        args = {k:v for (k, v) in args.items() if v is not None}  # Remove Nones.
        user.populate(**args)
        user.put()
        return user

    def delete(self, key_id):
        key = ndb.Key(UserModel, key_id)
        if not key.get():
            abort(404)
        key.delete()
        return make_response("", 204)

class AdminUserListAPI(Resource):
    method_decorators = [admin_required]
    user_list_fields = {'users': fields.List(fields.Nested(admin_user_fields))}

    @marshal_with(user_list_fields)
    def get(self):
        users = UserModel.query().fetch()
        return {'users': users}

    @marshal_with(user_list_fields)
    def delete(self):
        ndb.delete_multi(UserModel.query().fetch(keys_only=True))
        users = UserModel.query().fetch()
        return {'users': users}

class UserAPI(Resource):
    def __init__(self):
        self.post_parser = parser.copy()
        self.post_parser.replace_argument('email', type = str, required = True,
                                          location = 'json')
        self.put_parser = parser
        super(UserAPI, self).__init__()

    @marshal_with(user_fields)
    @user_required
    def get(self):
        user = current_user()
        return user

    @marshal_with(user_fields)
    def post(self):
        if current_user():
            abort(409)  # Don't create duplicate users.
        jwt = current_user_token_info()
        if not jwt:
            abort(400)
        args = self.post_parser.parse_args()
        args['id'] = jwt['sub']
        # Not sure what email policy to have. Use the authenticated
        # email, or allow arbitrary emails?
        #args['email'] = jwt['email']
        if args['email'].count('@') != 1:
            abort(400)
        user = UserModel(**args)
        user.put()
        return user

    @marshal_with(user_fields)
    @user_required
    def put(self):
        user = current_user()
        args = self.put_parser.parse_args()
        args = {k:v for (k, v) in args.items() if v is not None}
        user.populate(**args)
        user.put()
        return user

    @user_required
    def delete(self):
        user = current_user()
        if not user:
            abort(400)
        user.key.delete() # Delete a single user.
        return make_response("", 204)
