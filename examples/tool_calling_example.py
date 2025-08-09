#!/usr/bin/env python3
"""
Tool Calling Example for Argo Bridge

This example demonstrates how to use tool calling functionality with the argo_bridge server.
It shows both native tool calling and prompt-based fallback approaches.

Requirements:
- argo_bridge server running (python argo_bridge.py)
- OpenAI Python client library (pip install openai)

Usage:
    python examples/tool_calling_example.py
"""

import json
import requests
from openai import OpenAI

# Configuration
BRIDGE_URL = "http://localhost:7285"  # Default argo_bridge URL
API_KEY = "dummy"  # argo_bridge doesn't require real API keys

def test_with_requests():
    """Test tool calling using raw HTTP requests"""
    print("=" * 60)
    print("Testing Tool Calling with Raw HTTP Requests")
    print("=" * 60)
    
    # Define tools
    tools = [
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
    
    # Test different models and tool choice options
    test_cases = [
        {
            "name": "OpenAI GPT-4o with auto tool choice",
            "model": "gpt-4o",
            "tool_choice": "auto",
            "message": "What's the weather like in Paris?"
        },
        {
            "name": "Claude Sonnet with required tool choice",
            "model": "claudesonnet35v2",
            "tool_choice": "required",
            "message": "Calculate 15 * 23 + 7"
        },
        {
            "name": "Gemini with specific tool choice",
            "model": "gemini25flash",
            "tool_choice": {"type": "function", "function": {"name": "get_weather"}},
            "message": "Tell me about the weather in Tokyo"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n--- {test_case['name']} ---")
        
        payload = {
            "model": test_case["model"],
            "messages": [
                {"role": "user", "content": test_case["message"]}
            ],
            "tools": tools,
            "tool_choice": test_case["tool_choice"],
            "temperature": 0.1
        }
        
        try:
            response = requests.post(
                f"{BRIDGE_URL}/v1/chat/completions",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                choice = result["choices"][0]
                message = choice["message"]
                
                print(f"Content: {message.get('content', 'No content')}")
                
                if message.get("tool_calls"):
                    print("Tool calls:")
                    for tool_call in message["tool_calls"]:
                        print(f"  - {tool_call['function']['name']}: {tool_call['function']['arguments']}")
                        
                print(f"Finish reason: {choice['finish_reason']}")
            else:
                print(f"Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"Request failed: {e}")


def test_with_openai_client():
    """Test tool calling using OpenAI Python client"""
    print("\n" + "=" * 60)
    print("Testing Tool Calling with OpenAI Python Client")
    print("=" * 60)
    
    # Initialize OpenAI client pointing to argo_bridge
    client = OpenAI(
        api_key=API_KEY,
        base_url=f"{BRIDGE_URL}/v1"
    )
    
    # Define tools
    tools = [
        {
            "type": "function",
            "function": {
                "name": "search_web",
                "description": "Search the web for information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        },
                        "num_results": {
                            "type": "integer",
                            "description": "Number of results to return",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    ]
    
    test_cases = [
        {
            "name": "GPT-4o with streaming",
            "model": "gpt-4o",
            "stream": True,
            "message": "Search for recent news about artificial intelligence"
        },
        {
            "name": "Claude without streaming",
            "model": "claudesonnet35v2", 
            "stream": False,
            "message": "Find information about quantum computing breakthroughs"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n--- {test_case['name']} ---")
        
        try:
            response = client.chat.completions.create(
                model=test_case["model"],
                messages=[
                    {"role": "user", "content": test_case["message"]}
                ],
                tools=tools,
                tool_choice="auto",
                stream=test_case["stream"],
                temperature=0.1
            )
            
            if test_case["stream"]:
                print("Streaming response:")
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        print(chunk.choices[0].delta.content, end="", flush=True)
                    elif chunk.choices[0].delta.tool_calls:
                        print(f"\nTool call: {chunk.choices[0].delta.tool_calls}")
                print()  # New line after streaming
            else:
                message = response.choices[0].message
                print(f"Content: {message.content}")
                
                if message.tool_calls:
                    print("Tool calls:")
                    for tool_call in message.tool_calls:
                        print(f"  - {tool_call.function.name}: {tool_call.function.arguments}")
                        
                print(f"Finish reason: {response.choices[0].finish_reason}")
                
        except Exception as e:
            print(f"Request failed: {e}")


def test_prompt_based_fallback():
    """Test prompt-based tool calling fallback"""
    print("\n" + "=" * 60)
    print("Testing Prompt-Based Tool Calling Fallback")
    print("=" * 60)
    
    # This test demonstrates what happens when native tool calling fails
    # and the system falls back to prompt-based tool calling
    
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_time",
                "description": "Get the current time in a specific timezone",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "timezone": {
                            "type": "string",
                            "description": "Timezone (e.g., 'UTC', 'EST', 'PST')"
                        }
                    },
                    "required": ["timezone"]
                }
            }
        }
    ]
    
    # Test with a model that might not support native tools
    payload = {
        "model": "gpt-4o",  # This should work with native tools
        "messages": [
            {"role": "user", "content": "What time is it in UTC?"}
        ],
        "tools": tools,
        "tool_choice": "auto",
        "temperature": 0.1
    }
    
    try:
        response = requests.post(
            f"{BRIDGE_URL}/v1/chat/completions",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            choice = result["choices"][0]
            message = choice["message"]
            
            print(f"Response: {message.get('content', 'No content')}")
            
            if message.get("tool_calls"):
                print("Native tool calls detected:")
                for tool_call in message["tool_calls"]:
                    print(f"  - {tool_call['function']['name']}: {tool_call['function']['arguments']}")
            else:
                print("No tool calls detected - likely using prompt-based approach")
                
        else:
            print(f"Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Request failed: {e}")


def test_conversation_with_tools():
    """Test a multi-turn conversation with tool calls"""
    print("\n" + "=" * 60)
    print("Testing Multi-Turn Conversation with Tools")
    print("=" * 60)
    
    client = OpenAI(
        api_key=API_KEY,
        base_url=f"{BRIDGE_URL}/v1"
    )
    
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
    
    # Simulate a conversation
    messages = [
        {"role": "user", "content": "What's the weather like in New York?"}
    ]
    
    try:
        # First request
        response = client.chat.completions.create(
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
        
        print("Assistant:", assistant_message.content)
        
        if assistant_message.tool_calls:
            print("Tool calls made:")
            for tool_call in assistant_message.tool_calls:
                print(f"  - {tool_call.function.name}({tool_call.function.arguments})")
                
                # Simulate tool execution result
                tool_result = f"Weather in {json.loads(tool_call.function.arguments)['city']}: Sunny, 22°C"
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result
                })
            
            # Follow-up request with tool results
            response2 = client.chat.completions.create(
                model="gpt-4o",
                messages=messages
            )
            
            print("Assistant (after tool execution):", response2.choices[0].message.content)
            
    except Exception as e:
        print(f"Conversation test failed: {e}")


def main():
    """Run all tool calling tests"""
    print("Argo Bridge Tool Calling Test Suite")
    print("=" * 60)
    print(f"Testing against: {BRIDGE_URL}")
    print("Make sure argo_bridge server is running!")
    
    # Test server connectivity
    try:
        response = requests.get(f"{BRIDGE_URL}/v1/models", timeout=5)
        if response.status_code == 200:
            print("✓ Server is reachable")
        else:
            print(f"✗ Server returned {response.status_code}")
            return
    except Exception as e:
        print(f"✗ Cannot reach server: {e}")
        return
    
    # Run tests
    test_with_requests()
    test_with_openai_client()
    test_prompt_based_fallback()
    test_conversation_with_tools()
    
    print("\n" + "=" * 60)
    print("Tool calling tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
