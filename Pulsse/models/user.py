from datetime import date

from Pulsse.database import db


class User(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=False, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    is_active = db.Column(db.Boolean(), nullable=False, default=False)
    created_at = db.Column(db.Date(), default=date.today())
    modified_at = db.Column(db.Date(), default=date.today())
