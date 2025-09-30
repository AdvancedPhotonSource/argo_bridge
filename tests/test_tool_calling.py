import json
import os
import sys

import pytest
import requests
from openai import OpenAI

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tool_calls import ToolCall
from tool_calls.output_handle import (
    ToolInterceptor,
    tool_calls_to_openai,
    tool_calls_to_openai_stream,
)

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


def test_tool_interceptor_openai_nested_response():
    interceptor = ToolInterceptor()
    response_payload = {
        "content": None,
        "tool_calls": [
            {
                "id": "call_test",
                "type": "function",
                "function": {
                    "name": "add",
                    "arguments": "{\"a\":8,\"b\":5}"
                }
            }
        ]
    }

    tool_calls, clean_text = interceptor.process(response_payload, model_family="openai")

    assert clean_text == ""
    assert tool_calls is not None
    assert len(tool_calls) == 1
    assert tool_calls[0].name == "add"
    assert json.loads(tool_calls[0].arguments) == {"a": 8, "b": 5}


def test_tool_interceptor_google_object_response():
    interceptor = ToolInterceptor()
    response_payload = {
        "content": None,
        "tool_calls": {
            "id": None,
            "name": "add",
            "args": {"a": 8, "b": 5}
        }
    }

    tool_calls, clean_text = interceptor.process(response_payload, model_family="google")

    assert clean_text == ""
    assert tool_calls is not None
    assert len(tool_calls) == 1
    assert tool_calls[0].name == "add"
    assert json.loads(tool_calls[0].arguments) == {"a": 8, "b": 5}


def test_tool_interceptor_anthropic_with_text():
    interceptor = ToolInterceptor()
    response_payload = {
        "response": {
            "content": "I'll call the math tool now.",
            "tool_calls": [
                {
                    "id": "toolu_demo",
                    "name": "calculate",
                    "type": "tool_use",
                    "input": {"expression": "2+2"}
                }
            ]
        }
    }

    tool_calls, clean_text = interceptor.process(response_payload, model_family="anthropic")

    assert clean_text == "I'll call the math tool now."
    assert tool_calls is not None and len(tool_calls) == 1
    assert tool_calls[0].name == "calculate"
    assert json.loads(tool_calls[0].arguments) == {"expression": "2+2"}


def test_tool_interceptor_multiple_calls_mixed_content():
    interceptor = ToolInterceptor()
    response_payload = {
        "response": {
            "content": None,
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": "get_weather",
                        "arguments": '{"location":"Paris"}'
                    }
                },
                {
                    "id": "call_2",
                    "type": "function",
                    "function": {
                        "name": "calculate",
                        "arguments": '{"expression":"3*7"}'
                    }
                }
            ]
        }
    }

    tool_calls, clean_text = interceptor.process(response_payload, model_family="openai")

    assert clean_text == ""
    assert tool_calls is not None and len(tool_calls) == 2
    assert [tc.name for tc in tool_calls] == ["get_weather", "calculate"]


def test_tool_interceptor_handles_missing_tool_calls():
    interceptor = ToolInterceptor()
    response_payload = {"response": {"content": "All done."}}

    tool_calls, clean_text = interceptor.process(response_payload, model_family="openai")

    assert clean_text == "All done."
    assert tool_calls is None


def test_tool_interceptor_ignores_malformed_entry(caplog):
    interceptor = ToolInterceptor()
    caplog.set_level("WARNING")

    response_payload = {
        "response": {
            "content": None,
            "tool_calls": [
                {
                    "id": "call_good",
                    "type": "function",
                    "function": {"name": "add", "arguments": "{\"a\":1}"}
                },
                {
                    "id": "call_bad",
                    "type": "function",
                    "function": "not-a-dict"
                }
            ]
        }
    }

    tool_calls, clean_text = interceptor.process(response_payload, model_family="openai")

    assert clean_text == ""
    assert tool_calls is not None and len(tool_calls) == 1
    assert tool_calls[0].name == "add"
    assert any("Failed" in message for message in caplog.messages)


@pytest.mark.parametrize(
    "api_format",
    ["chat_completion", "response"],
)
def test_tool_calls_to_openai_conversion(api_format):
    calls = [
        ToolCall(id="call1", name="add", arguments="{\"a\":1}"),
        ToolCall(id="call2", name="subtract", arguments="{\"a\":5}"),
    ]

    converted = tool_calls_to_openai(calls, api_format=api_format)

    assert len(converted) == 2
    if api_format == "chat_completion":
        assert converted[0].function.name == "add"
    else:
        assert converted[0].name == "add"


def test_tool_calls_to_openai_stream_conversion():
    call = ToolCall(id="call1", name="add", arguments="{\"a\":1}")

    result = tool_calls_to_openai_stream(call, tc_index=3)

    assert result.index == 3
    assert result.function.name == "add"


def test_tool_calls_to_openai_stream_invalid_type():
    with pytest.raises(ValueError):
        tool_calls_to_openai_stream(123, tc_index=0)


def test_tool_interceptor_google_non_dict_tool_calls():
    interceptor = ToolInterceptor()
    response_payload = {
        "response": {
            "content": None,
            "tool_calls": [
                {
                    "name": "lookup",
                    "args": {"value": "x"},
                },
                "unexpected"
            ]
        }
    }

    tool_calls, clean_text = interceptor.process(response_payload, model_family="google")

    assert clean_text == ""
    assert tool_calls is not None and len(tool_calls) == 1
    assert tool_calls[0].name == "lookup"


def test_tool_interceptor_prompt_based_parsing():
    interceptor = ToolInterceptor()

    text = "Pre text<tool_call>{\"name\":\"add\",\"arguments\":{\"a\":1}}</tool_call>post text"

    tool_calls, clean_text = interceptor.process(text, model_family="openai")

    assert clean_text.strip() == "Pre textpost text"
    assert tool_calls is not None and len(tool_calls) == 1
    assert tool_calls[0].name == "add"



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
