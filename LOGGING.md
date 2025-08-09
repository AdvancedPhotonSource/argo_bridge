# Argo Bridge Logging Configuration

This document describes the logging configuration for the Argo Bridge server and how to control verbosity.

## Overview

The Argo Bridge now uses a centralized logging system that provides:
- Separate log levels for console and file output
- Environment variable configuration
- Structured logging with appropriate levels
- Optional verbose mode for debugging

## Default Behavior

By default, the server will:
- Log WARNING and above to console (much less verbose)
- Log INFO and above to file (`log_bridge.log`)
- Use structured, summary-style logging instead of full request/response dumps

## Environment Variables

You can control logging behavior using these environment variables:

### Basic Configuration
- `ARGO_LOG_LEVEL`: Overall log level (default: INFO)
- `ARGO_CONSOLE_LOG_LEVEL`: Console log level (default: WARNING)
- `ARGO_FILE_LOG_LEVEL`: File log level (default: same as ARGO_LOG_LEVEL)
- `ARGO_LOG_FILE`: Log file path (default: log_bridge.log)
- `ARGO_VERBOSE`: Enable verbose mode (default: false)

### Log Levels
Available log levels (from most to least verbose):
- `DEBUG`: Detailed debugging information
- `INFO`: General operational information
- `WARNING`: Warning messages
- `ERROR`: Error messages
- `CRITICAL`: Critical errors

## Usage Examples

### Normal Operation (Default)
```bash
python argo_bridge.py
```
- Console: Only warnings and errors
- File: Info level and above

### Verbose Mode
```bash
ARGO_VERBOSE=true python argo_bridge.py
```
- Console: Debug level (very verbose)
- File: Debug level (very verbose)

### Custom Console Verbosity
```bash
ARGO_CONSOLE_LOG_LEVEL=INFO python argo_bridge.py
```
- Console: Info level and above
- File: Info level and above (default)

### Quiet Console, Verbose File
```bash
ARGO_CONSOLE_LOG_LEVEL=ERROR ARGO_FILE_LOG_LEVEL=DEBUG python argo_bridge.py
```
- Console: Only errors
- File: Debug level (very verbose)

### Custom Log File
```bash
ARGO_LOG_FILE=/path/to/custom.log python argo_bridge.py
```

## What's Logged

### Summary Logging (Default)
- Request summaries: endpoint, model, whether tools are used
- Response summaries: status, model, finish reason
- Tool processing summaries: model family, tool count, approach used
- Connection status and errors

### Verbose Logging (DEBUG level)
- Full request and response payloads (truncated if very large)
- Detailed tool conversion information
- Step-by-step processing details
- Streaming chunk information

## Migration from Old Logging

The old system used:
- Many `print()` statements that always appeared on console
- Full request/response logging at INFO level
- Less structured logging

The new system:
- Replaces `print()` with proper logging calls
- Uses summary logging by default
- Provides detailed logging only when requested
- Allows fine-grained control over what appears where

## Troubleshooting

### Too Verbose
If console output is too verbose:
```bash
ARGO_CONSOLE_LOG_LEVEL=WARNING python argo_bridge.py
```

### Need More Detail
If you need to see request/response details:
```bash
ARGO_VERBOSE=true python argo_bridge.py
```

### File Logging Issues
Check file permissions and disk space if logging to file fails. The system will continue to work but may not log to file.

## Development

When developing or debugging:
```bash
ARGO_VERBOSE=true python argo_bridge.py --dlog
```

This enables:
- Verbose logging (DEBUG level everywhere)
- Flask debug mode
- Maximum detail for troubleshooting
