import os
import json
import requests
from openai import OpenAI
from dotenv import load_dotenv

# Configuration and API keys

DEBUG = False

load_dotenv()

ai_api_key=os.environ.get("OPENAI_API_KEY")
weather_api_key = os.environ.get("WEATHER_API_KEY")

# Conditional stdout
def debug_print(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)

# Function to fetch weather data from OpenWeatherMap API
def get_weather(city: str):
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": weather_api_key,
        "units": "metric",
        "lang": "cz"
    }

    r = requests.get(url, params=params)
    data = r.json()

    return {
        "city": data["name"],
        "temp": data["main"]["temp"],
        "feels_like": data["main"]["feels_like"],
        "description": data["weather"][0]["description"],
        "humidity": data["main"]["humidity"],
        "wind": data["wind"]["speed"]
    }

client = OpenAI(api_key=ai_api_key)

# Tool definition for OpenAI - describes the function the model can call
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current real-world weather conditions for a city. "
            "Use this whenever the user asks about weather, temperature, "
            "or conditions in any location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City name, e.g. Prague",
                    }
                },
                "required": ["city"],
            },
        },
    }
]

# Main function: sends message to GPT, handles tool call, returns response
def get_completion_from_messages(messages, model="gpt-4o"):
    # 1. First call - GPT decides whether to call a tool
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=tools,  # Custom tools
        tool_choice="auto",  # Allow AI to decide if a tool should be called
    )

    response_message = response.choices[0].message

    debug_print("First response:", response_message)

    # 2. If GPT wants to call a tool, process it
    if response_message.tool_calls:
        # Extract tool call information
        tool_call = response_message.tool_calls[0]

        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)
        tool_id = tool_call.id

        # Add assistant message with tool call to history
        messages.append(
            {
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": tool_id,
                        "type": "function",
                        "function": {
                            "name": function_name,
                            "arguments": json.dumps(function_args),
                        },
                    }
                ],
            }
        )

        # Call the actual get_weather function with GPT's arguments
        function_response = get_weather(function_args)

        # Add tool result to conversation history
        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_id,
                "name": function_name,
                "content": json.dumps(function_response),
            }
        )

        # 3. Second call - GPT generates final response based on tool data
        second_response = client.chat.completions.create(
            model=model, messages=messages, tools=tools, tool_choice="auto"
        )

        final_answer = second_response.choices[0].message

        debug_print("Second response:", final_answer)

        return final_answer.content

    return "No relevant function call found."

# Execution: system prompt + user query
messages = [
    {
        "role": "developer",
        "content": (
            "You are an assistant that can access real-world weather data "
            "using tools. If the user asks about weather or temperature, "
            "you must call the get_weather tool."
        )
    },
    {
        "role": "user",
        "content": "Jaké je dnes počasí v Ostravě?"
    }
]

# Run the query
responseContent = get_completion_from_messages(messages)

# Print result
print(responseContent)