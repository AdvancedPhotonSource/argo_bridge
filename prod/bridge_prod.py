"""
Metrics module for the Argo Bridge application.
This separates the metrics functionality from the main application code and allows for conditional import. 
"""
import os
import time
from functools import wraps
from flask import request, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST, multiprocess, CollectorRegistry
from argo_bridge import app, parse_args, ANL_USER
import logging

# Set up the metrics environment
os.environ.setdefault('PROMETHEUS_MULTIPROC_DIR', 'metrics')
REQUEST_COUNT = Counter('argo_requests_total', 'Total API requests', ['endpoint', 'model', 'status'])
REQUEST_LATENCY = Histogram('argo_request_latency_seconds', 'API request latency', ['endpoint', 'model'])

def track_metrics(endpoint_name):
    """Decorator to track metrics for API endpoints"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract model from request
            data = request.get_json(silent=True) or {}
            model = data.get('model', 'default') if data else 'default'
            
            # Start timing
            start_time = time.time()
            
            try:
                # Execute the endpoint function
                response = func(*args, **kwargs)
                
                # Record metrics after successful execution
                status = response[1] if isinstance(response, tuple) else response.status_code if hasattr(response, 'status_code') else 200
                REQUEST_COUNT.labels(endpoint=endpoint_name, model=model, status=status).inc()
                REQUEST_LATENCY.labels(endpoint=endpoint_name, model=model).observe(time.time() - start_time)
                
                return response
            except Exception as e:
                # Record failure metrics
                REQUEST_COUNT.labels(endpoint=endpoint_name, model=model, status=500).inc()
                REQUEST_LATENCY.labels(endpoint=endpoint_name, model=model).observe(time.time() - start_time)
                # Re-raise the exception
                raise e
                
        return wrapper
    return decorator

def metrics_endpoint():
    """Handler for the /metrics endpoint"""
    metrics_token = os.environ.get('METRICS_TOKEN', 'default_secret_token')
    
    # Check for auth token in header
    auth_header = request.headers.get('Authorization')
    if not auth_header or auth_header != f'Bearer {metrics_token}':
        return Response("Access denied: Invalid or missing token", status=403)

    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
    return Response(generate_latest(registry), mimetype=CONTENT_TYPE_LATEST)



# Apply to app
app.view_functions['chat_completions'] = track_metrics('chat_completions')(app.view_functions['chat_completions'])
app.view_functions['completions'] = track_metrics('completions')(app.view_functions['completions'])
app.view_functions['embeddings'] = track_metrics('embeddings')(app.view_functions['embeddings'])
app.view_functions['models_list'] = track_metrics('models')(app.view_functions['models_list'])

app.add_url_rule('/metrics', 'metrics', metrics_endpoint)

prod_app = app