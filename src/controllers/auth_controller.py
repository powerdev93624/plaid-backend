from flask import request, Response, json, Blueprint
from src.models.user_model import User
from src import bcrypt, db
from datetime import datetime, timedelta, timezone
from src.middlewares import authentication_required
import jwt
import os
import uuid


# user controller blueprint to be registered with api blueprint
auth = Blueprint("auth", __name__)

# login api/auth/signin
@auth.route('/signin', methods = ["POST"])
def handle_login():
    try: 
        # first check user parameters
        data = request.json
        if "email" and "password" in data:
            # check db for user records
            user = User.query.filter_by(email = data["email"]).first()

            # if user records exists we will check user password
            if user:
                # check user password
                if bcrypt.check_password_hash(user.password, data["password"]):
                    # user password matched, we will generate token
                    payload = {
                        'iat': datetime.now(timezone.utc),
                        'exp': datetime.now(timezone.utc) + timedelta(days=7),
                        'user_id': user.id,
                        'email': user.email,
                    }
                    token = jwt.encode(payload,os.getenv('SECRET_KEY'),algorithm='HS256')
                    return Response(
                            response=json.dumps({
                                    'status': True,
                                    "message": "User Sign In Successful",
                                    "payload": {
                                        "token": token
                                    }
                                }),
                            status=200,
                            mimetype='application/json'
                        )
                
                else:
                    return Response(
                        response=json.dumps({'status': False, "message": "User Password Mistmatched"}),
                        status=401,
                        mimetype='application/json'
                    ) 
            # if there is no user record
            else:
                return Response(
                    response=json.dumps({'status': False, "message": "User Record doesn't exist, kindly register"}),
                    status=404,
                    mimetype='application/json'
                ) 
        else:
            # if request parameters are not correct 
            return Response(
                response=json.dumps({'status': False, "message": "User Parameters Email and Password are required"}),
                status=400,
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

        
@auth.route('/signup', methods = ["POST"])
def handle_signup():
    
    try: 
        # first validate required use parameters
        
        data = request.json
        print(data)
        if "email" in data and "password" in data:
            # validate if the user exist 
            user = User.query.filter_by(email = data["email"]).first()
            # usecase if the user doesn't exists
            if not user:
                # creating the user instance of User Model to be stored in DB
                user_obj = User(
                    id = uuid.uuid4(),
                    email = data["email"],
                    # hashing the password
                    password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
                )
                db.session.add(user_obj)
                db.session.commit()

                # lets generate jwt token
                payload = {
                    'iat': datetime.now(timezone.utc),
                    'exp': datetime.now(timezone.utc) + timedelta(days=7),
                    'user_id': user_obj.id,
                    'email': user_obj.email,
                }
                token = jwt.encode(payload,os.getenv('SECRET_KEY'),algorithm='HS256')
                return Response(
                    response=json.dumps({
                        'status': True,
                        "message": "User Sign up Successful",
                        "payload": {
                            "token": token
                        }}),
                    status=201,
                    mimetype='application/json'
                )
            else:
                # if user already exists
                return Response(
                response=json.dumps({'status': False, "message": "User already exists kindly use sign in"}),
                status=409,
                mimetype='application/json'
            )
        else:
            # if request parameters are not correct 
            return Response(
                response=json.dumps({'status': False, "message": "User Parameters Firstname, Lastname, Email and Password are required"}),
                status=400,
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
        

@auth.route('/get_plaid_token', methods = ["POST"])
@authentication_required
def get_plaid_token(auth_data):
    try:
        user_id = auth_data['user_id']
        user_obj = User.query.get(user_id)
        if user_obj:
            if user_obj.plaid_access_key and user_obj.plaid_item_id:

                payload = {
                    'plaid_access_key': user_obj.plaid_access_key,
                    'plaid_item_id': user_obj.plaid_item_id,
                }
                plaid_token = jwt.encode(payload,os.getenv('SECRET_KEY'),algorithm='HS256')
                payload = {
                    "plaid_token": plaid_token
                }
                
                return Response(
                    response=json.dumps({
                        'status': True, 
                        "message": "Fetched access key successfully",
                        "payload": payload}),
                    status=200,
                    mimetype='application/json'
                )
            else:
                return Response(
                    response=json.dumps({
                        'status': False, 
                        "message": "User didn't linke bank account yet."}),
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
            response=json.dumps({
                'status': False, 
                "message": "Error Occured",
                "error": str(e)
            }),
            status=500,
            mimetype='application/json'
        )
        

        
