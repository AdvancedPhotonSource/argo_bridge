"""
Tool Calling Module
===================

This module provides a comprehensive toolkit for handling tool calls in Large Language Models (LLMs).
It offers a suite of utilities for converting tool calls, definitions, and choices between different
API formats, including OpenAI, Anthropic, and Google Gemini.

Core functionalities include:
- Universal middleware for seamless conversion of tool-related data structures.
- Robust input and output handling for both native and prompt-based tool calling.
- Pydantic-based type definitions for clear, validated data models.

Key Classes and Functions:
- `ToolCall`: A universal representation of a tool call.
- `Tool`: A universal representation of a tool definition.
- `ToolChoice`: A universal representation of a tool choice strategy.
- `handle_tools`: A function to process and convert incoming tool-related requests.
- `ToolInterceptor`: A class to process and extract tool calls from model responses.

Usage Example:
    from tool_calls import Tool, ToolCall, handle_tools, ToolInterceptor

    # Define a tool
    my_tool = Tool(name="get_weather", description="Fetches weather data.", parameters={...})

    # Process an incoming request
    processed_request = handle_tools(request_data)

    # Intercept and process a model's response
    interceptor = ToolInterceptor()
    tool_calls, text_content = interceptor.process(response_content)
"""

from .handler import Tool, ToolCall, ToolChoice
from .input_handle import handle_tools
from .output_handle import ToolInterceptor
from .types import *

__all__ = [
    "Tool",
    "ToolCall",
    "ToolChoice",
    "handle_tools",
    "ToolInterceptor",
]
