FROM python:3.11-slim-bookworm

# Set environment variables for uv
ENV UV_LINK_MODE=copy
ENV UV_COMPILE_BYTECODE=1

WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH"

# Install Docker CLI
RUN apt-get update && \
    apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release && \
    mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null && \
    apt-get update && \
    apt-get install -y docker-ce-cli && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install uv using the official method
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy project files and install dependencies
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-install-project

# Copy server code
COPY server.py .

# Set environment variables
# ENV MCP_PORT=3000
# Optional: Set authentication token (uncomment and set a secure token to enable authentication)
# ENV MCP_AUTH_TOKEN=your_secure_token_here
# Optional: Set hostname for Docker containers (default: localhost if not set)
# ENV MCP_HOSTNAME=localhost
# Optional: Set available ports for Docker containers (comma-separated list of ports or port ranges)
# Example: "8000,8080-8090,9000"
# ENV MCP_AVAILABLE_PORTS=3001-3010,8080-8090,9000


# Run the server using the virtual environment's Python
CMD ["python", "server.py"]
