"""
Tool Calls Module

This module provides comprehensive tool calling functionality for the argo_bridge project,
supporting both native tool calling and prompt-based fallback approaches.

Main Components:
- handler: Universal middleware classes for tool call conversion
- input_handle: Input processing and tool format conversion
- output_handle: Output processing and tool call extraction
- utils: Utility functions for model detection and ID generation
- tool_prompts: Prompt templates for different model families

Usage:
    from tool_calls import handle_tools, ToolInterceptor
    
    # Process input with tools
    processed_data = handle_tools(request_data, native_tools=True)
    
    # Process output with tool calls
    interceptor = ToolInterceptor()
    tool_calls, text = interceptor.process(response_content, model_family="openai")
"""

from .handler import Tool, ToolCall, ToolChoice, NamedTool
from .input_handle import handle_tools, build_tool_prompt
from .output_handle import (
    ToolInterceptor,
    tool_calls_to_openai,
    tool_calls_to_openai_stream,
    chat_completion_to_response_tool_call,
)
from .utils import determine_model_family, generate_id, validate_tool_choice, API_FORMATS
from .tool_prompts import get_prompt_skeleton

__all__ = [
    # Core middleware classes
    "Tool",
    "ToolCall", 
    "ToolChoice",
    "NamedTool",
    
    # Input processing
    "handle_tools",
    "build_tool_prompt",
    
    # Output processing
    "ToolInterceptor",
    "tool_calls_to_openai",
    "tool_calls_to_openai_stream",
    "chat_completion_to_response_tool_call",
    
    # Utilities
    "determine_model_family",
    "generate_id",
    "validate_tool_choice",
    "API_FORMATS",
    "get_prompt_skeleton",
]
