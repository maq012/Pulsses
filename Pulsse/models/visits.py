from datetime import date

from Pulsse.database import db
from Pulsse.models.customers import Customers
from Pulsse.models.sites import Sites


class Visits(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    yolo_id = db.Column(db.Integer(), nullable=False)
    customer_id = db.Column(db.Integer(), db.ForeignKey(Customers.id), nullable=True)
    day = db.Column(db.Date(), nullable=False, default=date.today())
    time_in = db.Column(db.Time())
    time_out = db.Column(db.Time())
    group_val = db.Column(db.Boolean(), nullable=False, default=False)
    created_at = db.Column(db.Date, default=date.today())
    modified_at = db.Column(db.Date(), default=date.today())
    sitekey = db.Column(db.Integer(), db.ForeignKey(Sites.id), nullable=True)
