"""Configuration model for Emsipi with wrap validators."""

# pyright: reportImplicitStringConcatenation=false
# pyright: reportUnusedCallResult=false
from __future__ import annotations

import contextlib
import os
import re
import tomllib
from pathlib import Path
from typing import Any, cast

import rich
import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    ValidationInfo,
    ValidatorFunctionWrapHandler,
    computed_field,
    field_serializer,
    field_validator,
    model_validator,
)
from rich.console import Console
from rich.prompt import Confirm

from .descriptions import DESCRIPTIONS
from .typeshed import CommandType, CustomPrompt, PythonDepsFile, Runtime
from .utils import infer_python_deps, infer_python_version, infer_runtime


class GoogleProviderConfig(BaseModel):
    """Configuration for Google Cloud Platform provider."""

    project: str = Field(
        ..., description="Google Cloud Platform (GCP) project ID"
    )
    artifact_registry: str = Field(
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
    service_name: str = Field(
        description=(
            "Cloud Run service name. If not provided, "
            "defaults to the server name and '-service' suffix."
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


ProvidersConfig = GoogleProviderConfig


class EmsipiConfig(BaseModel):
    """Configuration model using wrap validators for inference."""

    model_config: ConfigDict = ConfigDict(  # type: ignore[misc] # pyright: ignore[reportIncompatibleVariableOverride]
        extra="forbid", validate_assignment=True
    )

    working_directory: Path = Field(
        default_factory=Path.cwd,
        description="Base working directory (internal).",
    )

    provider: str = Field(
        default="auto",
        description="Cloud provider to deploy to.",
        exclude=True,
    )

    # Detection booleans (populated early)
    server_file_exists: bool
    uv_lock_present: bool
    deps_in_pyproject: bool
    requirements_txt_present: bool
    any_python_config_file_present: bool
    package_json_present: bool
    dockerfile: Path = Field(
        default=Path("./Dockerfile"),
        description="Dockerfile path (may be generated).",
        alias="dockerfile",
    )
    do_generate_dockerfile: bool
    do_generate_config_files: bool

    # ---------------- Raw & basic inputs ----------------
    server_name: str | None = Field(
        default=None,
        description=DESCRIPTIONS["server_name"],
        alias="server-name",
        validate_default=True,
    )

    server_file_or_command: str = Field(
        description="Path to server file or command "
        "(exclusive with server_file and server_command)."
        "Can only be provided in the CLI.",
    )
    # Inferred fields
    command_type: CommandType | None = Field(
        default=None, validate_default=True, alias="command-type"
    )
    server_command: str | None = Field(
        default=None,
        description="Shell command to run server (exclusive with server_file).",
        alias="server-command",
        validate_default=True,
    )
    server_file: Path | None = Field(
        default=None,
        description="Path to server file (.py or .js).",
        alias="server-file",
        validate_default=True,
    )
    raw_runtime: str | None = Field(
        default=None,
        description="Raw runtime: python | node | auto | null.",
        alias="runtime",
        validate_default=True,
    )

    providers: dict[str, GoogleProviderConfig] = Field(
        default_factory=dict,
        description="Cloud provider configurations.",
    )

    runtime: Runtime = Field(default_factory=infer_runtime)

    # Python deps file (raw + inferred)
    raw_python_dependencies_file: str | None = Field(
        default=None,
        alias="python-dependencies-file",
        description=(
            "Raw deps file: auto | requirements.txt | pyproject.toml | uv.lock."
        ),
        validate_default=True,
    )
    python_dependencies_file: PythonDepsFile | None = Field(
        default_factory=infer_python_deps,
        validate_default=True,
    )

    # Python version (raw + inferred)
    raw_python_version: str | None = Field(
        default=None,
        alias="python-version",
        description="Raw python version: auto | <version>.",
        validate_default=True,
    )
    python_version: str | None = Field(
        default_factory=infer_python_version,
        validate_default=True,
    )

    # Node specifics
    node_version: str | float | None = Field(
        default=None,
        alias="node-version",
        description="Node major version (needed if runtime node).",
        validate_default=True,
    )
    run_npm_build: bool | None = Field(
        default=None,
        alias="run-npm-build",
        description="Whether to run npm run build (node only).",
        validate_default=True,
    )

    environment_variables: dict[str, str] | None = Field(
        default=None,
        description="Environment variables to set.",
        alias="environment-variables",
        validate_default=True,
    )

    @classmethod
    def _deep_merge(
        cls,
        a: dict[str, Any],  # pyright: ignore[reportExplicitAny]
        b: dict[str, Any],  # pyright: ignore[reportExplicitAny]
    ) -> dict[str, Any]:  # pyright: ignore[reportExplicitAny]
        """Deep merge two dictionaries.

        Args:
            a: First dictionary.
            b: Second dictionary.

        Returns:
            dict[str, Any]: Merged dictionary.
        """
        for key, value in b.items():  # pyright: ignore[reportAny]
            if (
                key in a
                and isinstance(a[key], dict)
                and isinstance(value, dict)
            ):
                value = cast(
                    "dict[str, Any]",  # pyright: ignore[reportExplicitAny]
                    value,
                )
                a[key] = cls._deep_merge(a[key], value)  # pyright: ignore[reportAny]
            else:
                a[key] = value
        return a

    @classmethod
    def _deep_remove_none_values(cls, data: dict[str, Any]) -> dict[str, Any]:  # pyright: ignore[reportExplicitAny]
        """Remove None values from a dictionary.

        Args:
            data: Dictionary to remove None values from.

        Returns:
            dict[str, Any]: Dictionary with None values removed.
        """
        copy = data.copy()
        for key, value in data.items():  # pyright: ignore[reportAny]
            if value is None:
                del copy[key]
            elif isinstance(value, dict):
                copy[key] = cls._deep_remove_none_values(value)  # pyright: ignore[reportUnknownArgumentType]
        return copy

    @classmethod
    def _parse_yaml_files(cls, wd: Path) -> dict[str, Any]:  # pyright: ignore[reportExplicitAny]
        """Parse the YAML files.

        Args:
            wd: Working directory.

        Returns:
            Merged data from the YAML files.
        """
        public_yaml = wd / "emsipi.yaml"
        private_yaml = wd / "emsipi.private.yaml"
        public_yaml_data = {}
        private_yaml_data = {}
        if public_yaml.is_file():
            public_yaml_data = cast(
                "dict[str, Any]",  # pyright: ignore[reportExplicitAny]
                yaml.safe_load(public_yaml.read_text(encoding="utf-8")),
            )
        if private_yaml.is_file():
            private_yaml_data = cast(
                "dict[str, Any]",  # pyright: ignore[reportExplicitAny]
                yaml.safe_load(private_yaml.read_text(encoding="utf-8")),
            )
        return cls._deep_merge(public_yaml_data, private_yaml_data)

    @classmethod
    def _probe_environment(
        cls,
        provider: str,
        server_file_or_command: str | None = None,
        directory: Path | None = None,
        runtime: str | None = None,
    ) -> dict[str, Any]:  # pyright: ignore[reportExplicitAny]
        """Probe the environment and populate detection fields.

        This is called BEFORE model creation to ensure all fields
        are available during validation.

        Args:
            provider: Cloud provider to deploy to.
            server_file_or_command: Path to the server file or command.
            directory: Working directory. Defaults to current directory.
            runtime: Runtime to use. Can be 'python', 'node', or 'auto'.

        Returns:
            Modified data with probe results
        """
        wd = Path(directory).resolve() if directory else Path.cwd().resolve()
        data: dict[str, Any] = {  # pyright: ignore[reportExplicitAny]
            "working_directory": wd,
            "provider": provider,
            "server_file_or_command": server_file_or_command,
            "runtime": runtime,
        }

        # Config files (presence)
        public_yaml = wd / "emsipi.yaml"
        private_yaml = wd / "emsipi.private.yaml"
        data["do_generate_config_files"] = not (
            public_yaml.is_file() or private_yaml.is_file()
        )

        # Parse the YAML files
        data.update(cls._parse_yaml_files(wd))

        # Dockerfile resolution
        raw_df = cast("Path", data.get("dockerfile", Path("./Dockerfile")))
        df_path = Path(raw_df)
        if not df_path.is_absolute():
            df_path = (wd / df_path).resolve()
        data["dockerfile"] = df_path
        if df_path.exists():
            first_line = ""
            with contextlib.suppress(Exception):
                first_line = df_path.read_text(encoding="utf-8").splitlines()[0]
            data["do_generate_dockerfile"] = "# OVERWRITE:OK" in first_line
        else:
            data["do_generate_dockerfile"] = True

        # Server file existence
        sf = cast("Path", data.get("server_file"))
        server_file_exists = False
        if sf:
            candidate = Path(sf)
            if not candidate.is_absolute():
                candidate = (wd / candidate).resolve()
            server_file_exists = candidate.exists()
        data["server_file_exists"] = server_file_exists

        # Dependency indicators
        uv_lock = (wd / "uv.lock").is_file()
        reqs = (wd / "requirements.txt").is_file()
        deps_in_pyproject = False
        pyproject = wd / "pyproject.toml"
        if pyproject.is_file():
            with contextlib.suppress(Exception):
                parsed = tomllib.loads(pyproject.read_text(encoding="utf-8"))
                deps_in_pyproject = bool(
                    parsed.get("project", {}).get("dependencies")  # pyright: ignore[reportAny]
                )

        package_json = (wd / "package.json").is_file()

        data["uv_lock_present"] = uv_lock
        data["requirements_txt_present"] = reqs
        data["deps_in_pyproject"] = deps_in_pyproject
        data["any_python_config_file_present"] = any(
            (uv_lock, reqs, deps_in_pyproject)
        )
        data["package_json_present"] = package_json

        return cls._deep_remove_none_values(data)

    @classmethod
    def create(
        cls,
        provider: str,
        server_file_or_command: str | None = None,
        directory: Path | None = None,
        runtime: str | None = None,
    ) -> EmsipiConfig:
        """Factory method to create EmsipiConfig with proper probing.

        Args:
            provider: Cloud provider to deploy to.
            server_file_or_command: Path to the server file or command.
            directory: Working directory.
            runtime: Runtime to use. Can be 'python', 'node', or 'auto'.
            **kwargs: Additional configuration data from files.

        Returns:
            Validated EmsipiConfig instance
        """
        # Probe environment first
        probed_data = cls._probe_environment(
            provider,
            server_file_or_command,
            directory,
            runtime,
        )
        # Create instance with probed data
        return cls.model_validate(probed_data)

    # --------------- Wrap validators ---------------

    @field_validator("server_name", mode="wrap")
    @classmethod
    def _validate_server_name(
        cls,
        value: str | None,
        handler: ValidatorFunctionWrapHandler,
        info: ValidationInfo,
    ) -> str | None:
        """Validate and prompt for server name.

        Args:
            value: Raw server_name string.
            handler: Inner validator handler.
            info: Validation context.

        Returns:
            str | None: Validated server name.

        Raises:
            ValueError: If server name format is invalid.
        """
        regex = r"^[a-zA-Z0-9-]{3,}$"
        console = Console()
        final_value: str | None = value
        wizard_output = (
            "[bold blue]server_name[/bold blue] " + DESCRIPTIONS["server_name"]
        )

        # Check if we need to prompt (when do_generate_config_files is True)
        do_generate = cast(
            "bool", info.data.get("do_generate_config_files", False)
        )
        user_made_choice = False

        if final_value is None and do_generate:  # pragma: no cover
            final_value = CustomPrompt.ask(
                wizard_output,
                console=console,
            )
            user_made_choice = True
        elif final_value is None:
            msg = "server_name is required but not provided."
            raise ValueError(msg)

        # final_value is str now
        if not bool(re.fullmatch(regex, final_value)):
            msg = (
                "server_name must be at least 3 characters"
                " and contain only letters, digits, and dashes. "
                f"Got: {final_value}"
            )
            raise ValueError(msg)

        # Even if we have a value, prompt in wizard mode to confirm
        if (
            do_generate and final_value and not user_made_choice
        ):  # pragma: no cover
            confirmed_value = CustomPrompt.ask(
                f"{wizard_output} (detected: {final_value})",
                default=final_value,
                console=console,
            )
            if confirmed_value != final_value:
                final_value = confirmed_value
                # Re-validate the new value
                if not re.fullmatch(regex, final_value):
                    msg = (
                        "server_name must be at least three characters and "
                        "contain only letters, digits, and dashes. "
                        f"Got: {final_value}"
                    )
                    raise ValueError(msg)

        return cast("str | None", handler(final_value))

    @field_validator("server_file", mode="wrap")
    @classmethod
    def _validate_server_file(
        cls,
        value: str | None,
        handler: ValidatorFunctionWrapHandler,
        info: ValidationInfo,
    ) -> str | None:
        """Validate mutual exclusivity & file constraints.

        Args:
            value: Raw server_file string.
            handler: Inner validator handler.
            info: Validation context.

        Returns:
            str | None: Validated value or None.

        Raises:
            ValueError: If mutually exclusive, outside working dir, or bad ext.
        """
        final_value: str | None = value or info.data.get("server_file")
        server_command: str | None = info.data.get("server_command")
        if (server_command is None) and (
            sfc := info.data.get("server_file_or_command")
        ):
            server_file, server_command = (
                cls._distinguish_server_file_or_command(sfc)  # pyright: ignore[reportAny]
            )
            final_value = str(server_file) if server_file else None
        if final_value is not None:
            if server_command is not None:
                msg = (
                    "server_file and server_command are mutually exclusive. "
                    "Please provide only one."
                )
                raise ValueError(msg)
            wd = cast("Path", info.data["working_directory"])
            p = Path(final_value)
            if not p.is_absolute():
                p = (wd / p).resolve()
            try:
                _ = p.relative_to(wd)
            except ValueError:
                msg = (
                    "server_file must reside within working_directory. "
                    f"Got {p} outside {wd}."
                )
                raise ValueError(msg)  # noqa: B904
            if p.suffix not in {".py", ".js"}:
                msg = (
                    "server_file must end with .py or .js. "
                    f"Got {p.suffix} for {p}."
                )
                raise ValueError(msg)
        elif server_command is None:
            msg = "server_file is required when server_command is not provided."
            raise ValueError(msg)
        return cast("str | None", handler(final_value))

    @field_validator("server_command", mode="wrap")
    @classmethod
    def _validate_server_command(
        cls,
        value: str | None,
        handler: ValidatorFunctionWrapHandler,
        info: ValidationInfo,
    ) -> str | None:
        """Validate server_command and ensure exclusivity.

        Args:
            value: Raw server_command string.
            handler: Inner validator handler.
            info: Validation context.

        Returns:
            str | None: Validated server command or None.

        Raises:
            ValueError: If mutually exclusive with server_file or empty.
        """
        final_value: str | None = value or info.data.get("server_command")
        server_file: Path | None = info.data.get("server_file")
        if (server_file is None) and (
            sfc := info.data.get("server_file_or_command")
        ):
            server_file, final_value = cls._distinguish_server_file_or_command(
                sfc  # pyright: ignore[reportAny]
            )
            info.data["server_file"] = server_file
        if final_value is not None:
            if server_file is not None:
                msg = (
                    "server_command and server_file are mutually exclusive. "
                    "Please provide only one."
                )
                raise ValueError(msg)
            if not final_value.strip():
                msg = "server_command cannot be empty."
                raise ValueError(msg)
        elif server_file is None:
            msg = "server_command is required when server_file is not provided."
            raise ValueError(msg)
        return cast("str | None", handler(final_value))

    @staticmethod
    def _distinguish_server_file_or_command(
        server_file_or_command: str | Path,
    ) -> tuple[Path, None] | tuple[None, str]:
        """Return the server_file and server_command.

        We take a single string (`server_file_or_command`) and return a tuple
        (`server_file`, `server_command`).

        Args:
            server_file_or_command: The server_file_or_command string.

        Returns:
            A tuple of (`server_file`, `server_command`).
        """
        if isinstance(server_file_or_command, Path):
            server_file_or_command = str(server_file_or_command)
        if server_file_or_command.endswith((".py", ".js")):
            return Path(server_file_or_command), None
        return None, server_file_or_command

    @field_validator("command_type", mode="wrap")
    @classmethod
    def _infer_command_type(
        cls,
        value: CommandType | None,
        handler: ValidatorFunctionWrapHandler,
        info: ValidationInfo,
    ) -> CommandType:
        """Infer command_type from server_file / server_command.

        Args:
            value: Pre-existing (unused) value.
            handler: Inner handler.
            info: Validation context.

        Returns:
            CommandType | None: Inferred enum or None.

        Raises:
            ValueError: If neither server_file nor server_command is provided,
                or if server_file has an invalid extension.
        """
        if value:
            return cast("CommandType", handler(value))
        final_value: CommandType
        sf = cast("Path | None", info.data.get("server_file"))
        sc = cast("str | None", info.data.get("server_command"))
        sfc = info.data.get("server_file_or_command")
        if sfc:
            sf, sc = cls._distinguish_server_file_or_command(sfc)  # pyright: ignore[reportAny]
            info.data["server_file"] = sf
            info.data["server_command"] = sc
        elif not sf and not sc:
            msg = (
                "Provide either `server_file` or `server_command`"
                " to infer command_type."
            )
            raise ValueError(msg)

        # At this stage, we should have at least one of sf or sc.
        if sf:
            if sc:
                msg = (
                    "Provide only one of `server_file` or `server_command`"
                    " to infer command_type."
                )
                raise ValueError(msg)
            ext = Path(sf).suffix
            if ext == ".py":
                final_value = CommandType.python
                info.data["server_file_or_command"] = sf
            elif ext == ".js":
                final_value = CommandType.node
                info.data["server_file_or_command"] = sf
            else:
                msg = (
                    f"server_file must end with .py or .js. Got {ext} for {sf}."
                )
                raise ValueError(msg)

        elif sc:
            final_value = CommandType.shell
            info.data["server_file_or_command"] = sc
        else:
            msg = (
                "Provide either `server_file` or `server_command`"
                " to infer command_type."
            )
            raise ValueError(msg)
        return cast("CommandType", handler(final_value))

    @field_validator("node_version", mode="wrap")
    @classmethod
    def _validate_node_version(
        cls,
        value: str | float | None,
        handler: ValidatorFunctionWrapHandler,
        info: ValidationInfo,
    ) -> str | None:
        """Validate node_version only allowed when runtime node.

        Args:
            value: Raw node_version.
            handler: Inner handler.
            info: Validation context.

        Returns:
            str | None: Node version or None.

        Raises:
            ValueError: If provided for non-node runtime.
        """
        console = Console()
        final_value: str | float | None = value
        if isinstance(final_value, float):
            final_value = str(int(final_value))
        runtime = info.data.get("runtime")
        do_generate = cast(
            "float", info.data.get("do_generate_config_files", False)
        )

        if runtime != Runtime.node:
            if value is not None:
                msg = (
                    "node_version provided but runtime is not node. "
                    "Set runtime explicitly or remove node_version."
                )
                raise ValueError(msg)
            final_value = None
        # Runtime is node
        elif final_value is None:
            if do_generate:  # pragma: no cover
                prompt_text = (
                    f"[bold blue]node_version[/bold blue]"
                    f" {DESCRIPTIONS['node_version']}"
                )
                final_value = CustomPrompt.ask(
                    prompt_text,
                    default="20",
                    console=console,
                )
            else:
                msg = "node_version is required when runtime is node."
                raise ValueError(msg)
        elif do_generate:  # pragma: no cover
            # Even if we have a value, prompt in wizard mode to confirm
            prompt_text = (
                f"[bold blue]node_version[/bold blue]"
                f" {DESCRIPTIONS['node_version']} "
                f"(detected: {final_value})"
            )
            confirmed_version = CustomPrompt.ask(
                prompt_text,
                default=final_value,
                console=console,
            )
            final_value = confirmed_version

        return cast("str | None", handler(final_value))

    @field_validator("run_npm_build", mode="wrap")
    @classmethod
    def _validate_run_npm_build(
        cls,
        value: bool | None,  # noqa: FBT001
        handler: ValidatorFunctionWrapHandler,
        info: ValidationInfo,
    ) -> bool | None:
        """Validate run_npm_build only for node runtime (default False).

        Args:
            value: Raw value.
            handler: Inner handler.
            info: Validation context.

        Returns:
            bool | None: Final boolean (False if node & unspecified).

        Raises:
            ValueError: If set when runtime not node.
        """
        console = Console()
        final_value: bool | None = value
        runtime = info.data.get("runtime")
        do_generate = cast(
            "bool", info.data.get("do_generate_config_files", False)
        )

        if runtime == Runtime.node:
            if final_value is None:
                if do_generate:  # pragma: no cover
                    prompt_text = (
                        f"[bold blue]run_npm_build[/bold blue]"
                        f" {DESCRIPTIONS['run_npm_build']}"
                    )
                    final_value = Confirm.ask(
                        prompt_text,
                        default=False,
                        console=console,
                    )
                else:
                    final_value = False
            elif do_generate:  # pragma: no cover
                # Even if we have a value, prompt in wizard mode to confirm
                prompt_text = (
                    f"[bold blue]run_npm_build[/bold blue]"
                    f" {DESCRIPTIONS['run_npm_build']} "
                    f"(current: {final_value})"
                )
                confirmed_value = Confirm.ask(
                    prompt_text,
                    default=final_value,
                    console=console,
                )
                final_value = confirmed_value
        else:
            if value is not None:
                msg = "run_npm_build provided but runtime is not node. "
                raise ValueError(msg)
            final_value = None

        return cast("bool | None", handler(final_value))

    @staticmethod
    def _get_google_values(
        google_dict: dict[str, Any],  # pyright: ignore[reportExplicitAny]
        server_name: str,
        *,
        do_generate: bool,
    ) -> tuple[str, str, str, str]:
        """Get Google values from a dictionary.

        Args:
            google_dict: Dictionary containing Google values.
            server_name: Server name.
            do_generate: Whether to generate values.

        Returns:
            tuple[str, str, str, str]: Project name, region, artifact registry,
                service name.

        Raises:
            ValueError: If project name is required but not provided.
        """
        project_name = google_dict.get("project")
        if project_name is None:
            if do_generate:  # pragma: no cover
                project_name = CustomPrompt.ask(
                    "[bold blue]google.project[/bold blue]"
                    f" {DESCRIPTIONS['google.project']}",
                    default="",
                )
            else:
                msg = "google.project is required."
                raise ValueError(msg)
        region = google_dict.get("region")
        if region is None:
            region = "us-central1"
            if do_generate:  # pragma: no cover
                region = CustomPrompt.ask(
                    "[bold blue]google.region[/bold blue]"
                    f" {DESCRIPTIONS['google.region']}",
                    default=region,
                )
        artifact_registry = google_dict.get("artifact_registry")
        if not artifact_registry:
            artifact_registry = f"{server_name}-repo"
            if do_generate:  # pragma: no cover
                artifact_registry = CustomPrompt.ask(
                    "[bold blue]google.artifact_registry[/bold blue]"
                    f" {DESCRIPTIONS['google.artifact_registry']}",
                    default=artifact_registry,
                )
        service_name = google_dict.get("service_name")
        if not service_name:
            service_name = f"{server_name}-service"
            if do_generate:  # pragma: no cover
                service_name = CustomPrompt.ask(
                    "[bold blue]google.service_name[/bold blue]"
                    f" {DESCRIPTIONS['google.service_name']}",
                    default=service_name,
                )
        return (
            project_name,
            region,
            artifact_registry,
            service_name,
        )

    @field_validator("providers", mode="wrap")
    @classmethod
    def _validate_providers(
        cls,
        value: dict[str, GoogleProviderConfig],
        handler: ValidatorFunctionWrapHandler,
        info: ValidationInfo,
    ) -> dict[str, GoogleProviderConfig]:
        """Validate providers.

        Args:
            value: Raw providers dictionary.
            handler: Inner handler.
            info: Validation context.

        Returns:
            dict[str, GoogleProviderConfig]: Validated providers dictionary.
        """
        server_name = cast("str", info.data.get("server_name"))
        g_pn, g_reg, g_ar, g_sn = cls._get_google_values(
            cast("dict[str, Any]", value.get("google", {})),  # pyright: ignore[reportExplicitAny],
            server_name,
            do_generate=cast(
                "bool", info.data.get("do_generate_config_files", False)
            ),
        )
        return cast(
            "dict[str, GoogleProviderConfig]",
            handler(
                {
                    "google": GoogleProviderConfig(
                        project=g_pn,
                        artifact_registry=g_ar,
                        region=g_reg,
                        service_name=g_sn,
                    ),
                }
            ),
        )

    # --------------- AFTER model validator ---------------
    @model_validator(mode="after")
    def _ensure_server_target(self) -> EmsipiConfig:
        """Ensure at least one of server_file or server_command is present.

        Returns:
            EmsipiConfig: Self.

        Raises:
            ValueError: If neither is supplied.
        """
        if not self.server_file and not self.server_command:
            msg = (
                "Neither server_file nor server_command provided. "
                "Provide at least one to specify the server target."
            )
            raise ValueError(msg)
        return self

    @computed_field  # type: ignore[prop-decorator]
    @property
    def clean_server_file_or_command(self) -> str | Path:
        """A cleaned server file or command.

        Returns:
            str | Path: Cleaned server file or command.

        Raises:
            ValueError: If both server_file and server_command are provided.
        """
        if self.server_file and not self.server_command:
            return self.server_file
        if self.server_command and not self.server_file:
            return self.server_command
        if self.server_file and self.server_command:
            msg = "Both server_file and server_command provided. "
            "Provide only one to specify the server target."
            raise ValueError(msg)
        if not self.server_file and not self.server_command:
            msg = "Neither server_file nor server_command provided. "
            "Provide at least one to specify the server target."
            raise ValueError(msg)
        return self.server_file_or_command

    @computed_field  # type: ignore[prop-decorator]
    @property
    def clean_server_name(self) -> str:
        """A cleaned server name.

        Returns:
            str: Cleaned server name.

        Raises:
            ValueError: If server_name is not provided.
        """
        if self.server_name is None:
            msg = "server_name is required."
            raise ValueError(msg)
        return self.server_name

    @field_serializer("dockerfile")
    def serialize_path(self, path: Path, info: Any) -> str:  # noqa: ANN401  # pyright: ignore[reportExplicitAny, reportAny]
        """Serializes the Path object to a relative path string.

        Returns:
            str: The relative path string.
        """
        _ = info  # pyright: ignore[reportAny]
        try:
            return os.path.relpath(path, self.working_directory)
        except ValueError:
            # This can happen if the path is on a different drive on Windows
            return str(path)


if __name__ == "__main__":
    # Example usage
    try:
        cfg = EmsipiConfig.create(
            provider="google",
            server_file_or_command="app.py",
        )
        rich.print(cfg)
    except ValidationError as e:
        rich.print(e)
