# Gunicorn production entry
# Usage: gunicorn -c gunicorn.conf.py src.main:app

import os

bind = f"0.0.0.0:{os.getenv('PORT', '8081')}"
worker_class = "uvicorn.workers.UvicornWorker"
workers = int(os.getenv("WEB_CONCURRENCY", "2"))
timeout = 60
keepalive = 5
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info").lower()
preload_app = True
