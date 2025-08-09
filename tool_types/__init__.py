"""
Type definitions for the argo_bridge tool calling functionality.
"""

from .function_call import *

__all__ = [
    # OpenAI types
    "FunctionDefinitionCore",
    "FunctionDefinition", 
    "ChatCompletionToolParam",
    "ChatCompletionNamedToolChoiceParam",
    "ChatCompletionToolChoiceOptionParam",
    "Function",
    "ChatCompletionMessageToolCall",
    "ChoiceDeltaToolCallFunction",
    "ChoiceDeltaToolCall",
    "FunctionTool",
    "ToolChoiceFunctionParam",
    "ToolChoice",
    "ResponseFunctionToolCall",
    
    # Anthropic types
    "InputSchemaTyped",
    "InputSchema",
    "CacheControlEphemeralParam",
    "ToolParam",
    "ToolChoiceShared",
    "ToolChoiceAnyParam",
    "ToolChoiceAutoParam",
    "ToolChoiceNoneParam",
    "ToolChoiceToolParam",
    "ToolChoiceParam",
    "ToolUseBlock",
]
