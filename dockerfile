FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the port your bridge app uses
EXPOSE 80

# Command to run your application
CMD ["gunicorn", "--workers", "16", "--bind", "0.0.0.0:80", "--config", "gunicorn_config.py", "argo_bridge:app"]