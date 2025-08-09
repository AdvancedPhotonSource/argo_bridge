# Technical Context: Argo Bridge

## Technology Stack

### Core Technologies
- **Python 3.12**: Primary programming language
- **Flask**: Web framework for API endpoints
- **Gunicorn**: WSGI HTTP Server for production
- **Docker**: Containerization and deployment
- **Prometheus**: Metrics collection and monitoring
- **Grafana**: Monitoring dashboards

### Key Dependencies
```
flask>=2.0.0
requests>=2.28.0
gunicorn>=20.1.0
prometheus-client>=0.14.0
flask-cors
httpx
pydantic>=2.0.0
```

### Development Environment
- **Package Management**: Standard pip/requirements.txt approach
- **Container Development**: Docker and docker-compose for local development
- **Code Organization**: Modular structure with clear separation of concerns

## Project Structure

### Main Application Files
```
argo_bridge.py          # Main Flask application with OpenAI-to-Argo transformation
bridge_prod.py          # Production server entry point
requirements.txt        # Python dependencies
gunicorn_config.py     # Production server configuration
```

### Tool Calling System
```
tool_calls/
├── __init__.py         # Package initialization
├── handler.py          # Main tool execution logic and format conversion
├── input_handle.py     # Request processing and tool validation
├── output_handle.py    # Response formatting and streaming
├── tool_prompts.py     # Tool prompt management for prompt-based tools
└── utils.py           # Shared utilities and helpers
```

### Type Definitions
```
tool_types/
├── __init__.py
└── function_call.py    # Function call type definitions

types/
├── __init__.py
└── function_call.py    # Pydantic models for OpenAI and Anthropic formats
```

### Examples and Documentation
```
examples/
└── tool_calling_example.py  # Comprehensive tool calling test suite

TOOL_CALLING.md         # Detailed tool calling documentation
readme.md              # Project setup and usage documentation
downstream_config.md    # Integration guides for various tools
```

### Deployment Configuration
```
dockerfile              # Container build configuration
docker-compose.yaml     # Multi-container orchestration
prometheus.yml.template # Monitoring configuration template
```

### Monitoring Setup
```
grafana/
├── dashboards/
│   └── argo-bridge-dashboard.json
└── provisioning/
    ├── dashboards/
    └── datasources/
```

## Integration Architecture

### Argo API Integration
- **Direct Integration**: Direct HTTP calls to Argonne National Lab's Argo API
- **Environment Support**: Both production and development Argo environments
- **Model Routing**: Automatic routing based on model availability
- **Authentication**: Bearer token to username mapping

### API Compatibility
- **Standard**: OpenAI API v1 compatibility
- **Endpoints**: 
  - `/v1/chat/completions` - Chat completions with tool calling
  - `/v1/completions` - Legacy text completions
  - `/v1/embeddings` - Text embeddings
  - `/v1/models` - Available models listing

### Model Support
```python
# OpenAI Models (Production Environment)
'gpt-4o', 'gpt-4-turbo', 'gpt-4', 'gpt-3.5-turbo'

# Anthropic Models (Development Environment)  
'claude-sonnet-4', 'claude-opus-4', 'claude-sonnet-3.7'

# Google Models (Development Environment)
'gemini-2.5-pro', 'gemini-2.5-flash'

# Embedding Models
'text-embedding-3-small', 'text-embedding-3-large', 'text-embedding-ada-002'
```

## Development Patterns

### Code Organization
- **Modular Design**: Clear separation between API transformation and tool calling
- **Single Responsibility**: Each module has a focused purpose
- **Type Safety**: Pydantic models for request/response validation

### Tool Calling Architecture
- **Dual Strategy**: Native tools for OpenAI/Anthropic, prompt-based for Google
- **Format Conversion**: Automatic conversion between provider formats
- **Streaming Support**: Both streaming and non-streaming tool execution
- **Error Handling**: Graceful degradation and comprehensive logging

### Testing Strategy
- **Example-Driven**: Comprehensive examples showing usage patterns
- **Integration Testing**: End-to-end testing of tool calling flows
- **Connection Testing**: Built-in Argo API connection validation

## Deployment Considerations

### Container Strategy
- **Multi-Service**: Docker compose with bridge, Prometheus, and Grafana
- **Environment Configuration**: Environment variable based configuration
- **SSL Support**: HTTPS configuration for production deployment
- **Health Checks**: Built-in health check endpoints

### Production Requirements
- **Process Management**: Gunicorn for production serving
- **Monitoring**: Prometheus metrics and Grafana dashboards
- **Logging**: Structured logging for production debugging
- **Scaling**: Horizontal scaling support through stateless design

### Security Considerations
- **Input Validation**: Proper validation of tool calling requests
- **Error Sanitization**: Safe error message handling
- **Authentication**: Bearer token authentication with user mapping
- **CORS Support**: Cross-origin resource sharing for web applications

## Performance Characteristics

### Latency Considerations
- **Request Transformation**: Minimal overhead for API format conversion
- **Tool Processing**: Efficient tool calling pipeline
- **Streaming Support**: Real-time response streaming for long-running requests
- **Connection Management**: Efficient HTTP connections to Argo API

### Scalability Features
- **Stateless Design**: No server-side state between requests
- **Horizontal Scaling**: Support for multiple instances
- **Load Balancing**: Standard HTTP interface compatible with load balancers
- **Resource Management**: Proper cleanup and resource handling

## Configuration Management

### Environment Variables
- **Argo Configuration**: API endpoints and authentication
- **Server Configuration**: Port, host, and server settings
- **Tool Configuration**: Tool-specific configuration options
- **Monitoring Configuration**: Metrics and logging settings

### Model Environment Mapping
```python
# Production Environment Models
MODEL_ENV = {
    'gpt35': 'prod',
    'gpt4': 'prod', 
    'gpt4o': 'prod',
    # ... other production models
}

# Development Environment Models  
MODEL_ENV = {
    'gemini25pro': 'dev',
    'claudesonnet4': 'dev',
    'gpto3mini': 'dev',
    # ... other development models
}
```

### API URL Configuration
```python
URL_MAPPING = {
    'prod': {
        'chat': 'https://apps.inside.anl.gov/argoapi/api/v1/resource/chat/',
        'embed': 'https://apps.inside.anl.gov/argoapi/api/v1/resource/embed/'
    },
    'dev': {
        'chat': 'https://apps-dev.inside.anl.gov/argoapi/api/v1/resource/chat/',
        'embed': 'https://apps-dev.inside.anl.gov/argoapi/api/v1/resource/embed/'
    }
}
```

### File-Based Configuration
- **Docker Compose**: Multi-container configuration
- **Prometheus**: Monitoring configuration templates
- **Grafana**: Dashboard and datasource provisioning
- **Requirements**: Python dependency management
