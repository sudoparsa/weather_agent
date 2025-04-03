from openai import OpenAI
import requests
import json
from fastapi import FastAPI


app = FastAPI()



def get_weather(latitude, longitude):
    response = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m,wind_speed_10m&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m")
    data = response.json()
    return data['current']['temperature_2m']


client = OpenAI()

client.api_key = "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"

tools = [{
    "type": "function",
    "name": "get_weather",
    "description": "Get current temperature for provided coordinates in celsius.",
    "parameters": {
        "type": "object",
        "properties": {
            "latitude": {"type": "number"},
            "longitude": {"type": "number"}
        },
        "required": ["latitude", "longitude"],
        "additionalProperties": False
    },
    "strict": True
}]

def start(prompt):
    input_messages = [{"role": "user", "content": prompt}]

    response = client.responses.create(
        model="gpt-4o",
        input=input_messages,
        tools=tools,
    )

    tool_call = response.output[0]
    # print(tool_call)

    if tool_call.type == 'function_call':
        args = json.loads(tool_call.arguments)

        result = get_weather(args["latitude"], args["longitude"])

        print(f"Result: {result}")

        input_messages.append(tool_call)  # append model's function call message
        input_messages.append({                               # append result message
            "type": "function_call_output",
            "call_id": tool_call.call_id,
            "output": str(result)
        })

        response_2 = client.responses.create(
            model="gpt-4o",
            input=input_messages,
            tools=tools,
        )
        print('Final:', response_2.output_text)
        return response_2.output_text

    elif tool_call.type == 'message':
        print(tool_call.content[0].text)

        return tool_call.content[0].text
    
# prompt = "What's the weather like in Paris today?"
# # prompt = "How are you?"
# start(prompt)

@app.get('/')
def home():
    return {"message": "API is running!"}

@app.get("/weather")
def get_results(prompt):
    start(prompt)