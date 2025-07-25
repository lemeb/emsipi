"""Descriptions for the configuration fields."""

DESCRIPTIONS = {
    "server_name": (
        "The name of the server, used for identification. "
        "Many cloud resources will be derived from this name."
        " It must contain only letters, digits, and dashes."
    ),
    "runtime": (
        "The runtime environment for your server. This determines the base "
        "Docker image and dependency installation. Choose 'python' or 'node'."
    ),
    "python_dependencies_file": (
        "The file containing your Python dependencies. "
        "Choose 'uv.lock', 'pyproject.toml', or 'requirements.txt'."
    ),
    "python_version": (
        "The major Python version for your project (e.g., '3.11', '3.12'). "
        "This is used to select the correct base Docker image."
    ),
    "node_version": (
        "The major Node.js version for your project (e.g., '18', '20'). "
        "This is used to select the correct base Docker image."
    ),
    "run_npm_build": (
        "Whether to run `npm run build` during the Docker build. "
        "This is typically required for TypeScript projects or those with a "
        "frontend build step."
    ),
    "server_file_or_command": (
        "Path to the server file (.py or .js) or command to run the server "
        "(e.g. 'my-server-exe --arg value')."
    ),
    "directory": ("Working directory (defaults to current directory)."),
    "google.project": (
        "Google Cloud project ID. It should have the format 'project-id'."
    ),
    "google.region": ("Google Cloud region. Defaults to 'us-central1'."),
    "google.artifact_registry": (
        "Google Cloud Artifact Registry repository ID. Defaults to "
        "'{server-name}-repo'."
    ),
    "google.service_name": (
        "Google Cloud Run service name. Defaults to '{server-name}-service'."
    ),
}
