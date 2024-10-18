from src import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String(50), primary_key = True, unique=True)
    email = db.Column(db.String(70), unique = True)
    password = db.Column(db.String(80))
    chathistory = db.Column(db.String(4294967295))
    plaid_access_key = db.Column(db.String(255))
    plaid_item_id = db.Column(db.String(255))
    plaid_data = db.Column(db.String(4294967295))