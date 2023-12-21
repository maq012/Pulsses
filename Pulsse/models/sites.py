from datetime import date

from Pulsse.database import db

class Sites(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.Date(), default=date.today())
    modified_at = db.Column(db.Date(), default=date.today())