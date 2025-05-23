FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create and set permissions for metrics directory
RUN mkdir -p /app/metrics && chmod 777 /app/metrics

# Expose the port your bridge app uses
EXPOSE 80

# Command to run your application
CMD ["gunicorn", "--config", "gunicorn_config.py", "bridge_prod:prod_app"]