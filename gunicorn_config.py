import os
import shutil

# Worker-specific settings
workers = 1  
worker_class = 'gthread'
worker_connections = 1000
timeout = 240
keepalive = 30
preload_app = True  
    