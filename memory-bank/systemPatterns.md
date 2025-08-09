# System Patterns: Argo Bridge

## Architecture Overview
Argo Bridge follows a layered architecture with clear separation of concerns:

```
OpenAI Client Applications
       ↓
Flask Web Server (argo_bridge.py)
       ↓ 
Request Transformation & Tool Processing
       ↓
Argonne National Lab Argo API
       ↓
AI Model Providers (OpenAI, Anthropic, Google)
```

## Core Design Patterns

### 1. Modular Tool Calling System
**Location**: `tool_calls/` directory

**Components**:
- `handler.py` - Main orchestration and tool execution
- `input_handle.py` - Request processing and validation
- `output_handle.py` - Response formatting and streaming
- `tool_prompts.py` - Tool prompt generation and management
- `utils.py` - Shared utilities and helpers

**Pattern**: Each component has a single responsibility, enabling easy testing and modification.

### 2. API Transformation Pattern
**Location**: Core transformation logic in argo_bridge.py

**Key Aspects**:
- Transforms OpenAI API requests to Argo API format
- Maps model names between OpenAI and Argo conventions
- Handles authentication and user management
- Converts responses back to OpenAI format

### 3. Configuration Management
**Files**: 
- `requirements.txt` - Python dependencies
- `docker-compose.yaml` - Container orchestration
- `gunicorn_config.py` - Production server configuration

**Pattern**: Environment-based configuration with sensible defaults

## Key Technical Decisions

### 1. Flask as Web Framework
**Rationale**: 
- Lightweight and flexible for API transformation
- Simple request/response handling for compatibility layer
- Good ecosystem for API development and CORS support

### 2. Modular Tool System
**Rationale**:
- Enables easy addition of new tools
- Clear separation between tool logic and API handling
- Supports different tool execution patterns (native vs prompt-based)

### 3. OpenAI API Compatibility
**Rationale**:
- Enables existing OpenAI applications to use Argo API
- Leverages existing client libraries and tooling
- Provides familiar interface while accessing Argonne's infrastructure

## Component Relationships

### Request Processing Flow
1. **Request Reception**: Flask receives OpenAI-compatible request
2. **Model Mapping**: Transform OpenAI model names to Argo format
3. **Tool Processing**: `tool_calls/` system handles function calling if present
4. **API Transformation**: Convert request to Argo API format
5. **Argo API Call**: Send request to appropriate Argo endpoint
6. **Response Processing**: Convert Argo response back to OpenAI format
7. **Response Delivery**: Return OpenAI-compatible response

### Tool Calling Patterns
- **Native Tools**: Direct function calling for OpenAI/Anthropic models
- **Prompt-Based Tools**: Automatic fallback for Google models without native support
- **Format Conversion**: Seamless conversion between provider-specific formats
- **Streaming Support**: Both streaming and non-streaming tool execution

### Error Handling Strategy
- **Graceful Degradation**: Tool failures don't break the entire request
- **Detailed Logging**: Comprehensive error logging for debugging
- **Client-Friendly Errors**: Proper HTTP status codes and error messages
- **Argo API Integration**: Proper handling of Argo API errors and timeouts

## Scalability Patterns

### Horizontal Scaling
- **Stateless Design**: No server-side state between requests
- **Container Ready**: Docker support for easy scaling
- **Load Balancer Compatible**: Standard HTTP interface

### Performance Optimization
- **Streaming Support**: Real-time response streaming
- **Efficient Tool Execution**: Optimized tool calling pipeline
- **Resource Management**: Proper cleanup and resource handling
- **Connection Pooling**: Efficient Argo API connections

## Integration Patterns

### Argo API Integration
- **Environment Management**: Support for both production and development Argo environments
- **Model Routing**: Automatic routing to correct Argo environment based on model
- **Authentication**: Bearer token authentication mapped to Argo user system
- **Connection Health**: Built-in connection testing for Argo endpoints

### Monitoring Integration
- **Prometheus Metrics**: Built-in metrics collection
- **Grafana Dashboards**: Pre-configured monitoring dashboards
- **Health Checks**: Standard health check endpoints
- **Request Tracking**: Detailed logging of request/response cycles

## Model Support Patterns

### Model Family Detection
- **OpenAI Models**: Native tool calling support
- **Anthropic Models**: Native tool calling support
- **Google Models**: Prompt-based tool calling fallback
- **Environment Routing**: Automatic routing based on model availability

### Tool Calling Strategies
- **Native Strategy**: Direct API function calling for supported models
- **Prompt Strategy**: Structured prompts for unsupported models
- **Hybrid Approach**: Automatic fallback between strategies
- **Format Normalization**: Consistent OpenAI format regardless of backend
