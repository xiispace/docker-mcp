FROM python:3.11-slim

WORKDIR /app

# Install Docker CLI and uv
RUN apt-get update && \
    apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release && \
    mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null && \
    apt-get update && \
    apt-get install -y docker-ce-cli && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -sSf https://astral.sh/uv/install.sh | sh

# Copy project files
COPY pyproject.toml .
# Install dependencies using uv
RUN uv pip install -e .

# Copy server code
COPY server.py .

# Make server.py executable
RUN chmod +x server.py

# Set environment variables
ENV MCP_TRANSPORT=sse
ENV MCP_PORT=3000
# Optional: Set authentication token (uncomment and set a secure token to enable authentication)
# ENV MCP_AUTH_TOKEN=your_secure_token_here

# Expose the port
EXPOSE 3000

# Run the server
CMD ["python", "server.py"]
