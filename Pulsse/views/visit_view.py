import cv2
import numpy as np

from flask import request, jsonify, Blueprint
from flask_jwt_extended import jwt_required
from deepface import DeepFace
from sqlalchemy import exc


from Pulsse.database import db
from Pulsse.models.visits import Visits

visit_blueprint = Blueprint('visit', __name__, url_prefix='/visit')


@visit_blueprint.route('/', methods=['GET'])
@jwt_required()
def get_visit():
    visit_data = []
    visits = Visits.query.all()
    for visit in visits:
        visit_data.append({'id': str(visit.id), 'customer_id': visit.customer_id, 'day': visit.day})
    return jsonify(error=False, msg="Successfully Displayed", data=visit_data)

