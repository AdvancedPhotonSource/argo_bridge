import os
import shutil

# Worker-specific settings
bind = "0.0.0.0:443"
workers = 8
worker_class = 'gthread'
threads = 64
timeout = 600
keepalive = 75
preload_app = True
certfile= 'myserver.crt'
keyfile='myserver.key'
    