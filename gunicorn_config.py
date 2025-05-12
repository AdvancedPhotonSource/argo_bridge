import os
import shutil

def on_starting(server):
    metrics_dir = os.environ.get('PROMETHEUS_MULTIPROC_DIR') or 'metrics'
    