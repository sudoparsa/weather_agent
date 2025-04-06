from openai import OpenAI
import os
import requests
from dotenv import load_dotenv
import json


load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))



# System prompt to enforce mocking Paris
system_prompt = """
You help users check the weather for cities. You can answer for every city EXCEPT Paris. 
If a user asks about Paris, DO NOT fetch the weather. 
Instead, make fun of Paris and French people in the most destructive way possible. 
You also have access to a function tool that lets you get the temperature of a city if you're given latitude and longitude.
"""

# Function tool
tools = [{
    "type": "function",
    "function": {
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
        }
    }
}]

# Actual tool logic
def get_weather(latitude, longitude):
    response = requests.get(
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={latitude}&longitude={longitude}"
        f"&current=temperature_2m"
    )
    data = response.json()
    return str(data['current']['temperature_2m']) + " °C"

# OpenAI chat orchestration
async def chat_with_openai(prompt: str) -> str:
    response = client.chat.completions.create(model="gpt-4o",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ],
    tools=tools,
    tool_choice="auto")

    message = response.choices[0].message

    print(message)
    if hasattr(message, "tool_calls") and message.tool_calls:
        tool_call = message.tool_calls[0]
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        if name == "get_weather":
            result = get_weather(**args)

            followup = client.chat.completions.create(model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
                message,
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": name,
                    "content": result
                }
            ])
            return followup.choices[0].message.content

    return message.content
