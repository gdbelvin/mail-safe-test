"""
link.py

"""

from flask import request, Response, abort, make_response
from flask.ext.restful import Resource, fields, marshal_with, reqparse
from google.appengine.ext import ndb, blobstore
from mail_safe_test.custom_fields import NDBUrl
from mail_safe_test.auth import current_user, user_required, admin_required, UserModel

class LinkModel(ndb.Model):
    contact = ndb.KeyProperty(kind='ContactModel')
    doc = ndb.KeyProperty(kind='DocModel')
    clicked = ndb.BooleanProperty()
    expires = ndb.DateTimeProperty()
    otp = ndb.StringProperty()
    otp_expire = ndb.DateTimeProperty()

class Link(Resource):
    def get(self):
        return "hi"
