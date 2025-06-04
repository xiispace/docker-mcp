# Docker MCP Server

This is a Model Context Protocol (MCP) server that provides tools and resources for interacting with Docker containers and images. It uses the stream HTTP transport method for communication and the Python Docker SDK (docker-py) for Docker operations.

## Features

- List Docker containers and images
- Run, stop, and remove containers
- View container logs
- Pull Docker images
- Inspect container details
- Access Docker information as resources

## Prerequisites

- Docker
- Docker Compose (optional, for easier deployment)
- uv (for local development)

## Getting Started

### Running with Docker Compose

1. Clone this repository
2. Build and start the server:

```bash
docker-compose up -d
```

### Running with Docker directly

1. Build the Docker image:

```bash
docker build -t mcp-docker-server .
```

2. Run the container:

```bash
# Run server with SSE transport (no authentication)
docker run -d -p 3000:3000 -v /var/run/docker.sock:/var/run/docker.sock -e MCP_PORT=3000 --name mcp-docker-server mcp-docker-server

# Run server with SSE transport and token authentication
docker run -d -p 3000:3000 -v /var/run/docker.sock:/var/run/docker.sock -e MCP_PORT=3000 -e MCP_AUTH_TOKEN=your_secret_token --name mcp-docker-server mcp-docker-server
```

When the `MCP_PORT` environment variable is set, the server will use the SSE transport instead of stdio. Authentication is only applicable when using SSE transport. If the `MCP_AUTH_TOKEN` environment variable is set, the server will enable token authentication and configure the SSE endpoint to use the format `/sse/{token}` where `{token}` must match the value set in `MCP_AUTH_TOKEN`. If the token doesn't match or is not provided, the connection will be rejected. If no token is set, the server uses the standard `/sse` endpoint without authentication.

### Running locally (development)

1. Install uv (if not already installed):

```bash
curl -sSf https://astral.sh/uv/install.sh | sh
```

2. Install dependencies using uv:

```bash
uv sync
```

3. Run the server:

```bash
# Run with stdio transport (default)
uv run server.py

# Run with SSE transport on port 8000
MCP_PORT=8000 uv run server.py

# Run with SSE transport and token authentication
MCP_PORT=8000 MCP_AUTH_TOKEN=your_secret_token uv run server.py
```

## Configuration

The server can be configured using environment variables:

- `MCP_PORT`: When set, enables SSE transport mode and specifies the port to listen on (default: `8000`). If not set, the server will use stdio transport.
- `MCP_AUTH_TOKEN`: Secret token for authentication (only applicable when using SSE transport). When set, the SSE endpoint will be `/sse/{token}` instead of `/sse`
- `MCP_HOSTNAME`: Hostname to use for Docker containers (default: `localhost`). This can be a domain name or IP address that will be used to access Docker containers after they are created.
- `MCP_AVAILABLE_PORTS`: Comma-separated list of ports or port ranges that are available for Docker containers to bind to (e.g., `8000,8080-8090,9000`). When specified, the server will validate that requested host ports are in this list.

## Using with MCP clients

Should build the docker image first.

```json
{
  "mcpServers": {
    "docker": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-v",
        "/var/run/docker.sock:/var/run/docker.sock",
        "mcp-docker-server"
      ]
    }
  }
}
```

## Available Tools

- `docker_ps`: List running containers
- `docker_images`: List available Docker images
- `docker_inspect`: Get detailed information about a container
- `docker_run`: Run a Docker container
- `docker_stop`: Stop a running container
- `docker_rm`: Remove a container
- `docker_logs`: Fetch container logs
- `docker_pull`: Pull a Docker image

## Available Resources

- `docker://containers`: Information about all containers
- `docker://images`: Information about all images
- `docker://container/{container_id}`: Detailed information about a specific container
- `docker://config/hostname`: Get the configured hostname for Docker containers
- `docker://config/available_ports`: Get the list of available ports for Docker containers

## TODO

- Add functionality to query documentation for a specific Docker image

## License

MIT
