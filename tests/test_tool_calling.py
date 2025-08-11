import json
import pytest
import requests
from openai import OpenAI

# Configuration
BRIDGE_URL = "http://localhost:7285"  # Default argo_bridge URL
API_KEY = "dummy"  # argo_bridge doesn't require real API keys

# Define tools for testing
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather in a given city",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city name"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "Temperature unit"
                    }
                },
                "required": ["location"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Perform basic mathematical calculations",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression to evaluate (e.g., '2 + 3 * 4')"
                    }
                },
                "required": ["expression"]
            }
        }
    }
]

@pytest.fixture(scope="module")
def openai_client():
    """Fixture to initialize OpenAI client pointing to argo_bridge."""
    return OpenAI(
        api_key=API_KEY,
        base_url=f"{BRIDGE_URL}/v1"
    )

@pytest.mark.parametrize("test_case", [
    {
        "name": "OpenAI GPT-4o with auto tool choice",
        "model": "gpt-4o",
        "tool_choice": "auto",
        "message": "What's the weather like in Paris?",
        "expected_tool": "get_weather"
    },
    {
        "name": "Claude Sonnet with required tool choice",
        "model": "claudesonnet35v2",
        "tool_choice": "required",
        "message": "Calculate 15 * 23 + 7",
        "expected_tool": "calculate"
    },
    {
        "name": "Gemini with specific tool choice",
        "model": "gemini25flash",
        "tool_choice": {"type": "function", "function": {"name": "get_weather"}},
        "message": "Tell me about the weather in Tokyo",
        "expected_tool": "get_weather"
    }
])
def test_with_requests(test_case, mocker):
    """Test tool calling using raw HTTP requests."""
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "tool_calls": [
                        {
                            "function": {
                                "name": test_case["expected_tool"],
                                "arguments": "{}"
                            }
                        }
                    ]
                },
                "finish_reason": "tool_calls"
            }
        ]
    }
    mocker.patch('requests.post', return_value=mock_response)

    payload = {
        "model": test_case["model"],
        "messages": [
            {"role": "user", "content": test_case["message"]}
        ],
        "tools": TOOLS,
        "tool_choice": test_case["tool_choice"],
        "temperature": 0.1
    }
    
    response = requests.post(
        f"{BRIDGE_URL}/v1/chat/completions",
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    
    assert response.status_code == 200
    result = response.json()
    assert "choices" in result
    choice = result["choices"][0]
    message = choice["message"]
    
    assert message.get("tool_calls") is not None
    tool_call = message["tool_calls"][0]
    assert tool_call["function"]["name"] == test_case["expected_tool"]
    assert choice["finish_reason"] == "tool_calls"

def test_conversation_with_tools(openai_client, mocker):
    """Test a multi-turn conversation with tool calls."""
    # Mock the first call to create
    mock_response1 = mocker.Mock()
    mock_tool_call = mocker.Mock()
    mock_tool_call.function.name = "get_weather"
    mock_tool_call.function.arguments = '{"city": "New York"}'
    mock_tool_call.id = "call_123"
    mock_response1.choices = [mocker.Mock()]
    mock_response1.choices[0].message.tool_calls = [mock_tool_call]
    mock_response1.choices[0].message.content = None

    # Mock the second call to create
    mock_response2 = mocker.Mock()
    mock_response2.choices = [mocker.Mock()]
    mock_response2.choices[0].message.content = "The weather in New York is Sunny, 22°C"

    mocker.patch.object(openai_client.chat.completions, 'create', side_effect=[mock_response1, mock_response2])

    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get weather information for a city",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string", "description": "City name"}
                    },
                    "required": ["city"]
                }
            }
        }
    ]
    
    messages = [
        {"role": "user", "content": "What's the weather like in New York?"}
    ]
    
    # First request
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )
    
    assistant_message = response.choices[0].message
    messages.append({
        "role": "assistant",
        "content": assistant_message.content,
        "tool_calls": [tc.model_dump() for tc in assistant_message.tool_calls] if assistant_message.tool_calls else None
    })
    
    assert assistant_message.tool_calls is not None
    tool_call = assistant_message.tool_calls[0]
    assert tool_call.function.name == "get_weather"
    
    # Simulate tool execution result
    tool_result = f"Weather in {json.loads(tool_call.function.arguments)['city']}: Sunny, 22°C"
    messages.append({
        "role": "tool",
        "tool_call_id": tool_call.id,
        "content": tool_result
    })
    
    # Follow-up request with tool results
    response2 = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )
    
    final_message = response2.choices[0].message
    assert final_message.content is not None
    assert "Sunny" in final_message.content


def test_streaming_with_text_and_tool_call(openai_client, mocker):
    """Test streaming response with both text and a tool call."""
    # Mock the streaming response
    mock_stream = mocker.MagicMock()
    
    # Define the chunks to be returned by the stream
    # Create tool call function mock
    tool_call_function = mocker.Mock()
    tool_call_function.name = "get_weather"
    tool_call_function.arguments = '{"location": "Chicago"}'
    
    chunks = [
        # 1. Role chunk
        mocker.Mock(choices=[mocker.Mock(delta=mocker.Mock(role='assistant', content=None, tool_calls=None))]),
        # 2. Text content chunk
        mocker.Mock(choices=[mocker.Mock(delta=mocker.Mock(content="Of course, I can help with that.", tool_calls=None))]),
        # 3. Tool call chunk
        mocker.Mock(choices=[mocker.Mock(delta=mocker.Mock(content=None, tool_calls=[
            mocker.Mock(
                id="call_456",
                function=tool_call_function
            )
        ]))]),
        # 4. Final empty chunk
        mocker.Mock(choices=[mocker.Mock(delta=mocker.Mock(content=None, tool_calls=None), finish_reason="tool_calls")])
    ]
    
    mock_stream.__iter__.return_value = iter(chunks)
    mocker.patch.object(openai_client.chat.completions, 'create', return_value=mock_stream)

    # Make the streaming request
    stream = openai_client.chat.completions.create(
        model="claudesonnet35v2",
        messages=[{"role": "user", "content": "What is the weather in Chicago?"}],
        tools=TOOLS,
        stream=True,
    )

    # Process the stream and check the order
    received_text = None
    received_tool_call = None
    
    for chunk in stream:
        if chunk.choices[0].delta.content:
            assert received_tool_call is None, "Text chunk received after tool_call chunk"
            received_text = chunk.choices[0].delta.content
        
        if chunk.choices[0].delta.tool_calls:
            assert received_text is not None, "Tool_call chunk received before text chunk"
            received_tool_call = chunk.choices[0].delta.tool_calls[0]

    # Final assertions
    assert received_text == "Of course, I can help with that."
    assert received_tool_call.function.name == "get_weather"
    assert "Chicago" in received_tool_call.function.arguments
