import os
import logging
from flask import Flask, request
import openai
import json
from functions import (
  get_functions,
  use_database,
  run_code
)
from tenacity import retry, wait_random_exponential, stop_after_attempt
from dotenv import load_dotenv
load_dotenv()

openai.api_key = os.environ.get("OPENAI_API_KEY")

app = Flask(__name__)

CHAT_MODEL="gpt-4"

@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6))
def ask_gpt(messages):
    print("Asking GPT", messages)
    return openai.ChatCompletion.create(
        model=CHAT_MODEL,
        messages=[{
                "role": "system",
                "content": f"You are a sophisticated AI assistant that acts as an API endpoint. Your task is to handle the inbound request, decide what to do about it, and then return a valid JSON response. You only return valid JSON responses, even when you need to ask the user a follow up question."
            },
            *messages,
        ],
        temperature=0,
        functions=get_functions(),
    )

def get_completion(messages) -> dict:
    response = ask_gpt(messages)
    response_message = response.choices[0].get('message')

    if 'function_call' in response_message:
        function_call = response.choices[0]['message']['function_call']
        print(f"Function call: {function_call}")
        if function_call["name"] == "use_database":
            query = json.loads(function_call["arguments"])["query"]
            results = use_database(query)
            messages.append(response_message)
            messages.append({
                "role": "function",
                "name": "use_database",
                "content": json.dumps(results)
            })
            print("Got results, calling get_completion again", results)
            return get_completion(messages)
        if function_call["name"] == "run_code":
            code = json.loads(function_call["arguments"])["code"]
            results = run_code(code)
            messages.append(response_message)
            messages.append({
                "role": "function",
                "name": "run_code",
                "content": json.dumps(results)
            })
            print("Got results, calling get_completion again", results)
            return get_completion(messages)
    else:
        if not response_message:
            logging.error("Unable to process")
            return {
                "error": "Unable to process"
            }
        
        print("No function call, returning response message")
        return response_message

@app.post('/')
def new_request():
    request_json = request.get_json(silent=True)
    try:
        new_message = {
            "role": "user",
            "content": json.dumps(request_json)
        }
        print("New request", request_json)
        completion = get_completion([new_message])
        print("Completion complete, responding", completion)
        return (completion, 200)
    except Exception as e:
        error_message = e.args[0]
        logging.error(error_message)
        return ({
            "error": error_message
        }, 422)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 3000)))