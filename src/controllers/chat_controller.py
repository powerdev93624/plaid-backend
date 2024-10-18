from flask import request, Response, json, Blueprint, stream_with_context
from flask_socketio import SocketIO
from src.models.user_model import User
from src import bcrypt, db
from datetime import datetime, timedelta, timezone
from src.middlewares import authentication_required
import jwt
import os
import uuid
import json
from src.services.chatgpt_service import get_answer_from_chatgpt

chat = Blueprint("chat", __name__)

@chat.route('/add_history', methods = ["POST"])
@authentication_required
def add_history(auth_data):
    
    try:
        data = request.json     
        user_id = auth_data['user_id']
        user_obj = User.query.get(user_id)
        
        if user_obj:
            if user_obj.chathistory:
                current_chat_history = json.loads(user_obj.chathistory)
            else:
                current_chat_history = {"history":[]}
            
            current_chat_history["history"].append({
                "role": "user",
                "content": data["message"]
            })
            user_obj.chathistory = json.dumps(current_chat_history)
            db.session.commit()
            return Response(
                stream_with_context(
                    get_answer_from_chatgpt(user_id, data["message"])
                )
            )
        else:
            return Response(
                response=json.dumps({
                    'status': False, 
                    "message": "User doesn't exist"}),
                status=404,
                mimetype='application/json'
            )
    except Exception as e:
        return Response(
                response=json.dumps({'status': False, 
                                     "message": "Error Occured",
                                     "error": str(e)}),
                status=500,
                mimetype='application/json'
            )
@chat.route('/get_history', methods = ["POST"])
@authentication_required
def get_history(auth_data):
    try:
        user_id = auth_data['user_id']
        user_obj = User.query.get(user_id)
        
        if user_obj:
            if user_obj.chathistory:
                payload = {
                    "chathistory": json.loads(user_obj.chathistory)
                }
                return Response(
                    response=json.dumps({
                        'status': True,
                        "message": "Authenticated User fetched successfully.",
                        "payload": payload 
                    }),
                    status=200,
                    mimetype='application/json'
                )
            else:   
                return Response(
                    response=json.dumps({
                        'status': False,
                        "message": "No chat history"
                    }),
                    status=200,
                    mimetype='application/json'
                )
        else:
            return Response(
                response=json.dumps({
                    'status': False, 
                    "message": "User doesn't exist"}),
                status=404,
                mimetype='application/json'
            )
    except Exception as e:
        return Response(
                response=json.dumps({'status': False, 
                                     "message": "Error Occured",
                                     "error": str(e)}),
                status=500,
                mimetype='application/json'
            )


