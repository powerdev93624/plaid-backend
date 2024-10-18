from flask import request, Response, json, Blueprint
from src.models.user_model import User
from src import bcrypt, db
from datetime import datetime, timedelta, timezone
from src.middlewares import authentication_required
import jwt
import os
import uuid
from flask import *
import plaid
from plaid import ApiException
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
from plaid.model.transactions_refresh_request import TransactionsRefreshRequest
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from dotenv import load_dotenv
from datetime import date

load_dotenv()

if os.getenv("PLAID_ENV") == "sandbox":
    configuration = plaid.Configuration(
        host=plaid.Environment.Sandbox,
        api_key={
            'clientId': os.getenv("PLAID_CLIENT_ID"),
            'secret': os.getenv("PLAID_SANDBOX_SECRET"),
        }
    )
else:
    configuration = plaid.Configuration(
        host=plaid.Environment.Production,
        api_key={
            'clientId': os.getenv("PLAID_CLIENT_ID"),
            'secret': os.getenv("PLAID_PRODUCTION_SECRET"),
        }
    )

api_client = plaid.ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)

# user controller blueprint to be registered with api blueprint
plaid = Blueprint("plaid", __name__)

# login api/auth/signin
@plaid.route('/create_link_token', methods = ["POST"])
@authentication_required
def create_link_token(auth_data):
    try:  
        user_id = auth_data['user_id']
        user_obj = User.query.get(user_id)
        if user_obj:
            link_token_create_request = LinkTokenCreateRequest(
                products=[Products(product) for product in os.getenv("PLAID_PRODUCTS").split(',')],
                client_name="MoneyBot",
                country_codes=[CountryCode(country) for country in os.getenv("PLAID_COUNTRY_CODES").split(",")],
                language='en',
                webhook=os.getenv("PLAID_WEBHOOK"),
                user=LinkTokenCreateRequestUser(
                    client_user_id=user_id
                )
            )
            try:
                payload = client.link_token_create(link_token_create_request).to_dict()
                return Response(
                    response=json.dumps({
                    'status': True,
                    "message": "Created link-token successfully",
                    "payload": {
                        "response": payload
                    }
                }),
                status=200,
                mimetype='application/json'
                )
            except ApiException as e:
                print(str(e))
            
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
        
@plaid.route('/exchange_public_token', methods = ["POST"])
@authentication_required
def exchange_public_token(auth_data):
    try:
        user_id = auth_data['user_id']
        user_obj = User.query.get(user_id)
        if user_obj:
            data = request.json
            public_token = data['public_token']
            public_token_exchange_request = ItemPublicTokenExchangeRequest(
                public_token=public_token
            )
            response = client.item_public_token_exchange(public_token_exchange_request)
            # These values should be saved to a persistent database and
            # associated with the currently signed-in user
            access_token = response['access_token']
            item_id = response['item_id']
            user_obj.plaid_access_key = access_token
            user_obj.plaid_item_id = item_id
            db.session.commit()
            payload = {
                'plaid_access_key': access_token,
                'plaid_item_id': item_id,
            }
            plaid_token = jwt.encode(payload,os.getenv('SECRET_KEY'),algorithm='HS256')
            payload = {
                "plaid_token": plaid_token
            }
            result_json = {"accounts":[], "transactions":[]}

            accounts_get_request = AccountsGetRequest(access_token=access_token)
            response = client.accounts_get(accounts_get_request)
            accounts = response['accounts']
            for account in accounts:
                result_json["accounts"].append({
                    "name": account["name"],
                    "type": str(account["type"]),
                    "subtype": str(account["subtype"]),
                    "current_balance": account["balances"]["current"],
                    "currency": account["balances"]["iso_currency_code"]
                })
            transactions_get_request = TransactionsGetRequest(
                access_token=access_token,
                start_date=date(2023,1,1),
                end_date=date.today()
            )
            try:
                response = client.transactions_get(transactions_get_request)
                transactions = response['transactions']
            except ApiException as e:
                print(e)
            for transaction in transactions:
                result_json["transactions"].append({
                    "date": str(transaction['date']),
                    "description": str(transaction["merchant_name"]),
                    "amount": transaction["amount"],
                    "category": str(transaction["category"])
                })
            user_obj.plaid_data = result_json
            db.session.commit()
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
        
