from openai import OpenAI

# Define a function that our model can use.
def get_current_weather(location: str, unit: str = "celsius"):
    """
    Gets the current weather in a given location.

    Args:
        location: The city and state, e.g. "San Francisco, CA" or "Tokyo, JP"
        unit: The unit to return the temperature in. (choices: ["celsius", "fahrenheit"])

    Returns:
        temperature: The current temperature in the given location
        weather: The current weather in the given location
    """
    return {"temperature": 15, "weather": "sunny"}

base_url = "https://unermined-bridgette-transempirical.ngrok-free.dev/v1"
api_key = "sk"

client = OpenAI(
    base_url=base_url,
    api_key=api_key,
)

weather_function_schema = {
    "type": "function",
    "function": {
        "name": "get_current_temperature",
        "description": "Gets the current temperature for a given location.",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city name, e.g. San Francisco",
                },
            },
            "required": ["location"],
        },
    }
}


message = [
    {
        "role": "developer",
        "content": "You are a model that can do function calling with the following functions"
    },
    {
        "role": "user", 
        "content": "What's the temperature in London?"
    }
]

completion = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=message,
    tools=[weather_function_schema],
    extra_body={
        "reasoning": {
            "enabled": True
        }
    }
)

print(completion)