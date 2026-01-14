"""Configuration models for emsipi using Pydantic.

This module defines the Pydantic models for the emsipi configuration
that follows the specification defined in specs/config.md.
"""

import logging
import re
import tomllib
from pathlib import Path
from typing import Any

import rich
import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from emsipi.printshop import WARNING_RICH_PREPEND

logger = logging.getLogger(__name__)


def _extract_python_version_from_uv_lock(working_dir: Path) -> str:
    """Extract Python version from uv.lock file.

    Args:
        working_dir: Working directory containing uv.lock

    Returns:
        str: Extracted Python version

    Raises:
        ValueError: If version cannot be extracted
    """
    uv_lock_path = working_dir / "uv.lock"
    if not uv_lock_path.exists():
        msg = "uv.lock file not found but was expected"
        raise ValueError(msg)

    try:
        with uv_lock_path.open(encoding="utf-8") as f:
            content = f.read()
            # Look for requires-python in uv.lock
            match = re.search(
                r'requires-python\s*=\s*["\\](["\\]*)["\\]', content
            )
            if match:
                version_spec = match.group(1)
                # Extract major.minor version (e.g., ">=3.11" -> "3.11")
                version_match = re.search(r"(\d+\.\d+)", version_spec)
                if version_match:
                    return version_match.group(1)
    except (OSError, UnicodeDecodeError) as e:
        rich.print(
            WARNING_RICH_PREPEND
            + f"Could not read uv.lock file for Python version: {e}"
        )

    msg = "Could not find requires-python key in uv.lock file"
    raise ValueError(msg)


def _extract_python_version_from_pyproject(working_dir: Path) -> str:
    """Extract Python version from pyproject.toml file.

    Args:
        working_dir: Working directory containing pyproject.toml

    Returns:
        str: Extracted Python version

    Raises:
        ValueError: If version cannot be extracted
    """
    pyproject_path = working_dir / "pyproject.toml"
    if not pyproject_path.exists():
        msg = "pyproject.toml file not found but was expected"
        raise ValueError(msg)

    try:
        with pyproject_path.open("rb") as f:
            data = tomllib.load(f)
            requires_python = data.get("project", {}).get("requires-python")  # pyright: ignore[reportAny]
            if requires_python:
                # Extract major.minor version (e.g., ">=3.11" -> "3.11")
                version_match = re.search(r"(\d+\.\d+)", requires_python)  # pyright: ignore[reportAny]
                if version_match:
                    return version_match.group(1)
    except (tomllib.TOMLDecodeError, OSError) as e:
        rich.print(
            WARNING_RICH_PREPEND
            + f"Could not parse pyproject.toml file for Python version: {e}"
        )

    msg = "Could not find project.requires-python key in pyproject.toml file"
    raise ValueError(msg)


def _detect_file_presence(working_dir: Path) -> dict[str, bool]:
    """Detect presence of various configuration files.

    Args:
        working_dir: The working directory to check

    Returns:
        dict[str, Any]: Dictionary of detection flags
    """
    detection_flags: dict[str, bool] = {}

    # Check Python configuration files
    uv_lock_path = working_dir / "uv.lock"
    detection_flags["uv_lock_present"] = uv_lock_path.exists()

    requirements_path = working_dir / "requirements.txt"
    detection_flags["requirements_txt_present"] = requirements_path.exists()

    pyproject_path = working_dir / "pyproject.toml"
    deps_in_pyproject = False
    if pyproject_path.exists():
        try:
            with pyproject_path.open("rb") as f:
                pyproject_data = tomllib.load(f)
                deps_in_pyproject = "dependencies" in pyproject_data or (
                    "project" in pyproject_data
                    and isinstance(pyproject_data["project"], dict)
                    and "dependencies" in pyproject_data["project"]
                )
        except (tomllib.TOMLDecodeError, OSError) as e:
            rich.print(
                WARNING_RICH_PREPEND
                + f"Could not read pyproject.toml file: {e}"
            )

    detection_flags["deps_in_pyproject"] = deps_in_pyproject

    any_python_config = (
        detection_flags["uv_lock_present"]
        or deps_in_pyproject
        or detection_flags["requirements_txt_present"]
    )
    detection_flags["any_python_config_file_present"] = any_python_config

    # Check Node configuration files
    package_json_path = working_dir / "package.json"
    detection_flags["package_json_present"] = package_json_path.exists()

    return detection_flags


class GoogleProviderConfig(BaseModel):
    """Configuration for Google Cloud Platform provider."""

    project: str = Field(
        ..., description="Google Cloud Platform (GCP) project ID"
    )
    artifact_registry: str | None = Field(
        default=None,
        description=(
            "Artifact Registry repository ID. If not provided, "
            "we will create a repository called '<server-name>-repo>' "
            "in the Artifact Registry."
        ),
    )
    region: str = Field(
        default="us-central1",
        description="GCP region where the resources will be created",
    )
    service_name: str | None = Field(
        default=None,
        description=(
            "Cloud Run service name. If not provided, "
            "defaults to the server name"
        ),
    )

    @field_validator("project")
    @classmethod
    def validate_project(cls, v: str) -> str:
        """Validate that project ID is not empty.

        Args:
            v: Project ID to validate

        Returns:
            str: Validated and stripped project ID

        Raises:
            ValueError: If project ID is empty or whitespace only
        """
        if not v or not v.strip():
            msg = "Project ID cannot be empty"
            raise ValueError(msg)
        return v.strip()

    @field_validator("region")
    @classmethod
    def validate_region(cls, v: str) -> str:
        """Validate that region is not empty.

        Args:
            v: Region to validate

        Returns:
            str: Validated and stripped region

        Raises:
            ValueError: If region is empty or whitespace only
        """
        if not v or not v.strip():
            msg = "Region cannot be empty"
            raise ValueError(msg)
        return v.strip()


class EmsipiConfig(BaseModel):
    """Main configuration model for emsipi deployments.

    Follows the specification defined in specs/config.md.
    """

    # External, explicit attributes
    server_name: str = Field(
        ..., alias="server-name", description="The name of the MCP server"
    )
    providers: dict[str, GoogleProviderConfig] = Field(
        ...,
        description="Configuration for cloud providers",
    )
    environment_variables: dict[str, str] | None = Field(
        default=None,
        alias="environment-variables",
        description=(
            "Environment variables that will be available to the MCP server"
        ),
    )

    # Server file or command (mutually exclusive)
    server_file: str | None = Field(
        default=None,
        alias="server-file",
        description="Path to the server file to run",
    )
    server_command: str | None = Field(
        default=None,
        alias="server-command",
        description="Command to run the server",
    )

    # Dockerfile configuration
    dockerfile: str = Field(
        default="./Dockerfile",
        description="Path to the Dockerfile",
    )

    # Runtime configuration with implicit detection
    raw_runtime: str = Field(
        default="auto",
        alias="runtime",
        description="Runtime type (python, node, auto)",
    )

    # Python configuration
    raw_python_dependencies_file: str = Field(
        default="auto",
        alias="python-dependencies-file",
        description="Python dependencies file path",
    )
    raw_python_version: str = Field(
        default="auto",
        alias="python-version",
        description="Python version to use",
    )

    # Node configuration
    run_npm_build: bool = Field(
        default=False,
        alias="run-npm-build",
        description="Whether to run npm build",
    )
    node_version: str | None = Field(
        default=None,
        alias="node-version",
        description="Node version to use",
    )

    # Internal attributes (never set by config files)
    working_directory: Path | None = Field(
        default=None,
        exclude=True,
        description="Working directory (internal)",
    )
    do_generate_config_files: bool = Field(
        default=False,
        exclude=True,
        description="Whether to generate config files (internal)",
    )
    do_generate_dockerfile: bool = Field(
        default=False,
        exclude=True,
        description="Whether to generate Dockerfile (internal)",
    )
    server_file_or_command: str | None = Field(
        default=None,
        exclude=True,
        description="Raw server file or command value (internal)",
    )
    is_server_file: bool = Field(
        default=True,
        exclude=True,
        description="True if server_file_or_command is a file path (internal)",
    )
    command_type: str | None = Field(
        default=None,
        exclude=True,
        description="Command type: python, node, shell (internal)",
    )

    # Detection attributes
    server_file_exists: bool = Field(
        default=False,
        exclude=True,
        description="Whether the server file exists (internal)",
    )
    uv_lock_present: bool = Field(
        default=False,
        exclude=True,
        description="Whether uv.lock is present (internal)",
    )
    deps_in_pyproject: bool = Field(
        default=False,
        exclude=True,
        description="Whether pyproject.toml has dependencies (internal)",
    )
    requirements_txt_present: bool = Field(
        default=False,
        exclude=True,
        description="Whether requirements.txt is present (internal)",
    )
    any_python_config_file_present: bool = Field(
        default=False,
        exclude=True,
        description="Whether any Python config file is present (internal)",
    )
    package_json_present: bool = Field(
        default=False,
        exclude=True,
        description="Whether package.json is present (internal)",
    )

    runtime: str = Field(
        default="auto",
        exclude=True,
        description="Detected runtime type",
    )
    python_dependencies_file: str = Field(
        default="auto",
        exclude=True,
        description="Detected Python dependencies file",
    )
    python_version: str = Field(
        default="auto",
        exclude=True,
        description="Detected Python version",
    )

    model_config: ConfigDict = ConfigDict(  # type: ignore[misc] # pyright: ignore[reportIncompatibleVariableOverride]
        populate_by_name=True,
        extra="forbid",
        # Allow using setattr for internal fields during validation
        frozen=False,
    )

    @field_validator("server_name")
    @classmethod
    def validate_server_name(cls, v: str) -> str:
        """Validate that server name follows naming conventions.

        Args:
            v: Server name to validate

        Returns:
            str: Validated and stripped server name

        Raises:
            ValueError: If server name is empty, whitespace only,
                        or invalid format
        """
        if not v or not v.strip():
            msg = "Server name cannot be empty"
            raise ValueError(msg)

        # Validate format: letters, digits, and dashes only
        clean_name = v.strip()
        if not re.match(r"^[a-zA-Z0-9-]+$", clean_name):
            msg = "Server name must contain only letters, digits, and dashes"
            raise ValueError(msg)

        return clean_name

    @field_validator("providers")
    @classmethod
    def validate_providers(
        cls,
        v: dict[str, Any],  # pyright: ignore[reportExplicitAny]
    ) -> dict[str, GoogleProviderConfig]:
        """Validate that at least one provider is configured.

        Args:
            v: Provider configurations to validate

        Returns:
            dict[str, GoogleProviderConfig]: Validated provider configurations

        Raises:
            ValueError: If no providers are configured
        """
        if not v:
            msg = "At least one provider must be configured"
            raise ValueError(msg)

        # Convert dict values to GoogleProviderConfig instances
        validated_providers: dict[str, GoogleProviderConfig] = {}
        for provider_name, provider_config in v.items():  # pyright: ignore[reportAny]
            if not isinstance(provider_config, GoogleProviderConfig):
                validated_config = GoogleProviderConfig(**provider_config)  # pyright: ignore[reportAny]
            else:
                validated_config = provider_config
            validated_providers[provider_name] = validated_config

        return validated_providers

    @field_validator("environment_variables")
    @classmethod
    def validate_environment_variables(
        cls,
        v: dict[str, Any] | None,  # pyright: ignore[reportExplicitAny]
    ) -> dict[str, str] | None:
        """Validate environment variables are strings.

        Args:
            v: Environment variables to validate

        Returns:
            dict[str, str] | None: Validated environment variables or None

        Raises:
            TypeError: If keys or values are not strings
        """
        if v is None:
            return None

        validated_vars: dict[str, str] = {}
        for key, value in v.items():  # pyright: ignore[reportAny]
            if not isinstance(value, str):
                msg = (
                    f"Environment variable value must be a string, "
                    f"got {type(value)}"  # pyright: ignore[reportAny]
                )
                raise TypeError(msg)
            validated_vars[key] = value

        return validated_vars

    @model_validator(mode="after")
    def validate_server_file_or_command(self) -> "EmsipiConfig":
        """Validate that exactly one of server_file or server_command is set.

        Returns:
            EmsipiConfig: Validated configuration instance

        Raises:
            ValueError: If validation fails
        """
        has_file = self.server_file is not None
        has_command = self.server_command is not None

        if not has_file and not has_command:
            msg = "Either 'server-file' or 'server-command' must be specified"
            raise ValueError(msg)

        if has_file and has_command:
            msg = "'server-file' and 'server-command' are mutually exclusive"
            raise ValueError(msg)

        # Set internal attributes
        if has_file:
            self.server_file_or_command = self.server_file
            self.is_server_file = True
            # Validate file extension (Step 2 specification)
            if self.server_file:
                if not (
                    self.server_file.endswith(".py")
                    or self.server_file.endswith(".js")
                ):
                    msg = "Server file must end with .py or .js"
                    raise ValueError(msg)
                # Check if file path is above working directory
                if self.working_directory and self.server_file:
                    server_path = Path(self.server_file)
                    if server_path.is_absolute():
                        try:
                            _ = server_path.relative_to(self.working_directory)
                        except ValueError:
                            msg = (
                                "Server file path cannot be above "
                                "the working directory"
                            )
                            raise ValueError(msg) from None
        else:
            self.server_file_or_command = self.server_command
            self.is_server_file = False

        return self

    @model_validator(mode="after")
    def detect_command_type_and_runtime(self) -> "EmsipiConfig":
        """Detect command type and set initial runtime.

        Returns:
            EmsipiConfig: Configuration with detected command type
        """
        if not self.is_server_file:
            # Command type (Step 4.1)
            self.command_type = "shell"
            self.raw_runtime = "auto"
        # File-based detection (Step 4.2)
        elif (
            self.server_file_or_command
            and self.server_file_or_command.endswith(".py")
        ):
            self.command_type = "python"
            if self.raw_runtime == "auto":
                self.raw_runtime = "python"
        elif (
            self.server_file_or_command
            and self.server_file_or_command.endswith(".js")
        ):
            self.command_type = "node"
            if self.raw_runtime == "auto":
                self.raw_runtime = "node"
        else:
            self.command_type = "shell"

        return self

    @model_validator(mode="after")
    def detect_files_and_compute_runtime(self) -> "EmsipiConfig":
        """Detect configuration files and compute runtime values.

        Returns:
            EmsipiConfig: Configuration with computed runtime values
        """
        # Skip if working directory not set yet
        if not self.working_directory:
            return self

        # Detect file presence
        detection_flags = _detect_file_presence(self.working_directory)
        for key, value in detection_flags.items():
            setattr(self, key, value)

        # Detect runtime
        self.runtime = self._detect_runtime()

        # Detect Python dependencies file if Python runtime
        if self.runtime == "python":
            self.python_dependencies_file = (
                self._detect_python_dependencies_file()
            )

            # Detect Python version
            self.python_version = self._detect_python_version()

        return self

    def _detect_runtime(self) -> str:
        """Detect runtime type based on configuration files.

        Returns:
            str: Detected runtime type

        Raises:
            ValueError: If runtime cannot be determined
        """
        if self.raw_runtime != "auto":
            return self.raw_runtime

        # Auto-detect runtime based on Step 5A specification
        if self.any_python_config_file_present:
            if self.package_json_present:
                msg = (
                    "Both Python and Node.js configuration files found. "
                    "Please specify 'runtime' as either 'python' or 'node'."
                )
                raise ValueError(msg)
            return "python"
        if self.package_json_present:
            return "node"
        msg = (
            "No runtime configuration files found. "
            f"Working directory: {self.working_directory}. "
            "Please add Python dependencies "
            "(uv.lock, pyproject.toml, requirements.txt) "
            "or Node.js configuration (package.json), "
            "or use the --directory argument "
            "to specify the correct working directory."
        )
        raise ValueError(msg)

    def _detect_python_dependencies_file(self) -> str:
        """Detect Python dependencies file based on presence flags.

        Returns:
            str: Python dependencies file path

        Raises:
            ValueError: If dependencies file cannot be determined
        """
        if self.raw_python_dependencies_file != "auto":
            return self.raw_python_dependencies_file

        if self.runtime != "python":
            msg = (
                "Python dependencies file can only be set "
                "when runtime is 'python'"
            )
            raise ValueError(msg)

        # Auto-detect dependencies file based on Step 5B specification
        if self.uv_lock_present:
            if self.requirements_txt_present:
                msg = WARNING_RICH_PREPEND + (
                    "Both uv.lock and requirements.txt found. "
                    "Using uv.lock, but requirements.txt will not be used."
                )
                rich.print(msg)
            return "uv.lock"
        if self.requirements_txt_present:
            if self.deps_in_pyproject:
                msg = WARNING_RICH_PREPEND + (
                    "Both requirements.txt and pyproject.toml "
                    "with dependencies found. "
                    "Using requirements.txt, "
                    "but pyproject.toml will not be used."
                )
                rich.print(msg)
            return "requirements.txt"
        if self.deps_in_pyproject:
            return "pyproject.toml"
        msg = (
            "No Python dependencies file found. "
            "Please create uv.lock, pyproject.toml with dependencies, "
            "or requirements.txt."
        )
        raise ValueError(msg)

    def _detect_python_version(self) -> str:
        """Detect Python version from dependencies file.

        Returns:
            str: Python version

        Raises:
            ValueError: If Python version cannot be determined
        """
        if self.raw_python_version != "auto":
            return self.raw_python_version

        if self.runtime != "python":
            msg = "Python version can only be set when runtime is 'python'"
            raise ValueError(msg)

        # Auto-detect Python version from dependencies file
        if not self.working_directory:
            return "3.11"  # Default fallback

        deps_file = self.python_dependencies_file
        if deps_file == "uv.lock":
            return _extract_python_version_from_uv_lock(self.working_directory)
        if deps_file == "pyproject.toml":
            return _extract_python_version_from_pyproject(
                self.working_directory
            )
        # requirements.txt
        msg = (
            "Cannot detect Python version from requirements.txt. "
            "Please specify 'python-version' in your configuration."
        )
        raise ValueError(msg)

    @model_validator(mode="after")
    def validate_node_configuration(self) -> "EmsipiConfig":
        """Validate Node.js configuration.

        Returns:
            EmsipiConfig: Configuration with validated Node.js settings

        Raises:
            ValueError: If Node.js configuration is invalid
        """
        # Skip validation if runtime not computed yet
        if not hasattr(self, "runtime") or self.runtime == "auto":
            return self

        if self.run_npm_build and self.runtime != "node":
            msg = "'run-npm-build' can only be set when runtime is 'node'"
            raise ValueError(msg)

        if self.node_version is not None and self.runtime != "node":
            msg = "'node-version' can only be set when runtime is 'node'"
            raise ValueError(msg)

        if self.runtime == "node" and self.node_version is None:
            # Set default Node version (Step 5C specification)
            self.node_version = "20"

        return self

    def get_provider_config(self, provider: str) -> GoogleProviderConfig:
        """Get configuration for a specific provider.

        Args:
            provider: Name of the provider

        Returns:
            GoogleProviderConfig: Provider configuration

        Raises:
            ValueError: If provider is not configured
        """
        if provider not in self.providers:
            msg = f"Provider '{provider}' not configured"
            raise ValueError(msg)
        return self.providers[provider]

    def get_default_provider(self) -> str:
        """Get the default provider (first configured provider).

        Returns:
            str: Name of the default provider

        Raises:
            ValueError: If no providers are configured
        """
        if not self.providers:
            msg = "No providers configured"
            raise ValueError(msg)
        return next(iter(self.providers.keys()))

    def detect_file_presence(self, working_dir: Path) -> None:
        """Detect presence of various configuration files.

        Args:
            working_dir: The working directory to check
        """
        # Set working directory
        self.working_directory = working_dir

        # Check server file existence
        if self.is_server_file and self.server_file_or_command:
            server_path = Path(self.server_file_or_command)
            if not server_path.is_absolute():
                server_path = working_dir / server_path
            self.server_file_exists = server_path.exists()

        # Run file detection and runtime computation
        detection_flags = _detect_file_presence(working_dir)
        for key, value in detection_flags.items():
            setattr(self, key, value)

        # Check Dockerfile (Step 3 specification)
        dockerfile_path = working_dir / self.dockerfile
        do_generate_dockerfile = False

        if not dockerfile_path.exists():
            do_generate_dockerfile = True
        else:
            try:
                with dockerfile_path.open(encoding="utf-8") as f:
                    first_line = f.readline().strip()
                    if "# OVERWRITE:OK" in first_line:
                        do_generate_dockerfile = True
            except (OSError, UnicodeDecodeError) as e:
                rich.print(
                    WARNING_RICH_PREPEND
                    + f"Could not read Dockerfile at {dockerfile_path}: {e}"
                )

        self.do_generate_dockerfile = do_generate_dockerfile


class EmsipiConfigLoader:
    """Loader for emsipi configuration files following specs/config.md."""

    def __init__(
        self, config_path: Path | None = None, working_dir: Path | None = None
    ) -> None:
        """Initialize the configuration loader.

        Args:
            config_path: Path to emsipi.yaml config file
            working_dir: Working directory (defaults to parent of config_path)
        """
        self.explicit_config_path: bool = config_path is not None
        self.config_path: Path = config_path or Path("emsipi.yaml")
        self.working_dir: Path = working_dir or self.config_path.parent

    def load_config(self) -> EmsipiConfig:
        """Load configuration following the parsing mechanism.

        Returns:
            EmsipiConfig: Validated configuration object

        Raises:
            ValueError: If configuration validation fails
            FileNotFoundError: If configuration file not found
        """
        # Check if config files exist (Detection of emsipi configuration files)
        if self.explicit_config_path:
            # Custom config path provided - use it directly
            main_config_path = self.config_path
            # Look for private config with same stem but .private.yaml extension
            private_config_path = self.config_path.with_suffix(".private.yaml")

            # If custom config path was provided but doesn't exist, raise
            # FileNotFoundError
            if not main_config_path.exists():
                msg = f"Configuration file not found: {main_config_path}"
                raise FileNotFoundError(msg)

        else:
            # Default naming convention
            private_config_path = self.working_dir / "emsipi.private.yaml"
            main_config_path = self.working_dir / "emsipi.yaml"

            # If no config files exist with default naming, trigger wizard mode
            if (
                not main_config_path.exists()
                and not private_config_path.exists()
            ):
                # Return a config with wizard mode enabled
                config = EmsipiConfig(
                    **{
                        "server-name": "placeholder",
                        "server-file": "placeholder.py",
                    },  # type: ignore[arg-type] # pyright: ignore[reportArgumentType]
                    providers={
                        "google": GoogleProviderConfig(
                            project="placeholder",
                            artifact_registry=None,
                            service_name=None,
                        )
                    },
                )
                config.do_generate_config_files = True
                config.detect_file_presence(self.working_dir)
                return config

        # Try to load main config file
        config_data: dict[str, Any] = {}  # pyright: ignore[reportExplicitAny]
        if main_config_path.exists():
            with main_config_path.open(encoding="utf-8") as f:
                loaded_config = yaml.safe_load(f)  # pyright: ignore[reportAny]
                config_data = loaded_config if loaded_config is not None else {}

        # Try to load private config file (Step 2 override behavior)
        if private_config_path.exists():
            with private_config_path.open(encoding="utf-8") as f:
                private_config = yaml.safe_load(f)  # pyright: ignore[reportAny]
                if private_config is not None:
                    # Deep merge private config over main config
                    config_data = self._deep_merge(
                        config_data,
                        private_config,  # pyright: ignore[reportAny]
                    )

        try:
            # Use Pydantic validation for comprehensive error reporting
            config = EmsipiConfig(**config_data)  # pyright: ignore[reportAny]
            # Detect file presence after creation (Step 5 detection)
            config.detect_file_presence(self.working_dir)
            return config  # noqa: TRY300
        except Exception as e:
            msg = f"Configuration validation failed: {e}"
            raise ValueError(msg) from e

    def _deep_merge(
        self,
        base: dict[str, Any],  # pyright: ignore[reportExplicitAny]
        override: dict[str, Any],  # pyright: ignore[reportExplicitAny]
    ) -> dict[str, Any]:  # pyright: ignore[reportExplicitAny]
        """Deep merge two dictionaries, with override values taking precedence.

        Args:
            base: Base dictionary
            override: Override dictionary

        Returns:
            dict[str, Any]: Merged dictionary
        """
        result = base.copy()
        for key, value in override.items():  # pyright: ignore[reportAny]
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._deep_merge(
                    result[key],  # pyright: ignore[reportAny]
                    value,  # pyright: ignore[reportUnknownArgumentType]
                )
            else:
                result[key] = value
        return result

    def should_run_wizard(self) -> bool:
        """Check if the configuration wizard should be run.

        Returns:
            bool: True if wizard should be run
        """
        main_config_path = self.working_dir / "emsipi.yaml"
        private_config_path = self.working_dir / "emsipi.private.yaml"
        return (
            not main_config_path.exists() and not private_config_path.exists()
        )
