import os
import json
from src.models.user_model import User
from src import db
from openai import OpenAI
import httpx

def get_answer_from_chatgpt(user_id, user_message):
    user_obj = User.query.get(user_id)
    if user_obj:
        current_chat_history = json.loads(user_obj.chathistory)
        plaid_data = user_obj.plaid_data
        client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            http_client=httpx.Client(
                proxies=os.getenv("OPENAI_PROXIES"),
                transport=httpx.HTTPTransport(local_address="0.0.0.0"),
            ),
        )
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are an AI financial advisor. You review live access to the users financial accounts via Plaid and other data feeds and provide insights and advice into their ongoing transactions, trends and overall financial health. you learn about their goals by asking questions as advisor would ask and provide actionable advice. Switch between the tone, style and teaching of Dave Ramsey, Warren Buffet and Charlie Munger."}    
            ] + current_chat_history["history"][-5:] + [{"role": "user", "content": f"Here's some context about my financial data from Plaid.: {plaid_data}\n\n\n{user_message}"}],
            model="gpt-4o",
            stream=True
        )
        bot_message = ""
        for chunk in completion:
            if chunk.choices[0].delta.content:
                try:
                    yield(chunk.choices[0].delta.content)
                    bot_message += chunk.choices[0].delta.content
                except:
                    yield('')
        current_chat_history["history"].append({
            "role": "assistant",
            "content": bot_message
        })
        user_obj.chathistory = json.dumps(current_chat_history)
        db.session.commit()
    else:
        print("User doesn't exist!")