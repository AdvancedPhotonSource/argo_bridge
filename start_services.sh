#!/bin/bash

# Generate a random token if not provided
if [ -z "$METRICS_TOKEN" ]; then
  export METRICS_TOKEN=$(openssl rand -hex 16)
  echo "Generated random metrics token: $METRICS_TOKEN"
else
  echo "Using provided metrics token"
fi

# Export the token for docker-compose
export METRICS_TOKEN

# Generate the Prometheus configuration file with the actual token value
cat prometheus.yml.template | sed "s/METRICS_TOKEN_PLACEHOLDER/$METRICS_TOKEN/g" > prometheus.yml
echo "Generated Prometheus configuration with the actual token"

# Start the services
docker-compose up -d

echo "Services started with metrics security token"
echo "To access metrics directly, use: curl -H 'Authorization: Bearer $METRICS_TOKEN' http://localhost/metrics"
