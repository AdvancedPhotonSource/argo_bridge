# Active Context: Argo Bridge

## Current Project State
The Argo Bridge project is a functional OpenAI-to-Argo API compatibility layer with advanced tool calling capabilities:

### Working Components
1. **Core Flask Application** (`argo_bridge.py`) - OpenAI-compatible API server that transforms requests to Argo format
2. **Tool Calling System** - Complete modular system supporting both native and prompt-based function calling
3. **Model Support** - Supports OpenAI, Anthropic, and Google models through Argo API
4. **Examples** - Working tool calling examples in `examples/tool_calling_example.py`
5. **Documentation** - Comprehensive tool calling documentation in `TOOL_CALLING.md`
6. **Production Deployment** - Docker, Prometheus, and Grafana configurations

### Recent Focus Areas
Based on the open VSCode tabs, recent work has been focused on:
- **Tool Calling Handler** (`tool_calls/handler.py`) - Core tool execution logic and format conversion
- **Input/Output Processing** - Request and response handling modules
- **Type Safety** - Function call type definitions and Pydantic models
- **Example Implementation** - Comprehensive tool calling test suite

## Key Technical Patterns in Use

### Tool Calling Architecture
The system uses a modular approach with dual support:
- **Native Tool Calling**: Full OpenAI function calling for OpenAI and Anthropic models
- **Prompt-Based Tools**: Automatic fallback to prompt-based tools for Google models
- **Format Conversion**: Automatic conversion between different model provider formats
- **Streaming Support**: Tool calling works with both streaming and non-streaming responses

### Integration Strategy
- **Argo API Integration**: Direct integration with Argonne National Lab's Argo API
- **OpenAI Compatibility**: Full compatibility with OpenAI API standards and client libraries
- **Multi-Environment Support**: Supports both production and development Argo environments

## Current Development Priorities

### 1. Tool System Robustness
- Ensuring reliable tool execution with proper error handling
- Maintaining streaming capabilities for tool calling workflows
- Optimizing performance for request transformation and tool processing

### 2. Production Readiness
- Docker-based deployment with monitoring
- Prometheus metrics integration
- Grafana dashboard configuration
- SSL support for production deployment

### 3. Developer Experience
- Clear examples and documentation
- OpenAI client library compatibility
- Comprehensive error messages and debugging support

## Important Project Insights

### Design Philosophy
- **Compatibility First**: Designed to be a drop-in replacement for OpenAI API
- **Enhanced Functionality**: Adds advanced tool calling to Argo API capabilities
- **Production Ready**: Includes monitoring, scaling, and deployment from the start

### Key Differentiators
- **Argo API Bridge**: Unique compatibility layer for Argonne's infrastructure
- **Dual Tool Support**: Both native and prompt-based tool calling
- **Multi-Model Access**: OpenAI, Anthropic, and Google models through single interface
- **Enterprise Ready**: Production deployment with monitoring and scaling

## Current Configuration

### Model Environment Mapping
- **Production Models**: OpenAI models (gpt-4o, gpt-4-turbo, etc.)
- **Development Models**: Anthropic and Google models (claude-sonnet-4, gemini-2.5-pro, etc.)
- **Automatic Routing**: Models automatically routed to correct Argo environment

### Tool Calling Support
- **Native Support**: OpenAI and Anthropic models with full function calling
- **Prompt-Based**: Google models with automatic fallback to prompt-based tools
- **Streaming**: Both streaming and non-streaming tool execution
- **Format Conversion**: Seamless conversion between provider formats

### API Endpoints
- `/v1/chat/completions` - Chat completions with tool calling support
- `/v1/completions` - Legacy text completions
- `/v1/embeddings` - Text embeddings
- `/v1/models` - Available models listing

## Next Steps Considerations

### Potential Areas for Enhancement
1. **Real Streaming Tools**: Implement true streaming tool calls when Argo supports it
2. **Google Native Tools**: Add native tool calling for Google models when available
3. **Tool Registry**: More sophisticated tool registration and management system
4. **Authentication**: Enhanced security features for production deployment
5. **Caching**: Response caching for improved performance

### Maintenance Priorities
1. **Documentation**: Keep documentation up-to-date with Argo API changes
2. **Examples**: Maintain working examples for common use cases
3. **Monitoring**: Ensure monitoring and alerting are properly configured
4. **Performance**: Monitor and optimize request transformation performance

## Project Relationships

### Upstream Dependencies
- **Argo API**: Argonne National Lab's AI model API infrastructure
- **OpenAI API**: Compatibility standard for client integration
- **Flask Ecosystem**: Web framework and related tools
- **Pydantic**: Type validation and serialization

### Downstream Consumers
- **OpenAI Applications**: Existing applications using OpenAI client libraries
- **Development Tools**: IDEs and tools requiring AI model access
- **Research Systems**: Research applications needing access to multiple model providers
- **Enterprise Applications**: Production systems requiring reliable AI model access

## Current Limitations and Known Issues

### Technical Limitations
1. **Fake Streaming**: Tool calls use "fake streaming" (non-streaming response sent as chunks)
2. **Google Models**: Limited to prompt-based tool calling
3. **Parallel Tool Calls**: Not yet fully implemented
4. **Tool Results**: Tool result handling in conversation context needs enhancement

### Areas for Improvement
1. **Error Recovery**: Could be enhanced for complex failure scenarios
2. **Configuration Management**: Could benefit from more sophisticated config system
3. **Performance Monitoring**: Could benefit from more detailed performance metrics
4. **Security**: Additional security features for production deployment

## Integration Status

### Tested Integrations
- **OpenAI Client Libraries**: Python, JavaScript, and other language clients
- **IDE Integrations**: Various development environment integrations
- **Web UIs**: Web-based AI application interfaces
- **Command Line Tools**: CLI tools requiring AI model access

### Connection Health
- **Argo API Connectivity**: Built-in connection testing for both prod and dev environments
- **Model Availability**: Automatic detection of model availability
- **Error Handling**: Graceful handling of Argo API errors and timeouts
- **Monitoring**: Comprehensive monitoring of request/response cycles
