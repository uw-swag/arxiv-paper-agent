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

client = OpenAI(
    base_url="https://unlobbying-gauzelike-lyman.ngrok-free.dev/v1",
    api_key="token-abc123", # whatever but needed
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
    model="/home/yinx/yinx/scratch/yinx/custom_models/Qwen3-235B-A22B-Instruct-2507-FP8",
    messages=message,
    tools=[weather_function_schema]
)

print(completion)