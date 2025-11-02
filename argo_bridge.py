import os
import datetime
import requests
from flask import Flask, request, jsonify, Response
import time
import json
import logging
import argparse
from flask_cors import CORS  # Add this import
import httpx
from functools import wraps

# Import tool calling functionality
from tool_calls import handle_tools, ToolInterceptor
from tool_calls.output_handle import tool_calls_to_openai, tool_calls_to_openai_stream
from tool_calls.utils import determine_model_family

# Import centralized logging
from logging_config import get_logger, log_request_summary, log_response_summary, log_tool_processing, log_data_verbose


app = Flask(__name__)
CORS(app,
     origins="*",
     allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
     expose_headers=["Content-Type", "Authorization"],
     methods=["POST", "OPTIONS"],
     supports_credentials=True)


@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')

    return response


# Model names are different between OpenAI and Argo API
MODEL_MAPPING = {
    'gpt35': 'gpt35',
    'gpt-3.5': 'gpt35',

    'gpt35large': 'gpt35large',

    'gpt4': 'gpt4',
    'gpt-4': 'gpt4',

    'gpt4large': 'gpt4large',

    'gpt4turbo': 'gpt4turbo',
    'gpt-4-turbo': 'gpt4turbo',

    'gpt-4o': 'gpt4o',
    'gpt4o': 'gpt4o',
    'gpt-4o-mini': 'gpt4o',

    'gpt4olatest': 'gpt4olatest',
    'gpt-4o-latest': 'gpt4olatest',

    'gpto1preview': 'gpto1preview',
    'o1-preview': 'gpto1preview',

    'o1-mini': 'gpto1mini',
    'gpto1mini': 'gpto1mini',
    'o1mini': 'gpto1mini',
    'o3-mini': 'gpto3mini',
    'o3mini': 'gpto3mini',
    'gpto3mini': 'gpto3mini',
    'gpto4mini': 'gpto4mini',
    'o4-mini': 'gpto4mini',
    'o4mini': 'gpto4mini',

    'gpto1': 'gpto1',
    'o1': 'gpto1',
    'o3': 'gpto3',
    'gpto3': 'gpto3',

    'gpt41': 'gpt41',
    'gpt41mini' : 'gpt41mini',
    'gpt41nano' : 'gpt41nano',

    'gpt5': 'gpt5',
    'gpt5mini': 'gpt5mini',
    'gpt5nano': 'gpt5nano',


    'gemini25pro': 'gemini25pro',
    'gemini25flash': 'gemini25flash',
    'claudeopus4': 'claudeopus4',
    'claudeopus41': 'claudeopus41',
    'claudesonnet4': 'claudesonnet4',
    'claudesonnet45': 'claudesonnet45',
    'claudehaiku45': 'claudehaiku45',
    'claudesonnet37': 'claudesonnet37',
    'claudesonnet35v2': 'claudesonnet35v2',
}


EMBEDDING_MODEL_MAPPING = {
    'text-embedding-3-small': 'v3small',
    'v3small': 'v3small',

    'text-embedding-3-large': 'v3large',
    'v3large': 'v3large',

    'text-embedding-ada-002': 'ada002',
    'ada002': 'ada002',
}

# URL mapping for different models
URL_MAPPING = {
    # Production URLs
    'prod': {
        'chat': 'https://apps.inside.anl.gov/argoapi/api/v1/resource/chat/',
        'embed': 'https://apps.inside.anl.gov/argoapi/api/v1/resource/embed/'
    },
    # Development URLs
    'dev': {
        'chat': 'https://apps-dev.inside.anl.gov/argoapi/api/v1/resource/chat/',
        'embed': 'https://apps-dev.inside.anl.gov/argoapi/api/v1/resource/embed/'
    }
}


def _extract_response_payload(response_obj):
    """Return the nested response payload if present."""
    if isinstance(response_obj, dict) and "response" in response_obj:
        return response_obj["response"]
    return response_obj


def _extract_response_text(response_obj):
    """Extract textual content from an Argo response object."""
    payload = _extract_response_payload(response_obj)

    if isinstance(payload, dict):
        content = payload.get("content")
        if content is None:
            return ""
        if isinstance(content, (dict, list)):
            try:
                return json.dumps(content)
            except TypeError:
                return str(content)
        return content

    if payload is None:
        return ""

    return payload if isinstance(payload, str) else str(payload)

# Define which models use which environment
MODEL_ENV = {
    # Models using production environment
    'gpt35': 'prod',
    'gpt35large': 'prod',
    'gpt4': 'prod',
    'gpt4large': 'prod',
    'gpt4turbo': 'prod',
    'gpt4o': 'prod',
    'gpt4olatest': 'prod',
    'gpto1preview': 'prod',

    # Models using development environment
    'gpto3mini': 'dev',
    'gpto1mini': 'dev',
    'gpto1': 'dev',
    'gemini25pro': 'dev',
    'gemini25flash': 'dev',
    'claudeopus4': 'dev',
    'claudeopus41': 'dev',
    'claudesonnet4': 'dev',
    'claudesonnet45': 'dev',
    'claudehaiku45': 'dev',
    'claudesonnet37': 'dev',
    'claudesonnet35v2': 'dev',
    'gpto3': 'dev',
    'gpto4mini': 'dev',
    'gpt41': 'dev',
    'gpt41mini' : 'dev',
    'gpt41nano' : 'dev',
    'gpt5': 'dev',
    'gpt5mini': 'dev',
    'gpt5nano': 'dev',
}


NON_STREAMING_MODELS = ['gemini25pro', 'gemini25flash',
                        'claudeopus4', 'claudeopus41', 'claudesonnet4', 'claudesonnet45', 'claudesonnet37', 'claudesonnet35v2',
                        'gpto3', 'gpto4mini', 'gpt41', 'gpt41mini', 'gpt41nano', 'gpt5', 'gpt5mini', 'gpt5nano']

# For models endpoint
MODELS = {
    "object": "list",
    "data": []
}

for model in MODEL_ENV.keys():
    MODELS["data"].append({
            "id": model,
            "object": "model",
            "created": int(datetime.datetime.now().timestamp()),
            "owned_by": "system"
    })



# Default embedding environment
EMBED_ENV = 'prod'

DEFAULT_MODEL = "gpt4o"
BRIDGE_USER = "ARGO_BRIDGE"
ANL_STREAM_URL = "https://apps-dev.inside.anl.gov/argoapi/api/v1/resource/streamchat/"
ANL_DEBUG_FP = 'log_bridge.log'


def get_user_from_auth_header():
    """
    Extracts the user from the Authorization header.
    If the header is present and valid, the bearer token is returned.
    Otherwise, the default user is returned.
    """
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        # Return the token part of the header
        token = auth_header.split(" ")[1]
        logging.debug(f"Authorization header found: {auth_header}")
        if token == 'noop':
            return BRIDGE_USER

        return auth_header.split(" ")[1]
    # Return the default user if no valid header is found
    return BRIDGE_USER


def get_api_url(model, endpoint_type):
    """
    Determine the correct API URL based on model and endpoint type

    Args:
        model (str): The model identifier
        endpoint_type (str): Either 'chat' or 'embed'

    Returns:
        str: The appropriate API URL
    """
    # For embedding models, use the default embedding environment
    if model in EMBEDDING_MODEL_MAPPING.values():
        env = EMBED_ENV
    else:
        # For chat models, look up the environment or default to prod
        env = MODEL_ENV.get(model, 'prod')

    # Return the URL from the mapping
    return URL_MAPPING[env][endpoint_type]

# ================================
# Error Proxy Helpers
# ================================

class ArgoAPIError(Exception):
    def __init__(self, response):
        self.status_code = getattr(response, "status_code", 500)
        self.reason = getattr(response, "reason", "Unknown Error")
        self.body = _try_get_json_from_response(response)
        self.is_json = isinstance(self.body, (dict, list))
        super().__init__(f"Argo API error {self.status_code}: {self.reason}")

def _try_get_json_from_response(response):
    """
    Safely attempt to extract a JSON object from a requests.Response-like object.
    Returns dict/list if successful, otherwise None.
    """
    # Try based on Content-Type and text
    try:
        content_type = getattr(response, "headers", {}).get("Content-Type", "")
    except Exception:
        content_type = ""
    if isinstance(content_type, str) and "application/json" in content_type.lower():
        try:
            text = getattr(response, "text", "")
            if isinstance(text, str) and text:
                parsed = json.loads(text)
                if isinstance(parsed, (dict, list)):
                    return parsed
        except Exception:
            pass
    # Try response.json()
    try:
        parsed = response.json()
        if isinstance(parsed, (dict, list)):
            return parsed
    except Exception:
        pass
    # Try parse text as JSON regardless
    try:
        text = getattr(response, "text", "")
        if isinstance(text, str) and text:
            parsed = json.loads(text)
            if isinstance(parsed, (dict, list)):
                return parsed
    except Exception:
        pass
    return None

def _proxy_argo_error_response(response, logger, fallback_status=500):
    """
    If Argo returns a JSON error body (e.g., on 400), pass it through with the original status.
    Otherwise, return a generic error with fallback_status.
    """
    body = _try_get_json_from_response(response)
    if body is not None:
        logger.error(f"Argo API error body (proxied): {body}")
        try:
            status = int(getattr(response, "status_code", fallback_status))
        except Exception:
            status = fallback_status
        return jsonify(body), status

    # Non-JSON body fallback
    text = getattr(response, "text", "")
    logger.error(f"Argo API non-JSON error body: {text}")
    return jsonify({"error": {
        "message": f"Internal API error: {getattr(response, 'status_code', 'unknown')} {getattr(response, 'reason', '')}".strip()
    }}), fallback_status

"""
=================================
    Chat Endpoint
=================================
"""

@app.route('/chat/completions', methods=['POST'])
@app.route('/api/chat/completions', methods=['POST'])
@app.route('/v1/chat/completions', methods=['POST']) #LMStudio Compatibility
def chat_completions():
    logger = get_logger('chat')
    
    data = request.get_json()
    model_base = data.get("model", DEFAULT_MODEL)
    is_streaming = data.get("stream", False)
    temperature = data.get("temperature", 0.1)
    stop = data.get("stop", [])

    # Check if request contains tool-related parameters
    has_tools = "tools" in data or "tool_choice" in data
    
    # Log request summary
    log_request_summary("/v1/chat/completions", model_base, has_tools)
    log_data_verbose("Request data", data)

    # Force non-streaming for specific models. Remove once Argo supports streaming for all models.
    # TODO: TEMP Fake streaming for the new models until Argo supports it
    is_fake_stream = False
    if model_base in NON_STREAMING_MODELS and is_streaming:
        is_fake_stream = True
        logger.debug(f"Using fake streaming for {model_base}")
    
    # Also force fake streaming for tool calls until we implement streaming tool support
    if has_tools and is_streaming:
        is_fake_stream = True
        logger.debug("Using fake streaming for tool calls")

    if model_base not in MODEL_MAPPING:
        logger.error(f"Unsupported model: {model_base}")
        return jsonify({"error": {
            "message": f"Model '{model_base}' not supported."
        }}), 400

    model = MODEL_MAPPING[model_base]

    # Process tool calls if present
    if has_tools:
        try:
            # Determine if we should use native tools or prompt-based tools
            model_family = determine_model_family(model)
            use_native_tools = model_family in ["openai", "anthropic"]
            
            tool_count = len(data.get("tools", []))
            log_tool_processing(model_family, tool_count, use_native_tools)
            
            data = handle_tools(data, native_tools=use_native_tools)
            log_data_verbose("Processed request with tools", data)
        except Exception as e:
            logger.error(f"Tool processing failed: {e}")
            return jsonify({"error": {
                "message": f"Tool processing failed: {str(e)}"
            }}), 400

    # Process multimodal content for Gemini models
    if model_base.startswith('gemini'):
        try:
            data['messages'] = convert_multimodal_to_text(data['messages'], model_base)
        except ValueError as e:
            return jsonify({"error": {
                "message": str(e)
            }}), 400

    user = get_user_from_auth_header()

    req_obj = {
        "user": user,
        "model": model,
        "messages": data['messages'],
        "system": data.get("system", ""),
        "stop": stop,
        "temperature": temperature
    }

    # Add tool-related fields if they exist (for native tool calling)
    if "tools" in data:
        req_obj["tools"] = data["tools"]
    if "tool_choice" in data:
        req_obj["tool_choice"] = data["tool_choice"]

    log_data_verbose("Argo request", req_obj)

    if is_fake_stream:
        response = requests.post(get_api_url(model, 'chat'), json=req_obj)

        if not response.ok:
            logger.error(f"Argo API error: {response.status_code} {response.reason}")
            log_response_summary("error", model_base)
            return _proxy_argo_error_response(response, logger)

        json_response = response.json()
        text = _extract_response_text(json_response)
        log_data_verbose("Response text", text)
        
        # Process tool calls in response if present
        if has_tools:
            log_response_summary("success", model_base, "tool_calls")
            return Response(
                _fake_stream_response_with_tools(json_response, model, model_base), 
                mimetype='text/event-stream'
            )
        else:
            log_response_summary("success", model_base, "stop")
            return Response(_fake_stream_response(text, model), mimetype='text/event-stream')

    elif is_streaming:
        if has_tools:
            return Response(_stream_chat_response_with_tools(model, req_obj, model_base), mimetype='text/event-stream')
        else:
            return Response(_stream_chat_response(model, req_obj), mimetype='text/event-stream')
    else:
        response = requests.post(get_api_url(model, 'chat'), json=req_obj)

        if not response.ok:
            logger.error(f"Argo API error: {response.status_code} {response.reason}")
            log_response_summary("error", model_base)
            return _proxy_argo_error_response(response, logger)

        json_response = response.json()
        text = _extract_response_text(json_response)
        log_data_verbose("Response text", text)
        
        # Process tool calls in response if present
        if has_tools:
            log_response_summary("success", model_base, "tool_calls")
            return jsonify(_static_chat_response_with_tools(text, model_base, json_response))
        else:
            log_response_summary("success", model_base, "stop")
            return jsonify(_static_chat_response(text, model_base))


def _stream_chat_response(model, req_obj):
    begin_chunk = {
        "id": 'abc',
        "object": "chat.completion.chunk",
        "created": int(datetime.datetime.now().timestamp()),
        "model": model,
        "choices": [{
                    "index": 0,
                    "delta": {'role': 'assistant', 'content':''},
                    "logprobs": None,
                    "finish_reason": None
                }]
    }
    yield f"data: {json.dumps(begin_chunk)}\n\n"


    with httpx.stream("POST", ANL_STREAM_URL, json=req_obj, timeout=300.0)  as response:
        for chunk in response.iter_bytes():
            if chunk:
                text = chunk.decode(errors="replace")
                logging.debug(f'Text Chunk Recieved: {chunk}')
                response_chunk = {
                    "id": 'abc',
                    "object": "chat.completion.chunk",
                    "created": int(datetime.datetime.now().timestamp()),
                    "model": model,
                    "choices": [{
                                "index": 0,
                                "delta": {'content': text},
                                "logprobs": None,
                                "finish_reason": None
                            }]
                }
                yield f"data: {json.dumps(response_chunk)}\n\n"

    end_chunk = {
        "id": 'argo',
        "object": "chat.completion.chunk",
        "created": int(datetime.datetime.now().timestamp()),
        "model": model,
        "system_fingerprint": "fp_44709d6fcb",
        "choices": [{
            "index": 0,
            "delta": {},
            "logprobs": None,
            "finish_reason": "stop"
        }]
    }
    yield f"data: {json.dumps(end_chunk)}\n\n"
    yield "data: [DONE]\n\n"


def _static_chat_response(text, model):
    return {
        "id": "argo",
        "object": "chat.completion",
        "created": int(datetime.datetime.now().timestamp()),
        "model": model,
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": text,
            },
            "logprobs": None,
            "finish_reason": "stop"
        }]
    }

def _fake_stream_response(text, model):
    begin_chunk = {
        "id": 'abc',
        "object": "chat.completion.chunk",
        "created": int(datetime.datetime.now().timestamp()),
        "model": model,
        "choices": [{
                    "index": 0,
                    "delta": {'role': 'assistant', 'content':''},
                    "logprobs": None,
                    "finish_reason": None
                }]
    }
    yield f"data: {json.dumps(begin_chunk)}\n\n"
    chunk = {
                    "id": 'abc',
                    "object": "chat.completion.chunk",
                    "created": int(datetime.datetime.now().timestamp()),
                    "model": model,
                    "choices": [{
                                "index": 0,
                                "delta": {'content': text},
                                "logprobs": None,
                                "finish_reason": None
                            }]
                }
    yield f"data: {json.dumps(chunk)}\n\n"
    end_chunk = {
        "id": 'argo',
        "object": "chat.completion.chunk",
        "created": int(datetime.datetime.now().timestamp()),
        "model": model,
        "system_fingerprint": "fp_44709d6fcb",
        "choices": [{
            "index": 0,
            "delta": {},
            "logprobs": None,
            "finish_reason": "stop"
        }]
    }
    yield f"data: {json.dumps(end_chunk)}\n\n"
    yield "data: [DONE]\n\n"

def convert_multimodal_to_text(messages, model_base):
    """
    Convert multimodal content format to plain text for Gemini models.

    Args:
        messages (list): List of message objects
        model_base (str): The model being used

    Returns:
        list: Processed messages with text-only content

    Raises:
        ValueError: If non-text content is found in multimodal format
    """
    # Only process for Gemini models
    gemini_models = ['gemini25pro', 'gemini25flash']
    if model_base not in gemini_models:
        return messages

    processed_messages = []

    for message in messages:
        processed_message = message.copy()
        content = message.get("content")

        # Check if content is in multimodal format (list of content objects)
        if isinstance(content, list):
            text_parts = []

            for content_item in content:
                if isinstance(content_item, dict):
                    content_type = content_item.get("type")

                    if content_type == "text":
                        text_parts.append(content_item.get("text", ""))
                    else:
                        # Error if non-text content is found
                        raise ValueError(f"Gemini models only support text content. Found unsupported content type: '{content_type}'")
                else:
                    # If content item is not a dict, treat as plain text
                    text_parts.append(str(content_item))

            # Join all text parts and set as the content
            processed_message["content"] = " ".join(text_parts)

        processed_messages.append(processed_message)

    return processed_messages


def _static_chat_response_with_tools(text, model_base, json_response):
    """
    Generate static chat response with tool call processing.
    """
    # Initialize tool interceptor
    tool_interceptor = ToolInterceptor()
    
    # Determine model family for processing
    model_family = determine_model_family(model_base)
    
    # Process response to extract tool calls
    response_payload = _extract_response_payload(json_response)

    tool_calls, clean_text = tool_interceptor.process(
        response_payload,
        model_family
    )

    if not clean_text:
        clean_text = text
    
    # Determine finish reason
    finish_reason = "tool_calls" if tool_calls else "stop"
    
    # Convert tool calls to OpenAI format if present
    openai_tool_calls = None
    if tool_calls:
        openai_tool_calls = tool_calls_to_openai(tool_calls, api_format="chat_completion")
        # Convert Pydantic models to dictionaries for JSON serialization
        openai_tool_calls = [tool_call.model_dump() for tool_call in openai_tool_calls]
    
    return {
        "id": "argo",
        "object": "chat.completion",
        "created": int(datetime.datetime.now().timestamp()),
        "model": model_base,
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": clean_text,
                "tool_calls": openai_tool_calls,
            },
            "logprobs": None,
            "finish_reason": finish_reason
        }]
    }


def _fake_stream_response_with_tools(json_response, model, model_base):
    """
    Generate fake streaming response with tool call processing.
    """
    # Initialize tool interceptor
    tool_interceptor = ToolInterceptor()
    
    # Determine model family for processing
    model_family = determine_model_family(model_base)
    
    # Process response to extract tool calls
    response_payload = _extract_response_payload(json_response)

    tool_calls, clean_text = tool_interceptor.process(
        response_payload,
        model_family
    )

    if not clean_text:
        clean_text = _extract_response_text(response_payload)
    
    # Start with role chunk
    begin_chunk = {
        "id": 'abc',
        "object": "chat.completion.chunk",
        "created": int(datetime.datetime.now().timestamp()),
        "model": model,
        "choices": [{
            "index": 0,
            "delta": {'role': 'assistant', 'content': ''},
            "logprobs": None,
            "finish_reason": None
        }]
    }
    yield f"data: {json.dumps(begin_chunk)}\n\n"
    
    # Send text content if present
    if clean_text:
        content_chunk = {
            "id": 'abc',
            "object": "chat.completion.chunk",
            "created": int(datetime.datetime.now().timestamp()),
            "model": model,
            "choices": [{
                "index": 0,
                "delta": {'content': clean_text},
                "logprobs": None,
                "finish_reason": None
            }]
        }
        yield f"data: {json.dumps(content_chunk)}\n\n"
    
    # Send tool calls if present
    if tool_calls:
        for i, tool_call in enumerate(tool_calls):
            tool_call_chunk = tool_calls_to_openai_stream(
                tool_call, 
                tc_index=i, 
                api_format="chat_completion"
            )
            chunk = {
                "id": 'abc',
                "object": "chat.completion.chunk",
                "created": int(datetime.datetime.now().timestamp()),
                "model": model,
                "choices": [{
                    "index": 0,
                    "delta": {'tool_calls': [tool_call_chunk.model_dump()]},
                    "logprobs": None,
                    "finish_reason": None
                }]
            }
            yield f"data: {json.dumps(chunk)}\n\n"
    
    # Send final chunk
    finish_reason = "tool_calls" if tool_calls else "stop"
    end_chunk = {
        "id": 'argo',
        "object": "chat.completion.chunk",
        "created": int(datetime.datetime.now().timestamp()),
        "model": model,
        "system_fingerprint": "fp_44709d6fcb",
        "choices": [{
            "index": 0,
            "delta": {},
            "logprobs": None,
            "finish_reason": finish_reason
        }]
    }
    yield f"data: {json.dumps(end_chunk)}\n\n"
    yield "data: [DONE]\n\n"


def _stream_chat_response_with_tools(model, req_obj, model_base):
    """
    Generate streaming response with tool call processing.
    Note: This is a placeholder for future real streaming tool support.
    For now, it falls back to fake streaming.
    """
    # For now, we'll use the non-streaming endpoint and fake stream the result
    # TODO: Implement real streaming tool support when Argo supports it
    
    response = requests.post(get_api_url(model, 'chat'), json=req_obj)
    
    if not response.ok:
        # Return error in streaming format
        error_chunk = {
            "id": 'error',
            "object": "chat.completion.chunk",
            "created": int(datetime.datetime.now().timestamp()),
            "model": model,
            "choices": [{
                "index": 0,
                "delta": {'content': f"Error: {response.status_code} {response.reason}"},
                "logprobs": None,
                "finish_reason": "stop"
            }]
        }
        yield f"data: {json.dumps(error_chunk)}\n\n"
        yield "data: [DONE]\n\n"
        return
    
    json_response = response.json()
    text = _extract_response_text(json_response)
    
    # Use fake streaming with tool processing
    yield from _fake_stream_response_with_tools(json_response, model, model_base)


"""
=================================
    Completions Endpoint
=================================
"""


@app.route('/completions', methods=['POST'])
@app.route('/v1/completions', methods=['POST', 'OPTIONS']) #LMStudio Compatibility
def completions():
    logger = get_logger('completions')
    
    data = request.get_json()
    prompt = data.get("prompt", "")
    stop = data.get("stop", [])
    temperature = data.get("temperature", 0.1)
    model_base = data.get("model", DEFAULT_MODEL)
    is_streaming = data.get("stream", False)

    log_request_summary("/v1/completions", model_base)
    log_data_verbose("Request data", data)

    if model_base not in MODEL_MAPPING:
        logger.error(f"Unsupported model: {model_base}")
        return jsonify({"error": {
            "message": f"Model '{model_base}' not supported."
        }}), 400

    model = MODEL_MAPPING[model_base]

    user = get_user_from_auth_header()

    req_obj = {
        "user": user,
        "model": model,
        "prompt": [data['prompt']],
        "system": "",
        "stop": stop,
        "temperature": temperature
    }

    log_data_verbose("Argo request", req_obj)

    response = requests.post(get_api_url(model, 'chat'), json=req_obj)
    if not response.ok:
        logger.error(f"Argo API error: {response.status_code} {response.reason}")
        log_response_summary("error", model_base)
        return _proxy_argo_error_response(response, logger)

    json_response = response.json()
    text = _extract_response_text(json_response)
    log_data_verbose("Response text", text)

    if is_streaming:
        log_response_summary("success", model_base, "stop")
        return Response(_stream_completions_response(text, model), mimetype='text/event-stream')
    else:
        log_response_summary("success", model_base, "stop")
        return jsonify(_static_completions_response(text, model_base))


def _static_completions_response(text, model):
    return {
        "id": "argo",
        "object": "text_completion",
        "created": int(datetime.datetime.now().timestamp()),
        "model": model,
        "choices": [{
            "text": text,
            "logprobs": None,
            "finish_reason": "stop"
        }]
    }

def _stream_completions_response(text, model):
    chunk = {
        "id": 'abc',
        "object": "text_completion",
        "created": int(datetime.datetime.now().timestamp()),
        "model": model,
        "choices": [{
            "text": text,
            'index': 0,
            "logprobs": None,
            "finish_reason": "stop"
        }]
    }
    yield f"data: {json.dumps(chunk)}\n\n"
    yield "data: [DONE]\n\n"


"""
=================================
    Embeddings Endpoint
=================================
"""
@app.route('/embeddings', methods=['POST'])
@app.route('/v1/embeddings', methods=['POST'])
def embeddings():
    logger = get_logger('embeddings')
    
    data = request.get_json()
    model_base = data.get("model", "v3small")

    log_request_summary("/v1/embeddings", model_base)
    log_data_verbose("Request data", data)

    # Check if the model is supported
    if model_base not in EMBEDDING_MODEL_MAPPING:
        logger.error(f"Unsupported embedding model: {model_base}")
        return jsonify({"error": {
            "message": f"Embedding model '{model_base}' not supported."
        }}), 400
    model = EMBEDDING_MODEL_MAPPING[model_base]

    input_data = data.get("input", [])
    if isinstance(input_data, str):
        input_data = [input_data]

    user = get_user_from_auth_header()
    
    try:
        embedding_vectors = _get_embeddings_from_argo(input_data, model, user)
    except ArgoAPIError as e:
        logger.error(f"Embedding API error: {e.status_code} {e.reason}")
        log_response_summary("error", model_base)
        if e.is_json:
            return jsonify(e.body), e.status_code
        else:
            return jsonify({"error": {
                "message": f"Embedding API error: {e.status_code} {e.reason}"
            }}), e.status_code
    except Exception as e:
        logger.error(f"Embedding processing failed: {e}")
        log_response_summary("error", model_base)
        return jsonify({"error": {
            "message": f"Embedding processing failed: {str(e)}"
        }}), 500

    response_data = {
        "object": "list",
        "data": [],
        "model": model_base,
        "usage": {
            "prompt_tokens": 0,  # We don't have token counts from Argo
            "total_tokens": 0
        }
    }

    for i, embedding in enumerate(embedding_vectors):
        response_data["data"].append({
            "object": "embedding",
            "embedding": embedding,
            "index": i
        })

    log_response_summary("success", model_base)
    return jsonify(response_data)


def _get_embeddings_from_argo(texts, model, user=BRIDGE_USER):
    logger = get_logger('embeddings')
    BATCH_SIZE = 16
    all_embeddings = []

    for i in range(0, len(texts), BATCH_SIZE):
        batch_texts = texts[i:i + BATCH_SIZE]

        payload = {
            "user": user,
            "model": model,
            "prompt": batch_texts
        }

        logger.debug(f"Sending embedding request for batch {i // BATCH_SIZE + 1}")
        log_data_verbose(f"Embedding batch {i // BATCH_SIZE + 1} payload", payload)

        response = requests.post(get_api_url(model, 'embed'), json=payload)

        if not response.ok:
            logger.error(f"Argo embedding API error: {response.status_code} {response.reason}")
            raise ArgoAPIError(response)

        embedding_response = response.json()
        batch_embeddings = embedding_response.get("embedding", [])
        all_embeddings.extend(batch_embeddings)

    logger.debug(f"Successfully processed {len(all_embeddings)} embeddings")
    return all_embeddings

"""
=================================
    Models Endpoint
=================================
"""
@app.route('/models', methods=['GET'])
@app.route('/v1/models', methods=['GET'])
def models_list():
    logging.info("Received models list request")
    return jsonify(MODELS)


def check_argo_connection():
    """
    Check connection to Argo API endpoints and report status.

    Returns:
        bool: True if all connections successful, False otherwise
    """
    all_successful = True

    # Print for end-user
    print("\nTesting Argo API connections...")
    logging.info("Testing Argo API connections")

    for env in ['prod', 'dev']:
        for endpoint_type in ['chat', 'embed']:
            url = URL_MAPPING[env][endpoint_type]
            try:
                response = requests.head(url, timeout=5)
                msg = f"✓ Connection to {env} {endpoint_type} endpoint ({url}) available"
                print(msg)
                logging.info(msg)
            except requests.exceptions.RequestException as e:
                msg = f"✗ Connection to {env} {endpoint_type} endpoint ({url}) failed: {str(e)}"
                print(msg)
                logging.error(msg)
                all_successful = False

    if all_successful:
        print("✓ All Argo API connections successful!")
        logging.info("All Argo API connections successful")
    else:
        print("⚠ Some Argo API connections failed. The server may not function correctly.")
        logging.warning("Some Argo API connections failed")

    return all_successful


"""
=================================
    CLI Functions
=================================
"""

def parse_args():
    parser = argparse.ArgumentParser(description='Run the Flask server.')
    parser.add_argument('-u', '--username', required=True, type=str, help='Username for the API requests')
    parser.add_argument('--port', type=int, default=7285, help='Port number to run the server on')
    parser.add_argument('--dlog', action='store_true', help='Enable debug-level logging')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    BRIDGE_USER = args.username
    debug_enabled = args.dlog
    logging.basicConfig(
        filename=ANL_DEBUG_FP,
        level=logging.DEBUG if debug_enabled else logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logging.getLogger('watchdog').setLevel(logging.CRITICAL+10)

    logging.info(f'Starting server with debug mode: {debug_enabled}')
    print(f'Starting server... | Port {args.port} | User {args.username} | Debug: {debug_enabled}')

    check_argo_connection()

    app.run(host='localhost', port=args.port, debug=debug_enabled)
