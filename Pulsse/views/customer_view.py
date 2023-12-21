import cv2
import numpy as np

from flask import request, jsonify, Blueprint
from flask_jwt_extended import jwt_required
from deepface import DeepFace
from sqlalchemy import exc
from flask_jwt_extended import jwt_required


from Pulsse.database import db
from Pulsse.models.customers import Customers

customer_blueprint = Blueprint('customer', __name__, url_prefix='/customer')


@customer_blueprint.route('/add', methods=['POST'])
@jwt_required()
def add_customer():
    name = request.form.get('name')
    gender = request.form.get('gender')
    image = request.files.get('image')
    file_bytes = np.fromfile(image, np.uint8)
    file = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    try:
        image_embedding = DeepFace.represent(file, model_name="Facenet")
    except:
        return jsonify(error=True, msg="Face Not Detected"), 400

    customer = Customers()
    customer.name = (name.strip()).lower()
    customer.gender = gender.lower()
    customer.image = image_embedding[0]['embedding']

    try:
        db.session.add(customer)
        db.session.commit()
    except exc.SQLAlchemyError as err:
        return jsonify(error=True, msg=str(err)), 400

    return jsonify(error=False, msg="Customer Successfully Added"), 200


@customer_blueprint.route('/', methods=['GET'])
@jwt_required()
def get_customer():
    customer_data = []
    customers = Customers.query.all()
    for customer in customers:
        customer_data.append({'id': str(customer.id), 'fullname': customer.name, 'gender': customer.gender})
    return jsonify(error=False, msg="Successfully Displayed", data=customer_data)

