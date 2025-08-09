"""
Logging Configuration for Argo Bridge

This module provides centralized logging configuration with support for:
- Different log levels for console and file output
- Environment variable configuration
- Structured logging with appropriate levels
- Optional verbose mode for debugging
"""

import logging
import os
import sys
from typing import Optional


class ArgoLogger:
    """Centralized logger configuration for Argo Bridge"""
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ArgoLogger, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # Prevent re-initialization if already initialized
        if hasattr(self, '_initialized') and self._initialized:
            return
        self.logger = None
        self._setup_logging()
        self._initialized = True
    
    def _setup_logging(self):
        """Setup logging configuration based on environment variables and defaults"""
        
        # Get configuration from environment variables
        log_level = os.getenv('ARGO_LOG_LEVEL', 'INFO').upper()
        console_level = os.getenv('ARGO_CONSOLE_LOG_LEVEL', 'WARNING').upper()
        file_level = os.getenv('ARGO_FILE_LOG_LEVEL', log_level).upper()
        log_file = os.getenv('ARGO_LOG_FILE', 'log_bridge.log')
        verbose_mode = os.getenv('ARGO_VERBOSE', 'false').lower() == 'true'
        
        # If verbose mode is enabled, make console more verbose
        if verbose_mode:
            console_level = 'DEBUG'
            file_level = 'DEBUG'
        
        # Create logger
        self.logger = logging.getLogger('argo_bridge')
        self.logger.setLevel(logging.DEBUG)  # Set to lowest level, handlers will filter
        
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # File handler - detailed logging
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, file_level))
        file_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler - less verbose by default
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, console_level))
        console_handler.setFormatter(simple_formatter)
        self.logger.addHandler(console_handler)
        
        # Suppress noisy third-party loggers
        logging.getLogger('watchdog').setLevel(logging.CRITICAL + 10)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)
        
        # Log the configuration
        self.logger.info(f"Logging initialized - Console: {console_level}, File: {file_level}")
        if verbose_mode:
            self.logger.debug("Verbose mode enabled")
    
    def get_logger(self, name: Optional[str] = None) -> logging.Logger:
        """Get a logger instance"""
        if name:
            return logging.getLogger(f'argo_bridge.{name}')
        return self.logger
    
    def log_request_summary(self, endpoint: str, model: str, has_tools: bool = False):
        """Log a summary of incoming requests without full payload"""
        tools_info = " (with tools)" if has_tools else ""
        self.logger.info(f"Request: {endpoint} - Model: {model}{tools_info}")
    
    def log_response_summary(self, status: str, model: str, finish_reason: str = None):
        """Log a summary of responses without full payload"""
        reason_info = f" - {finish_reason}" if finish_reason else ""
        self.logger.info(f"Response: {status} - Model: {model}{reason_info}")
    
    def log_tool_processing(self, model_family: str, tool_count: int, native_tools: bool):
        """Log tool processing information"""
        tool_type = "native" if native_tools else "prompt-based"
        self.logger.info(f"Processing {tool_count} tools for {model_family} model using {tool_type} approach")
    
    def log_data_verbose(self, label: str, data: any, max_length: int = 500):
        """Log data only in verbose mode, with optional truncation"""
        if self.logger.isEnabledFor(logging.DEBUG):
            data_str = str(data)
            if len(data_str) > max_length:
                data_str = data_str[:max_length] + "... (truncated)"
            self.logger.debug(f"{label}: {data_str}")


# Global logger instance
_argo_logger = ArgoLogger()

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get the Argo Bridge logger"""
    return _argo_logger.get_logger(name)

def log_request_summary(endpoint: str, model: str, has_tools: bool = False):
    """Log a summary of incoming requests"""
    _argo_logger.log_request_summary(endpoint, model, has_tools)

def log_response_summary(status: str, model: str, finish_reason: str = None):
    """Log a summary of responses"""
    _argo_logger.log_response_summary(status, model, finish_reason)

def log_tool_processing(model_family: str, tool_count: int, native_tools: bool):
    """Log tool processing information"""
    _argo_logger.log_tool_processing(model_family, tool_count, native_tools)

def log_data_verbose(label: str, data: any, max_length: int = 500):
    """Log data only in verbose mode"""
    _argo_logger.log_data_verbose(label, data, max_length)
