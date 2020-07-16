# coding: utf-8

import logging
import functools

from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from server import api_return_code
from server.db import db_session
from server.models import UserInfo
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash


logger = logging.getLogger(__name__)

bp = Blueprint("auth", __name__, url_prefix="/v1")


@bp.route("/register", methods=["GET", "POST"])
def register():
    """Register a new user.

    Validates that the username is not already taken. Hashes the
    password for security.
    """
    return_code = {'code': api_return_code.SUCCESS, 'message': 'success', 'content': None}
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        email = request.form['email']

        if not username:
            return_code['code'] = api_return_code.REGISTER_FAILED_NO_PASSWORD
            return_code['message'] = 'Username is required.'
        elif not password:
            return_code['code'] = api_return_code.REGISTER_FAILED_NO_USERNAME
            return_code['message'] = 'Password is required.'
        else:
            if UserInfo.query.filter(UserInfo.name == username).first():
                return_code['code'] = api_return_code.REGISTER_FAILED_USER_ALREADY_REGISTERED
                return_code['message'] = 'User {0} is already registered.'.format(username)
            elif UserInfo.query.filter(UserInfo.email == email).first():
                return_code['code'] = api_return_code.REGISTER_FAILED_EMAIL_ALREADY_USED
                return_code['message'] = 'Email {0} has been used.'.format(email)

        if return_code['code'] == api_return_code.SUCCESS:
            user = UserInfo(name=username, password=generate_password_hash(password), email=email)
            try:
                db_session.add(user)
                db_session.commit()
            except Exception as e:
                return_code['code'] = api_return_code.REGISETR_FAILED_INSERT_USER_INFO_FAILED
                return_code['message'] = 'Db exception.'
                logger.exception('register user[{0}] exception: [{1}].'.format(user, e))
                db_session.rollback()

        return return_code

    else:
        return_code['code'] = api_return_code.REGISTER_FAILED_REQUEST_TYPE_NOT_SUPPORTED
        return_code['message'] = 'Request type not supported.'
        return return_code


