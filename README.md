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
# Run server without token authentication
docker run -d -p 3000:3000 -v /var/run/docker.sock:/var/run/docker.sock --name mcp-docker-server mcp-docker-server

# Run server with token authentication
docker run -d -p 3000:3000 -v /var/run/docker.sock:/var/run/docker.sock -e MCP_AUTH_TOKEN=your_secret_token --name mcp-docker-server mcp-docker-server
```

When the `MCP_AUTH_TOKEN` environment variable is set, the server will enable token authentication. Clients need to access the server through the `/sse/your_secret_token` path. If the token doesn't match or is not provided, the connection will be rejected.

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
uv run server.py
```

## Configuration

The server can be configured using environment variables:

- `MCP_TRANSPORT`: Transport method (default: `sse`)
- `MCP_PORT`: Port to listen on (default: `3000`)

## Using with Claude Desktop

Add the following configuration to your `claude_desktop_config.json` file:

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

## Using with VS Code

Add the following configuration to your VS Code settings or `.vscode/mcp.json` file:

```json
{
  "mcp": {
    "servers": {
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

## TODO

- Add functionality to query documentation for a specific Docker image

## License

MIT
