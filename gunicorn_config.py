import os
import shutil

# Worker-specific settings
bind = "0.0.0.0:443"
workers = 8
worker_class = 'gthread'
worker_connections = 1000
timeout = 240
keepalive = 30
preload_app = True
certfile= 'myserver.crt'
keyfile='myserver.key'
    