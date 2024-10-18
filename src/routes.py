from flask import Blueprint
from src.controllers.auth_controller import auth
from src.controllers.chat_controller import chat
from src.controllers.plaid_controller import plaid

# main blueprint to be registered with application
api = Blueprint('api', __name__)

# register user with api blueprint
api.register_blueprint(auth, url_prefix="/auth")
api.register_blueprint(chat, url_prefix="/chat")
api.register_blueprint(plaid, url_prefix="/plaid")