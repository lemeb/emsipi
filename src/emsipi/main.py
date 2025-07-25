"""Main module for emsipi - FastMCP server deployment library.

Copyright (c) 2025 Leopold Mebazaa.
"""

import json
import logging
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, NoReturn

import rich
import typer

from emsipi.config.config import EmsipiConfig, ProvidersConfig
from emsipi.config.descriptions import DESCRIPTIONS
from emsipi.config.typeshed import PythonDepsFile, Runtime
from emsipi.logos import maxi

if TYPE_CHECKING:
    from emsipi.deployment.base import DeploymentProvider

logger = logging.getLogger(__name__)


# Custom exceptions for better error handling
class EmsipiValidationError(Exception):
    """Raised when validation fails."""


def _raise_validation_error(msg: str) -> NoReturn:
    """Raise a ValueError for validation failures.

    Args:
        msg: The error message

    Raises:
        ValueError: Always raised with the provided message
    """
    raise ValueError(msg)


class EmsipiDeploymentError(Exception):
    """Raised when deployment fails."""


def _raise_deployment_error(msg: str) -> NoReturn:
    """Raise a RuntimeError for deployment failures.

    Args:
        msg: The error message

    Raises:
        EmsipiDeploymentError: Always raised with the provided message
    """
    raise EmsipiDeploymentError(msg)


class EmsipiSynthesisError(Exception):
    """Raised when CDKTF synthesis fails."""


# Create the main typer app
app = typer.Typer(
    name="emsipi",
    help="Deploy FastMCP servers to cloud providers",
    add_completion=False,
    no_args_is_help=True,
    rich_markup_mode="rich",
)


# EmsipiConfig is now imported from .config module


class FastMCPValidator:
    """Validator for FastMCP server code."""

    def __init__(self, server_path: Path) -> None:
        """Initialize validator.

        Args:
            server_path: Path to the FastMCP server file
        """
        self.server_path: Path = server_path

    def validate(self) -> None:
        """Validate that the server file is a valid FastMCP server.

        Raises:
            FileNotFoundError: If server file doesn't exist
            EmsipiValidationError: If validation fails
        """
        if not self.server_path.exists():
            msg = f"Server file not found: {self.server_path}"
            raise FileNotFoundError(msg)

        # Check if file imports FastMCP
        try:
            with self.server_path.open(encoding="utf-8") as f:
                content = f.read()
                if (
                    "from fastmcp import FastMCP" not in content
                    and "import fastmcp" not in content
                ):
                    msg = "Server file does not import FastMCP"
                    _raise_validation_error(msg)

                # Check for FastMCP instance creation
                if "FastMCP(" not in content:
                    msg = "Server file does not create FastMCP instance"
                    _raise_validation_error(msg)

        except (FileNotFoundError, EmsipiValidationError):
            # Re-raise these specific exceptions
            raise
        except Exception as e:
            # Convert other exceptions to EmsipiValidationError
            msg = f"Validation failed: {e}"
            raise EmsipiValidationError(msg) from e


class DockerfileGenerator:
    """Generator for Dockerfile based on FastMCP server requirements."""

    def __init__(
        self,
        config: EmsipiConfig,
    ) -> None:
        """Initialize generator.

        Args:
            config: Emsipi configuration
        """
        self.config: EmsipiConfig = config

    def generate(self) -> None:
        """Generate Dockerfile for the MCP server."""
        match self.config.runtime:
            case Runtime.python:
                dockerfile_content = self._generate_python_dockerfile()
            case Runtime.node:
                dockerfile_content = self._generate_node_dockerfile()

        with self.config.dockerfile.open("w", encoding="utf-8") as f:
            _ = f.write(dockerfile_content)

        logger.info(f"Generated Dockerfile at {self.config.dockerfile}")

    def _generate_python_dockerfile(self) -> str:
        """Generate Dockerfile for Python projects.

        Returns:
            str: Dockerfile content
        """
        python_version = self.config.python_version
        python_deps_file = self.config.python_dependencies_file
        if python_version is None:
            msg = "Python version not found"
            raise ValueError(msg)
        if python_deps_file is None:
            msg = "Python dependencies file not found"
            raise ValueError(msg)

        files_to_copy: list[str] = []
        if self.config.uv_lock_present:
            files_to_copy.append("uv.lock")
        if self.config.deps_in_pyproject:
            files_to_copy.append("pyproject.toml")
        if self.config.requirements_txt_present:
            files_to_copy.append("requirements.txt")

        uv_sync_flag: str
        match python_deps_file:
            case PythonDepsFile.uvlock:
                uv_sync_flag = "--frozen"
            case PythonDepsFile.pyproject:
                uv_sync_flag = ""
            case PythonDepsFile.requirements:
                uv_sync_flag = "-r requirements.txt"

        server_file_or_command = self.config.clean_server_file_or_command
        cmd_args: list[str]
        if isinstance(server_file_or_command, Path):
            file_path_relative_to_workdir = (
                server_file_or_command.absolute().relative_to(
                    self.config.working_directory
                )
            )
            cmd_args = ["uv", "run", str(file_path_relative_to_workdir)]
        else:
            cmd_args = shlex.split(server_file_or_command)

        return f"""# OVERWRITE:OK
# Automatically generated by emsipi.

FROM python:{python_version}-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY {" ".join(files_to_copy)} ./

# Install dependencies
RUN uv sync {uv_sync_flag}

# Copy source code
COPY . .

# Expose port
EXPOSE 8080

# Run the server
CMD {cmd_args}
"""

    def _generate_node_dockerfile(self) -> str:
        """Generate Dockerfile for Node projects.

        Returns:
            str: Dockerfile content
        """
        node_version = self.config.node_version
        run_npm_build = self.config.run_npm_build
        if node_version is None:
            msg = "Node version not found"
            raise ValueError(msg)
        if run_npm_build is None:
            msg = "Provide a value for run_npm_build"
            raise ValueError(msg)

        cmd_args: list[str]
        if isinstance(self.config.clean_server_file_or_command, Path):
            file_path_relative_to_workdir = (
                self.config.clean_server_file_or_command.relative_to(
                    self.config.working_directory
                )
            )
            cmd_args = [
                "node",
                str(file_path_relative_to_workdir),
            ]
        else:
            cmd_args = shlex.split(self.config.clean_server_file_or_command)

        return f"""# OVERWRITE:OK
# Automatically generated by emsipi.

FROM node:{node_version}-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./

RUN npm install

COPY . .

{"RUN npm run build" if run_npm_build else ""}

FROM node:{node_version}-alpine AS runner

WORKDIR /app

COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/build ./build
COPY package.json ./

EXPOSE 8080

CMD {cmd_args}
"""


class EmsipiDeployer:
    """Main deployer class for FastMCP servers."""

    def __init__(self, config: EmsipiConfig) -> None:
        """Initialize deployer.

        Args:
            config: Emsipi configuration
        """
        self.config: EmsipiConfig = config
        # Generate Dockerfile if needed
        if self.config.do_generate_dockerfile:
            generator = DockerfileGenerator(self.config)
            generator.generate()

    def deploy(self) -> str:
        """Deploy MCP server to cloud provider.

        Returns:
            URL of the deployed service

        Raises:
            EmsipiValidationError: If the server file is not a valid server
        """
        logger.info(f"Deploying MCP server to {self.config.provider}...")

        if not self.config.server_file:
            msg = "No server file provided"
            raise EmsipiValidationError(msg)

        # Deploy using the provider factory
        return self._deploy_with_provider(self.config)

    @staticmethod
    def _deploy_with_provider(config: EmsipiConfig) -> str:
        """Deploy using the specified cloud provider.

        Args:
            config: Emsipi configuration

        Returns:
            URL of the deployed service

        Raises:
            EmsipiDeploymentError: If the deployment fails
        """
        provider_name = config.provider
        server_file_or_command = config.clean_server_file_or_command
        working_dir = config.working_directory
        runtime = config.runtime

        try:
            app_cmd = (
                f"emsipi synth-internal {provider_name} "
                f"{server_file_or_command} "
                f"--directory {working_dir.absolute()} "
                f"--runtime {runtime}"
            )

            cdktf_json_file = working_dir / "cdktf.json"
            if cdktf_json_file.exists():
                with cdktf_json_file.open(encoding="utf-8") as f:
                    cdktf_json = json.load(f)  # pyright: ignore[reportAny]
                    cdktf_json["app"] = app_cmd
                with cdktf_json_file.open("w", encoding="utf-8") as f:
                    json.dump(cdktf_json, f, indent=2)
            else:
                with cdktf_json_file.open("w", encoding="utf-8") as f:
                    json.dump(
                        {"app": app_cmd, "language": "python"}, f, indent=2
                    )

            # Actually run the CDKTF deployment
            logger.info("Running CDKTF deployment...")

            deploy_result = subprocess.run(
                [  # noqa: S607
                    "cdktf",
                    "deploy",
                    "--auto-approve",
                ],
                check=False,
                capture_output=False,
                text=True,
                cwd=working_dir.absolute(),
                timeout=1800,
                env=os.environ
                | {"JSII_SILENCE_WARNING_UNTESTED_NODE_VERSION": "1"},
            )

            if deploy_result.returncode != 0:
                stacks_dir = working_dir / "cdktf.out" / "stacks"
                all_stacks: list[str] = []
                if stacks_dir.exists():
                    all_stacks = [
                        (
                            f"- {stack_name.name}\t"
                            f"{(stacks_dir / stack_name.name).absolute()}"
                        )
                        for stack_name in stacks_dir.iterdir()
                        if stack_name.is_dir()
                    ]

                useful_info_msg = (
                    "USEFUL INFORMATION (give this to your LLM 😊):\n"
                    f"Server file or command: {server_file_or_command}\n"
                    f"Working directory: {working_dir.absolute()}\n"
                    f"Runtime: {runtime}\n"
                    f"Provider: {provider_name}\n"
                    f"Stacks (this is where you can find Terraform files):\n\t"
                    f"{'\n\t'.join(all_stacks)}"
                )

                exit_code = deploy_result.returncode
                msg = (
                    f"CDKTF deployment failed with exit code {exit_code}.\n\n"
                    f"{useful_info_msg}"
                )
                _raise_deployment_error(msg)

            # Since we're not capturing output, return a success message
            return "Deployment completed successfully"  # noqa: TRY300

        except EmsipiDeploymentError:
            # Re-raise deployment errors directly
            raise
        except Exception as e:
            # Convert other exceptions to deployment errors
            msg = f"Deployment failed: {e}"
            raise EmsipiDeploymentError(msg) from e


@app.command(name="deploy")
def deploy_command(
    provider: Annotated[
        str, typer.Argument(help="Cloud provider to deploy to.")
    ],
    server_file_or_command: Annotated[
        str,
        typer.Argument(help=DESCRIPTIONS["server_file_or_command"]),
    ],
    directory: Annotated[
        Path | None,
        typer.Option(help=DESCRIPTIONS["directory"]),
    ] = None,
    runtime: Annotated[
        str | None,
        typer.Option(help=DESCRIPTIONS["runtime"]),
    ] = None,
) -> None:
    """Deploy your MCP server to a cloud provider."""
    _ = sys.stdout.write(maxi)
    try:
        cfg = EmsipiConfig.create(
            provider=provider,
            server_file_or_command=server_file_or_command,
            directory=directory,
            runtime=runtime,
        )

        deployer = EmsipiDeployer(cfg)

        url = deployer.deploy()

        logger.info("Successfully deployed MCP server!")
        logger.info("Service URL: %s", url)

    except (
        EmsipiValidationError,
        EmsipiDeploymentError,
        EmsipiSynthesisError,
    ) as e:
        # Print error message without stack trace for custom exceptions
        logger.exception("Deployment failed")
        raise typer.Exit(1) from e
    except Exception as e:
        # For unexpected errors, log with stack trace
        logger.exception("Unexpected error during deployment")
        raise typer.Exit(1) from e


@app.command(name="synth-internal")
def synth_internal_command(
    provider: Annotated[
        str, typer.Argument(help="Cloud provider to deploy to.")
    ],
    server_file_or_command: Annotated[
        str,
        typer.Argument(help=DESCRIPTIONS["server_file_or_command"]),
    ],
    directory: Annotated[
        Path | None,
        typer.Option(help=DESCRIPTIONS["directory"]),
    ] = None,
    runtime: Annotated[
        str | None,
        typer.Option(help=DESCRIPTIONS["runtime"]),
    ] = None,
) -> None:
    """Synthesize CDKTF configuration without deploying."""
    try:
        cfg = EmsipiConfig.create(
            provider=provider,
            server_file_or_command=server_file_or_command,
            directory=directory,
            runtime=runtime,
        )

        _ = EmsipiDeployer(cfg)

        # Create provider instance and synthesize
        # We import here to avoid starting JSII too early.
        from .deployment import DeploymentFactory  # noqa: PLC0415

        provider_config: ProvidersConfig = cfg.providers[provider]
        provider_instance: DeploymentProvider[ProvidersConfig] = (  # pyright: ignore[reportUnknownVariableType]
            DeploymentFactory.create_provider(  # pyright: ignore[reportUnknownMemberType]
                provider, cfg, provider_config
            )
        )

        # Synthesize CDKTF configuration
        logger.info("Synthesizing CDKTF configuration...")
        try:
            _ = provider_instance.synth()
        except Exception as e:
            msg = f"CDKTF synthesis failed: {e}"
            raise EmsipiSynthesisError(msg) from e

        logger.info("Successfully synthesized CDKTF configuration!")

    except (
        EmsipiValidationError,
        EmsipiDeploymentError,
        EmsipiSynthesisError,
    ) as e:
        # Print error message without stack trace for custom exceptions
        logger.exception("Synthesis failed")
        raise typer.Exit(1) from e
    except Exception as e:
        # For unexpected errors, log with stack trace
        logger.exception("Unexpected error during synthesis")
        raise typer.Exit(1) from e


@app.command(name="internal-config", hidden=True)
def internal_config_command(
    provider: Annotated[
        str, typer.Argument(help="Cloud provider to deploy to.")
    ],
    server_file_or_command: Annotated[
        str | None,
        typer.Argument(help=DESCRIPTIONS["server_file_or_command"]),
    ],
    directory: Annotated[
        Path | None,
        typer.Option(help=DESCRIPTIONS["directory"]),
    ] = None,
    runtime: Annotated[
        str | None,
        typer.Option(help=DESCRIPTIONS["runtime"]),
    ] = None,
) -> None:
    """Internal command to generate configuration files."""
    cfg = EmsipiConfig.create(
        provider=provider,
        server_file_or_command=server_file_or_command,
        directory=directory,
        runtime=runtime,
    )

    if hasattr(sys, "ps1"):
        rich.print(cfg.model_dump_json(indent=2))
    else:
        _ = sys.stdout.write(cfg.model_dump_json(indent=2))


def main() -> None:
    """Main entry point for emsipi CLI."""
    logging.basicConfig(level=logging.INFO)
    app()


if __name__ == "__main__":
    main()
