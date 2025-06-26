# Argo API Bridge

This project provides a compatibility layer that transforms OpenAI-style API requests into Argonne National Lab's Argo API format. It supports chat completions, text completions, and embeddings endpoints.


## Downstream Integration

Several tools have been tested with the bridge, including IDE integrations, web UI's, and python libraries. Setup guides for these tools tools are located in the [downstream_config.md](downstream_config.md). 


## Setup

### 1. Create Conda Environment

First, create a new conda environment with Python 3.12:

```bash
conda create -n argo_bridge python=3.12
conda activate argo_bridge
```

### 2. Install Requirements

Install the required Python packages using pip:

```bash
pip install -r requirements.txt
```

### 3. Run the Server

Start the server with default settings (port 7285):

```bash
python argo_bridge.py
```

## Configuration Options

The server supports the following command-line arguments:

- `--username`: Sets the **default** username for API requests when no API key is provided (default: 'ARGO_BRIDGE').
- `--port`: Set the port number for the server (default: 7285)
- `--dlog`: Enable debug-level logging (when set, logging is at DEBUG level; by default it is INFO level)

Example with custom settings:

```bash
python argo_bridge.py --username custom_user --port 8000 --dlog
```

## Authentication

The bridge now supports passing a username as an API key using the `Authorization` header, following the OpenAI format.

- **API Key**: The username can be passed as a bearer token.
- **Format**: `Authorization: Bearer <your_username>`

If no `Authorization` header is provided, the server will use the default username specified by the `--username` argument.

## Endpoints

The API exposes the following endpoints:

- **Chat Completions**: `/chat/completions` (POST)
- **Text (Legacy) Completions**: `/completions` (POST)
- **Embeddings**: `/embeddings` (POST)

## Supported Models

The server accepts both Argo and OpenAI model identifiers.

### Chat and Completion Models

- GPT-3.5: (`gpt35`, `gpt-3.5`)
- GPT-3.5 Large: (`gpt35large`)
- GPT-4: (`gpt4`, `gpt-4`)
- GPT-4 Large: (`gpt4large`)
- GPT-4 Turbo: (`gpt4turbo`, `gpt-4-turbo`)
- GPT-4o: (`gpt4o`, `gpt-4o`, `gpt-4o-mini`)
- GPT-4o Latest: (`gpt4olatest`, `gpt-4o-latest`)
- GPT-o1 Preview: (`gpto1preview`, `o1-preview`)
- GPT-o1 Mini: (`gpto1mini`, `o1-mini`, `o1mini`)
- GPT-o1: (`gpto1`, `o1`)
- GPT-o3 Mini: (`gpto3mini`, `o3-mini`, `o3mini`)
- GPT-o3: (`gpto3`)
- GPT-o4 Mini: (`gpto4mini`)
- GPT-4.1: (`gpt41`)
- GPT-4.1 Mini: (`gpt41mini`)
- GPT-4.1 Nano: (`gpt41nano`)
- Gemini 2.5 Pro: (`gemini25pro`)
- Gemini 2.5 Flash: (`gemini25flash`)
- Claude Opus 4: (`claudeopus4`)
- Claude Sonnet 4: (`claudesonnet4`)
- Claude Sonnet 3.7: (`claudesonnet37`)
- Claude Sonnet 3.5 v2: (`claudesonnet35v2`)

### Embedding Models

- v3small: (`text-embedding-3-small`, `v3small`)
- v3large: (`text-embedding-3-large`, `v3large`)
- ada002: (`text-embedding-ada-002`, `ada002`)

## Production Deployment
For personal use, the development server should be plenty, but if you wish to scale up, this project includes a `docker-compose.yaml` file to manage the following services:

- **argo_bridge**: The main application container, built using the provided `dockerfile`. It runs the Argo API bridge using Gunicorn.
- **prometheus**: A Prometheus container for collecting metrics from the `argo_bridge` service.
- **grafana**: A Grafana container for visualizing the metrics collected by Prometheus. It comes pre-configured with a dashboard for the Argo Bridge.

### Steps to run

- To run, first set the environment variable `METRICS_TOKEN` to an arbitrary string. 
- Then, copy the `prometheus.yml.template` to `prometheus.yml` replacing the bearer token to that string. 
- Currently the prod setup is configured for SSL and requires a `myserver.crt` and `myserver.key`. Either generate these, or change the gunicorn and prometheus service to http.
- Once that is in place, build and run the containers using the following command from the root of the project directory:

```bash
docker-compose up -d
```

This will start all services in detached mode.

- The Argo Bridge will be accessible on port 80 of the host machine.
- Prometheus will be accessible on `http://localhost:9090`.
- Grafana will be accessible on `http://localhost:3000`. The default credentials are `admin` / `admin_password`.

To stop the containers:

```bash
docker-compose down
```

### Manual Gunicorn Deployment (without Docker)

If you prefer to run the application with Gunicorn directly without Docker, you can use the following command:

`gunicorn --workers 4 --bind localhost:7285 argo_bridge:app`

## Testing

Run the test suite using unittest:

```bash
python -m unittest test_server.py
```
