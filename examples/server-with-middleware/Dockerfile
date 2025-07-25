FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies
RUN uv sync

# Copy source code
COPY . .

# Expose port
EXPOSE 8080

# Run the server
CMD ["uv", "run", "server.py"]
