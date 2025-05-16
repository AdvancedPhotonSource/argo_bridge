import os
import shutil

def on_starting(server):
    """Clear out old metrics files when starting up"""
    metrics_dir = os.environ.get('PROMETHEUS_MULTIPROC_DIR') or 'metrics'
    if os.path.exists(metrics_dir):
        for file in os.listdir(metrics_dir):
            file_path = os.path.join(metrics_dir, file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Error removing file {file_path}: {e}")
    else:
        os.makedirs(metrics_dir, exist_ok=True)

# Worker-specific settings
workers = 1  # Adjust based on your server's CPU cores
worker_class = 'gthread'
worker_connections = 1000
timeout = 60
keepalive = 5
    