import datetime
import config

from flask import request, jsonify, Blueprint
from flask_cors import cross_origin
from flask_jwt_extended import get_jwt, jwt_required, create_access_token
from passlib.hash import pbkdf2_sha256
from sqlalchemy import exc

# from Vend_Dir import app
from Pulsse.database import db
from Pulsse.models.user import User
from Pulsse.utils.user import new_password_check, email_in_db, true_false_check, forget_password_email
from Pulsse.extensions.extensions import blacklist_token

user_blueprint = Blueprint('user', __name__, url_prefix='/user')


@user_blueprint.route('/', methods=['GET'])
@jwt_required()
def read_all_user():
    user_data = []
    users = User.query.all()
    for user in users:
        user_data.append({'id': str(user.id), 'fullname': user.name, 'is_active': user.is_active,
                          'email': user.email, 'password': user.password})

    if not user_data:
        return jsonify(error=False, msg="No data in table", Data=[]), 200

    else:
        return jsonify(error=False, msg="Successfully Displayed", Data=user_data), 200


@user_blueprint.route('/verify', methods=['PATCH', 'OPTIONS'])
@jwt_required()
def verify_user():
    id = request.args.get('id')
    user = User.query.filter_by(id=id).first()
    user.is_active = True

    try:
        db.session.add(user)
        db.session.commit()
    except exc.SQLAlchemyError as err:
        return jsonify(error=True, msg=str(err)), 400

    return jsonify(error=False, msg="Successfully Verified"), 200


@user_blueprint.route('/signup', methods=['POST'])
def signup_user():
    fullname = request.form.get('fullname')
    email = request.form.get('email')
    password = request.form.get('password')

    if email_in_db(email, password) is True:
        return jsonify(error=True, msg="Email already registered"), 400

    else:
        hashed_password = pbkdf2_sha256.hash(password)

        if new_password_check(password) is True:
            user_model = User()
            user_model.name = fullname.lower()
            user_model.email = email.lower()
            user_model.password = hashed_password
            user_model.is_active = False

            try:
                db.session.add(user_model)
                db.session.commit()
            except exc.SQLAlchemyError as err:
                return jsonify(error=True, msg=str(err)), 400

            return jsonify(error=False, msg="Successfully Signed Up"), 200


@user_blueprint.route('/login', methods=['POST'])
def login_user():
    email = request.form.get('email')

    if email_in_db(email, request.form.get('password')) is True:

        access_token = create_access_token(identity=email, expires_delta=False)

        user = User.query.filter_by(email=email.lower()).first()
        if user.is_active:
            return jsonify(error=False, access_token=access_token, user_data={'id': str(user.id),
                                                                              'name': user.name}), 200
        else:
            return jsonify(error=True, msg="User not active"), 400
    else:
        return jsonify(error=True, msg="Email not registered or password incorrect"), 400


@user_blueprint.route('/logout', methods=['DELETE'])
@jwt_required()
def logout_user():
    jti = get_jwt()["jti"]
    blacklist_token(jti)
    return jsonify(error=False, msg="Successfully logged out"), 200

# @user_blueprint.route('/verified', methods=['GET'])
# @jwt_required()
# def read_verified_user():
#     user_data = []
#     page_no = request.args.get('page_no')
#     for user in User.objects(created_at__exists=False):
#         user_data.append({'id': str(user.id), 'fullname': user.fullname, 'is_active': user.is_active,
#                           'email': user.email, 'password': user.password, 'role_data': {'id': str(
#                             user.role_id.id), 'role_name': user.role_id.role_name}})
#
#     if not user_data:
#         return jsonify(error=False, msg="No data in table"), 400
#
#     else:
#         per_page = 10
#         no_of_doc = len(user_data)
#         skip = (int(page_no) - 1) * per_page
#         limit = skip + per_page
#         return jsonify(error=False, msg="Successfully Displayed", Data=user_data[skip:limit], pagination_data={
#             'total_no_of_pages': (int(no_of_doc / per_page) + (no_of_doc % per_page > 0)), 'items_per_page': per_page,
#             'total_items': no_of_doc}), 200


# @user_blueprint.route('/add', methods=['POST'])
# @jwt_required()
# def add_user():
#     fullname = request.form.get('fullname')
#     email = request.form.get('email')
#     password = request.form.get('password')
#     hashed_password = pbkdf2_sha256.hash(password)
#
#     user_model = User()
#     user_model.name = (fullname.strip()).lower()
#     user_model.email = email.lower()
#     user_model.password = hashed_password
#
#     try:
#         db.session.add(user_model)
#         db.session.commit()
#     except exc.SQLAlchemyError as err:
#         return jsonify(error=True, msg=str(err)), 400
#
#     return jsonify(error=False, msg="Successfully Added to the table User"), 200


# @user_blueprint.route('/detail', methods=['GET'])
# @jwt_required()
# def read_user():
#     user_id = request.args.get('user_id')
#
#     for product in User.objects(id=ObjectId(str(user_id))):
#         user_data = {'id': str(product.id), 'fullname': product.fullname,
#                      'email': product.email, 'password': product.password, 'is_active': product.is_active,
#                      'role_data': {'id': str(product.role_id.id), 'role_name': product.role_id.role_name}}
#
#         return jsonify(error=False, data=user_data), 200


# @user_blueprint.route('/update', methods=['PATCH'])
# @jwt_required()
# def update_user():
#     user_id = request.form.get('user_id')
#     password = request.form.get('password')
#     fullname = request.form.get('fullname')
#     role_id = request.form.get('role_id')
#
#     for product in User.objects(id=ObjectId(str(user_id))):
#         product.password = pbkdf2_sha256.hash(password)
#         product.fullname = (fullname.strip()).lower()
#         product.role_id = ObjectId(role_id)
#         product.updated_at = datetime.datetime.now
#
#         try:
#             product.save()
#
#         except mongoengine.errors.NotUniqueError as err:
#
#             if "Tried to save duplicate unique keys" in str(err):
#                 return jsonify(error=True, msg="Email already exist"), 400
#
#             else:
#                 return jsonify(error=True, msg=str(err)), 400
#
#         except mongoengine.errors.ValidationError as err:
#
#             if "Invalid email address" in str(err):
#                 return jsonify(error=True, msg="Invalid email"), 400
#
#             elif "String value did not match validation regex" in str(err):
#                 return jsonify(error=True, msg="Invalid fullname"), 400
#
#             else:
#                 return jsonify(error=True, msg=str(err)), 400
#
#     return jsonify(error=False, msg="Successfully Updated"), 200
#
#
# @user_blueprint.route('/forgot_password', methods=['PATCH'])
# @jwt_required()
# def forgot_user():
#     password = request.form.get('password')
#     email = request.form.get('email')
#
#     if forget_password_email(email) is True:
#
#         for product in User.objects(email=email.lower()):
#             product.password = pbkdf2_sha256.hash(password)
#             product.updated_at = datetime.datetime.now
#             product.save()
#         return jsonify(error=False, msg="Successfully Updated"), 200
#
#     else:
#         return jsonify(error=True, msg="Data against email not available"), 400


# @user_blueprint.route('/suspend', methods=['PATCH'])
# @jwt_required()
# def suspend_user():
#     user_id = ObjectId(request.form.get('user_id'))
#     is_active = request.form.get('is_active')
#
#     for product in User.objects(id=user_id):
#
#         if true_false_check(is_active) is False:
#             product.is_active = True
#             product.save()
#             return jsonify(error=False, msg="Successfully changed status of User"), 200
#
#         elif true_false_check(is_active) is True:
#             product.is_active = True
#             product.save()
#             return jsonify(error=False, msg="Successfully changed status of User"), 200
#
#         else:
#             return jsonify(error=True, msg="Please enter correct status"), 400


# @user_blueprint.route('/delete', methods=['DELETE'])
# @jwt_required()
# def delete_user():
#     user_id = request.args.get('user_id')
#
#     try:
#         us = User.objects(id=user_id)
#         us.delete()
#         return jsonify(error=False, msg="Successfully deleted data from User"), 200
#
#     except mongoengine.errors.OperationError as err:
#
#         if "Could not delete document" in str(err):
#             return jsonify(error=True, msg="User is being used"), 400
#
#         else:
#             return jsonify(error=True, msg=str(err)), 400

