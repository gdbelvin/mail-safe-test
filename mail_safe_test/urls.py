""" urls.py

URL dispatch, route mappings

"""

from flask.ext import restful
from mail_safe_test import app
from mail_safe_test.resources.oauth import login, oauth_callback, logout, verify
from mail_safe_test.resources.user import UserAPI, AdminUserAPI, AdminUserListAPI
from mail_safe_test.resources.contact import ContactListAPI, ContactAPI
from mail_safe_test.resources.doc import DocListAPI, DocAPI
from mail_safe_test.resources.link import Link

app.add_url_rule('/login/', endpoint='login', view_func = login, methods=['GET'])
app.add_url_rule('/login/oauth2callback/', endpoint='authorized', view_func = oauth_callback, methods=['GET', 'POST'])
app.add_url_rule('/logout/', endpoint='logout', view_func=logout, methods=['GET'])
app.add_url_rule('/verify/', endpoint='verify', view_func=verify, methods=['GET'])

app.api = restful.Api(app)
app.api.add_resource(AdminUserAPI, '/admin/user/<string:key_id>/', endpoint='/admin/user/')
app.api.add_resource(AdminUserListAPI, '/admin/users/', endpoint='/admin/users/')

app.api.add_resource(DocAPI, '/user/doc/<string:key_id>/', endpoint='/user/doc/')
app.api.add_resource(DocListAPI, '/user/docs/', endpoint='/user/docs/')

# Login requied.
app.api.add_resource(UserAPI, '/user/', endpoint='/user/')
app.api.add_resource(ContactAPI, '/user/contact/<string:key_id>/', endpoint='/user/contact/')
app.api.add_resource(ContactListAPI, '/user/contacts/', endpoint='/user/contacts/')

# Login not required.
#app.api.add_resource(Link,     '/link/<int:link_id>/')
