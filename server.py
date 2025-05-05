#!/usr/bin/env python3
"""
MCP Server with Docker tools and resources.
This server provides tools for interacting with Docker containers and images.
Uses the docker-py library for Docker operations.
"""

import os
import json
import asyncio
import docker
from typing import List, Dict, Any, Optional, Union

from mcp.server.fastmcp import FastMCP, Context
from mcp.server.fastmcp.prompts import base

# Get authentication token from environment variable or use None (no authentication)
AUTH_TOKEN = os.environ.get("MCP_AUTH_TOKEN")

sse_path = "/sse/{token}" if AUTH_TOKEN else "/sse"

# Create an MCP server
mcp = FastMCP(
    "Docker MCP Server", port=os.environ.get("MCP_PORT", 8000), sse_path=sse_path
)

# Create a Docker client
docker_client = docker.from_env()


@mcp.tool()
async def docker_ps(all: bool = False) -> str:
    """
    List running Docker containers.

    Args:
        all: If True, show all containers (default shows just running)
    """
    try:
        containers = docker_client.containers.list(all=all)

        # Format the output similar to docker ps command
        header = "CONTAINER ID\tIMAGE\tCOMMAND\tCREATED\tSTATUS\tPORTS\tNAMES"
        container_lines = []

        for container in containers:
            # Get container details
            container_id = container.id[:12]  # Short ID
            image = (
                container.image.tags[0]
                if container.image.tags
                else container.image.id[:12]
            )
            command = (
                container.attrs.get("Config", {}).get("Cmd", [""])[0]
                if container.attrs.get("Config", {}).get("Cmd")
                else ""
            )
            created = container.attrs.get("Created", "")
            status = container.status
            ports = (
                " ".join(
                    [
                        f"{host_port}->{container_port}"
                        for container_port, host_ports in container.ports.items()
                        for host_port in host_ports
                    ]
                )
                if container.ports
                else ""
            )
            names = container.name

            container_lines.append(
                f"{container_id}\t{image}\t{command}\t{created}\t{status}\t{ports}\t{names}"
            )

        return header + "\n" + "\n".join(container_lines)
    except docker.errors.APIError as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def docker_images() -> str:
    """List available Docker images."""
    try:
        images = docker_client.images.list()

        # Format the output similar to docker images command
        header = "REPOSITORY\tTAG\tIMAGE ID\tCREATED\tSIZE"
        image_lines = []

        for image in images:
            # Get image details
            repo_tags = image.tags
            if not repo_tags:
                repo_tags = ["<none>:<none>"]

            for tag in repo_tags:
                if ":" in tag:
                    repo, tag_value = tag.split(":", 1)
                else:
                    repo, tag_value = tag, "<none>"

                image_id = image.id.split(":")[-1][:12]
                created = image.attrs.get("Created", "")
                size = image.attrs.get("Size", 0) // (1024 * 1024)  # Convert to MB

                image_lines.append(
                    f"{repo}\t{tag_value}\t{image_id}\t{created}\t{size}MB"
                )

        return header + "\n" + "\n".join(image_lines)
    except docker.errors.APIError as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def docker_inspect(container_id: str) -> str:
    """
    Return detailed information about a container.

    Args:
        container_id: ID or name of the container to inspect
    """
    try:
        container = docker_client.containers.get(container_id)
        return json.dumps(container.attrs, indent=2)
    except docker.errors.NotFound:
        return f"Error: No such container: {container_id}"
    except docker.errors.APIError as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def docker_run(
    image: str,
    command: Optional[str] = None,
    detach: bool = True,  # Default to detached mode for MCP server
    env_vars: Optional[Dict[str, str]] = None,
    ports: Optional[List[str]] = None,
    volumes: Optional[List[str]] = None,
    name: Optional[str] = None,
) -> str:
    """
    Run a Docker container.

    Args:
        image: Docker image to run
        command: Command to run in the container
        detach: Run container in background if True (default: True)
        env_vars: Environment variables as key-value pairs
        ports: Port mappings in various formats:
               - "host_port:container_port" (e.g. "8080:80")
               - "host_port:container_port/protocol" (e.g. "8080:80/tcp", "53:53/udp")
               - "container_port" (e.g. "80", container port only, host port auto-assigned)
               - "container_port/protocol" (e.g. "80/tcp", "53/udp")
        volumes: Volume mappings in various formats:
               - "host_path:container_path" (e.g. "/host/path:/container/path")
               - "host_path:container_path:mode" (e.g. "/host/path:/container/path:ro")
               - "named_volume:container_path" (e.g. "my_volume:/container/path")
               - "named_volume:container_path:mode" (e.g. "my_volume:/container/path:ro")
               - "volume_name" (e.g. "my_volume", container path will be the same)
        name: Name for the container
    """
    try:
        # Convert ports from list format to dict format for docker-py
        port_bindings = {}
        if ports:
            for port_mapping in ports:
                if ":" in port_mapping:
                    host_port, container_port = port_mapping.split(":", 1)
                    # Handle protocol specification (tcp/udp)
                    if "/" not in container_port:
                        # Default to TCP if no protocol is specified
                        container_port = f"{container_port}/tcp"
                    port_bindings[container_port] = host_port
                else:
                    # Handle case where only container port is specified
                    container_port = port_mapping
                    if "/" not in container_port:
                        container_port = f"{container_port}/tcp"
                    port_bindings[container_port] = None

        # Convert volumes from list format to dict format for docker-py
        volume_bindings = {}
        if volumes:
            for volume_mapping in volumes:
                # Handle different volume formats
                if ":" in volume_mapping:
                    # Format: host_path:container_path[:mode]
                    parts = volume_mapping.split(":")
                    host_path = parts[0]
                    container_path = parts[1]

                    # Handle different volume modes
                    if len(parts) > 2:
                        # Explicit mode specified (ro, rw, z, Z, etc.)
                        mode = parts[2]
                    else:
                        # Default to read-write
                        mode = "rw"

                    # Both named volumes and bind mounts use the same format for docker-py
                    # The Docker daemon will determine if it's a named volume or bind mount
                    volume_bindings[host_path] = {
                        "bind": container_path,
                        "mode": mode,
                    }
                else:
                    # Format: volume_name (anonymous volume with container path)
                    # For anonymous volumes, Docker assigns a random name
                    # For named volumes without container path, Docker uses the volume name as the container path
                    volume_bindings[volume_mapping] = {
                        "bind": volume_mapping,
                        "mode": "rw",
                    }

        # Run the container
        container = docker_client.containers.run(
            image=image,
            command=command,
            detach=detach,
            environment=env_vars,
            ports=port_bindings,
            volumes=volume_bindings,
            name=name,
        )

        if detach:
            return f"Container started: {container.id[:12]}"
        else:
            return container.logs().decode("utf-8")
    except docker.errors.ImageNotFound:
        return f"Error: Image not found: {image}"
    except docker.errors.APIError as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def docker_stop(container_id: str) -> str:
    """
    Stop a running container.

    Args:
        container_id: ID or name of the container to stop
    """
    try:
        container = docker_client.containers.get(container_id)
        container.stop()
        return f"Container {container_id} stopped"
    except docker.errors.NotFound:
        return f"Error: No such container: {container_id}"
    except docker.errors.APIError as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def docker_rm(container_id: str, force: bool = False) -> str:
    """
    Remove a container.

    Args:
        container_id: ID or name of the container to remove
        force: Force removal of running container
    """
    try:
        container = docker_client.containers.get(container_id)
        container.remove(force=force)
        return f"Container {container_id} removed"
    except docker.errors.NotFound:
        return f"Error: No such container: {container_id}"
    except docker.errors.APIError as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def docker_logs(container_id: str, tail: Optional[int] = None) -> str:
    """
    Fetch the logs of a container.

    Args:
        container_id: ID or name of the container
        tail: Number of lines to show from the end of the logs
    """
    try:
        container = docker_client.containers.get(container_id)
        logs = container.logs(tail=tail).decode("utf-8")
        return logs if logs else "No logs available"
    except docker.errors.NotFound:
        return f"Error: No such container: {container_id}"
    except docker.errors.APIError as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def docker_pull(image: str) -> str:
    """
    Pull a Docker image.

    Args:
        image: Image to pull (e.g., "ubuntu:latest")
    """
    try:
        image_obj = docker_client.images.pull(image)
        return f"Successfully pulled image: {image} (ID: {image_obj.id[:12]})"
    except docker.errors.APIError as e:
        return f"Error: {str(e)}"


@mcp.resource("docker://containers")
async def get_containers() -> str:
    """Get information about all containers as a resource."""
    try:
        containers = docker_client.containers.list(all=True)
        container_data = []

        for container in containers:
            container_data.append(
                {
                    "id": container.id,
                    "name": container.name,
                    "image": (
                        container.image.tags[0]
                        if container.image.tags
                        else container.image.id
                    ),
                    "status": container.status,
                    "created": container.attrs.get("Created"),
                    "ports": container.ports,
                    "command": container.attrs.get("Config", {}).get("Cmd"),
                }
            )

        return json.dumps(container_data, indent=2)
    except docker.errors.APIError as e:
        return f"Error: {str(e)}"


@mcp.resource("docker://images")
async def get_images() -> str:
    """Get information about all images as a resource."""
    try:
        images = docker_client.images.list()
        image_data = []

        for image in images:
            image_data.append(
                {
                    "id": image.id,
                    "tags": image.tags,
                    "created": image.attrs.get("Created"),
                    "size": image.attrs.get("Size"),
                    "labels": image.labels,
                }
            )

        return json.dumps(image_data, indent=2)
    except docker.errors.APIError as e:
        return f"Error: {str(e)}"


@mcp.resource("docker://container/{container_id}")
async def get_container_info(container_id: str) -> str:
    """
    Get detailed information about a specific container.

    Args:
        container_id: ID or name of the container
    """
    try:
        container = docker_client.containers.get(container_id)
        return json.dumps(container.attrs, indent=2)
    except docker.errors.NotFound:
        return f"Error: No such container: {container_id}"
    except docker.errors.APIError as e:
        return f"Error: {str(e)}"


@mcp.prompt()
def docker_help() -> str:
    """Create a prompt for Docker help."""
    return """
    I can help you manage Docker containers and images. Here are some things you can ask me to do:

    - List running containers
    - Show all Docker images
    - Run a new container
    - Stop or remove containers
    - View container logs
    - Pull Docker images

    What would you like to do with Docker today?
    """


if __name__ == "__main__":
    if os.environ.get("MCP_PORT"):
        transport = "sse"
    else:
        transport = "stdio"
    mcp.run(transport=transport)
