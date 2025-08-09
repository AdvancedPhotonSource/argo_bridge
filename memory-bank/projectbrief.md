# Project Brief: Argo Bridge

## Project Overview
Argo Bridge is a Python Flask-based compatibility layer that transforms OpenAI-style API requests into Argonne National Lab's Argo API format. It provides OpenAI-compatible endpoints for chat completions, text completions, and embeddings, with advanced tool calling capabilities added as an enhancement.

## Core Purpose
- **API Compatibility Layer**: Transforms OpenAI API requests to Argo API format for Argonne National Lab's AI services
- **Tool Calling Enhancement**: Advanced tool calling system supporting both native and prompt-based function calling
- **Model Access**: Provides access to multiple AI models (OpenAI, Anthropic, Google) through Argo's infrastructure
- **Production Ready**: Includes Docker deployment, monitoring, and scaling configurations

## Key Components
1. **Main Bridge Server** (`argo_bridge.py`) - Core Flask application that transforms OpenAI requests to Argo format
2. **Tool Calling System** (`tool_calls/`) - Modular system for handling OpenAI-compatible function calls
3. **Argo Proxy Integration** (`argo-proxy-master/`) - Reference implementation for advanced proxy features
4. **Examples and Documentation** - Comprehensive examples showing tool calling usage

## Primary Goals
- Provide OpenAI-compatible access to Argonne National Lab's Argo API
- Enable advanced tool calling capabilities for AI applications
- Support multiple AI model providers (OpenAI, Anthropic, Google) through unified interface
- Support production deployment with monitoring and scaling

## Target Use Cases
- Organizations needing OpenAI-compatible access to Argo API services
- AI applications requiring function calling capabilities
- Development environments needing access to multiple model providers
- Research and experimentation with tool-augmented AI through Argonne's infrastructure

## Technical Foundation
- **Language**: Python 3.12
- **Framework**: Flask for web server
- **API Standard**: OpenAI-compatible endpoints transforming to Argo API format
- **Architecture**: Compatibility layer with modular tool calling system
- **Deployment**: Docker support with Prometheus/Grafana monitoring
