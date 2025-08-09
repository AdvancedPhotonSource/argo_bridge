# Tool Calling Implementation for Argo Bridge

This document describes the comprehensive tool calling functionality implemented in the argo_bridge project, based on the argo-proxy architecture.

## Overview

The tool calling implementation provides:

1. **Native Tool Calling**: Direct API format conversion between providers (OpenAI, Anthropic, Google)
2. **Prompt-Based Fallback**: For models without native tool support, using system prompts
3. **Universal Middleware**: Classes that can convert between different API formats
4. **Type Safety**: Pydantic models for validation and type checking
5. **Streaming Support**: Both streaming and non-streaming tool calls

## Architecture

### Core Components

```
tool_calls/
├── __init__.py          # Module exports
├── handler.py           # Universal middleware classes
├── input_handle.py      # Input processing and conversion
├── output_handle.py     # Output processing and extraction
├── utils.py            # Utility functions
└── tool_prompts.py     # Prompt templates

types/
└── function_call.py    # Type definitions for all providers
```

### Key Classes

#### Middleware Classes (`tool_calls/handler.py`)

- **`ToolCall`**: Universal representation of tool call data
- **`Tool`**: Universal representation of tool definition data  
- **`ToolChoice`**: Universal representation of tool choice strategy
- **`NamedTool`**: Simple representation of named tools

#### Processing Classes (`tool_calls/input_handle.py`, `tool_calls/output_handle.py`)

- **`handle_tools()`**: Main entry point for input processing
- **`ToolInterceptor`**: Processes responses and extracts tool calls
- **`tool_calls_to_openai()`**: Converts tool calls to OpenAI format

## Usage

### Basic Tool Calling

```python
from tool_calls import handle_tools, ToolInterceptor

# Process input request
processed_data = handle_tools(request_data, native_tools=True)

# Process output response
interceptor = ToolInterceptor()
tool_calls, text = interceptor.process(response_content, model_family="openai")
```

### With argo_bridge Server

The tool calling functionality is automatically integrated into the argo_bridge server. Simply include `tools` and `tool_choice` in your requests:

```python
import requests

response = requests.post("http://localhost:7285/v1/chat/completions", json={
    "model": "gpt-4o",
    "messages": [{"role": "user", "content": "What's the weather in Paris?"}],
    "tools": [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get weather for a city",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string", "description": "City name"}
                    },
                    "required": ["city"]
                }
            }
        }
    ],
    "tool_choice": "auto"
})
```

### With OpenAI Client

```python
from openai import OpenAI

client = OpenAI(
    api_key="dummy",
    base_url="http://localhost:7285/v1"
)

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Calculate 15 * 23"}],
    tools=[
        {
            "type": "function",
            "function": {
                "name": "calculate",
                "description": "Perform calculations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {"type": "string"}
                    },
                    "required": ["expression"]
                }
            }
        }
    ],
    tool_choice="auto"
)
```

## Model Support

### Native Tool Calling Support

- **OpenAI Models**: Full native support (gpt-4o, gpt-4, gpt-3.5-turbo, etc.)
- **Anthropic Models**: Full native support (claude-sonnet-3.5, claude-opus-4, etc.)
- **Google Models**: Partial support (gemini-2.5-pro, gemini-2.5-flash)

### Prompt-Based Fallback

For models without native tool support, the system automatically falls back to prompt-based tool calling using model-specific prompt templates.

## API Formats

### OpenAI Format (Input)

```json
{
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "function_name",
        "description": "Function description",
        "parameters": {
          "type": "object",
          "properties": {
            "param": {"type": "string"}
          },
          "required": ["param"]
        }
      }
    }
  ],
  "tool_choice": "auto"
}
```

### OpenAI Format (Output)

```json
{
  "choices": [{
    "message": {
      "role": "assistant",
      "content": "I'll help you with that.",
      "tool_calls": [
        {
          "id": "call_abc123",
          "type": "function",
          "function": {
            "name": "function_name",
            "arguments": "{\"param\": \"value\"}"
          }
        }
      ]
    },
    "finish_reason": "tool_calls"
  }]
}
```

### Anthropic Format (Converted Internally)

```json
{
  "tools": [
    {
      "name": "function_name",
      "description": "Function description",
      "input_schema": {
        "type": "object",
        "properties": {
          "param": {"type": "string"}
        },
        "required": ["param"]
      }
    }
  ],
  "tool_choice": {"type": "auto"}
}
```

## Configuration

### Native vs Prompt-Based

The system automatically determines whether to use native or prompt-based tool calling based on the model family:

```python
# Automatic detection
model_family = determine_model_family(model_name)
use_native = model_family in ["openai", "anthropic"]

# Manual override
processed_data = handle_tools(data, native_tools=False)  # Force prompt-based
```

### Tool Choice Options

- **`"auto"`**: Model decides whether to use tools
- **`"none"`**: Don't use tools
- **`"required"`**: Must use at least one tool
- **`{"type": "function", "function": {"name": "tool_name"}}`**: Use specific tool

## Streaming Support

### Non-Streaming

Tool calls are returned in the final response with `finish_reason: "tool_calls"`.

### Streaming

Tool calls are sent as delta chunks during streaming:

```json
{
  "choices": [{
    "delta": {
      "tool_calls": [
        {
          "index": 0,
          "id": "call_abc123",
          "function": {
            "name": "function_name",
            "arguments": "{\"param\": \"value\"}"
          }
        }
      ]
    },
    "finish_reason": null
  }]
}
```

## Error Handling

### Validation Errors

If tool definitions are invalid, the system returns a 400 error:

```json
{
  "error": {
    "message": "Tool validation/conversion failed: Invalid tool schema"
  }
}
```

### Fallback Behavior

If native tool calling fails, the system automatically falls back to prompt-based tool calling:

```
Native tool handling failed, falling back to prompt-based: Google API format is not supported yet.
```

## Examples

### Complete Example

See `examples/tool_calling_example.py` for comprehensive examples including:

- Raw HTTP requests with different models
- OpenAI client usage with streaming
- Multi-turn conversations with tool calls
- Error handling and fallback scenarios

### Running the Example

```bash
# Start the argo_bridge server
python argo_bridge.py --port 7285

# Run the tool calling examples
python examples/tool_calling_example.py
```

## Implementation Details

### Input Processing Flow

1. **Request arrives** with `tools` and `tool_choice`
2. **Model family detection** determines processing strategy
3. **Native tool handling** attempts format conversion
4. **Fallback to prompt-based** if native handling fails
5. **Request forwarded** to upstream API

### Output Processing Flow

1. **Response received** from upstream API
2. **Tool interceptor** processes response content
3. **Tool calls extracted** using regex (prompt-based) or direct parsing (native)
4. **Format conversion** to OpenAI-compatible format
5. **Response returned** to client

### Type Safety

All tool calling operations use Pydantic models for validation:

```python
from types.function_call import ChatCompletionToolParam

# Automatic validation
tool = ChatCompletionToolParam.model_validate(tool_dict)
```

## Debugging

### Logging

Enable debug logging to see tool processing details:

```bash
python argo_bridge.py --dlog
```

### Debug Output

```
[Input Handle] OpenAI model detected, converted tools
[Input Handle] Converted tools: [{'type': 'function', 'function': {...}}]
[Output Handle] Using [OpenAI] native tool calling format
[Output Handle] Converted ToolCall objects: [ToolCall(id=call_abc123, ...)]
```

## Future Enhancements

1. **Real Streaming Tool Support**: Currently uses fake streaming for tool calls
2. **Google Gemini Native Support**: Complete implementation of Google tool calling
3. **Parallel Tool Calls**: Support for multiple simultaneous tool calls
4. **Tool Result Processing**: Automatic handling of tool execution results
5. **Custom Tool Registries**: Integration with external tool management systems

## Contributing

When adding new model support:

1. Add model detection logic to `determine_model_family()`
2. Implement format conversion in middleware classes
3. Add prompt templates for prompt-based fallback
4. Update type definitions if needed
5. Add test cases to the example script

## Troubleshooting

### Common Issues

1. **"Tool validation/conversion failed"**: Check tool schema format
2. **"Google API format is not supported yet"**: Use prompt-based fallback
3. **No tool calls detected**: Model may not support native tools, using prompts
4. **Streaming not working with tools**: Currently uses fake streaming

### Solutions

1. Validate tool schemas against OpenAI specification
2. Set `native_tools=False` for unsupported models
3. Check model family detection logic
4. Use non-streaming for real-time tool calls
