from datetime import date

from Pulsse.database import db
from sqlalchemy.dialects.postgresql import ARRAY
from Pulsse.models.sites import Sites
# from pgvector.sqlalchemy import Vector

class Customers(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=False, nullable=True)
    gender = db.Column(db.String(10), nullable=False)
    image = db.Column(ARRAY(db.Float()), nullable=False)
    created_at = db.Column(db.Date, default=date.today())
    modified_at = db.Column(db.DateTime(), default=date.today())
    