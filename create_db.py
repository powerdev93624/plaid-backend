from src import app, db, bcrypt
import uuid
import os

app.app_context().push()
db.create_all()