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

base_url = "https://openrouter.ai/api/v1"
api_key = "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"

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
    model="nvidia/nemotron-3-nano-30b-a3b:free",
    messages=message,
    tools=[weather_function_schema],
    extra_body={
        "reasoning": {
            "enabled": True
        }
    }
)

print(completion)