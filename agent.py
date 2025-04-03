from openai import OpenAI
import requests


def get_weather(latitude, longitude):
    response = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m,wind_speed_10m&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m")
    data = response.json()
    return data['current']['temperature_2m']

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
    },
    "strict": True
    }
}]


system_prompt = """
You help users find recent soccer match results. You can answer about every team EXCEPT Liverpool. If a user asks about Liverpool, DO NOT fetch the recent matches. Instead, make fun of Liverpool and its fans in the 
"""

system_prompt = """
You help users check the weather for cities. You can answer for every city EXCEPT Paris. If a user asks about Paris, DO NOT fetch the weather. Instead, make fun of Paris and French people in general in the most destructive way.
"""

client = OpenAI()

assistant = client.beta.assistants.create(
    name="Hala Madrid",
    instructions=system_prompt,
    model="gpt-4o",
    tools=tools
)

    
from typing_extensions import override
from openai import AssistantEventHandler
    
class EventHandler(AssistantEventHandler):
    @override
    def on_event(self, event):
        # Retrieve events that are denoted with 'requires_action'
        # since these will have our tool_calls
        if event.event == 'thread.run.requires_action':
            run_id = event.data.id  # Retrieve the run ID from the event data
            self.handle_requires_action(event.data, run_id)

    # @override
    # def on_text_created(self, text) -> None:
    #     print(f"\nassistant > ", end="", flush=True)
        
    # @override
    # def on_text_delta(self, delta, snapshot):
    #     print(delta.value, end="", flush=True)
        
    def on_tool_call_created(self, tool_call):
        print(f"\nassistant > {tool_call.type}\n", flush=True)


    def handle_requires_action(self, data, run_id):
        tool_outputs = []
        

        for tool in data.required_action.submit_tool_outputs.tool_calls:
            if tool.function.name == "get_weather":
                tool_outputs.append({"tool_call_id": tool.id, "output": "57"})
            
        # Submit all tool_outputs at the same time
        self.submit_tool_outputs(tool_outputs, run_id)

    def submit_tool_outputs(self, tool_outputs, run_id):
        # Use the submit_tool_outputs_stream helper
        with client.beta.threads.runs.submit_tool_outputs_stream(
            thread_id=self.current_run.thread_id,
            run_id=self.current_run.id,
            tool_outputs=tool_outputs,
            event_handler=EventHandler(),
        ) as stream:
            for text in stream.text_deltas:
                print(text, end="", flush=True)
                print()


user_prompt = "What's the weather like in Tokyo today?"
# user_prompt = "What's the weather like in Paris today?"
thread = client.beta.threads.create()
message = client.beta.threads.messages.create(
thread_id=thread.id,
role="user",
content=user_prompt,
)
    

with client.beta.threads.runs.stream(
thread_id=thread.id,
assistant_id=assistant.id,
event_handler=EventHandler()
) as stream:
    stream.until_done()
    





