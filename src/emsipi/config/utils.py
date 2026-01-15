"""Utility functions for the config module."""

# pyright: reportImplicitStringConcatenation=false

import tomllib
from pathlib import Path
from typing import Any, Literal, cast

from rich.console import Console

from emsipi.config.version_parser import get_first_ok_version_as_string
from emsipi.printshop import WARNING_RICH_PREPEND

from .descriptions import DESCRIPTIONS
from .typeshed import CommandType, CustomPrompt, PythonDepsFile, Runtime


def try_parse_python_version_from_toml(
    file_path: Path, keys: list[str] | str
) -> str | None:
    """Try to parse Python version from a TOML file.

    Args:
        file_path: Path to the TOML file.
        keys: Key(s) to look for in the parsed data. Can be a single key
            or a list of keys for nested lookup.

    Returns:
        str | None: Parsed version or None if not found.

    Raises:
        ValueError: If file not found, parsing fails, or unexpected error.
        TypeError: If the final value is not a string.
    """
    try:
        data = tomllib.loads(file_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        msg = f"{file_path} not found."
        raise ValueError(msg) from exc
    except tomllib.TOMLDecodeError as exc:
        msg = f"Failed parsing {file_path}: {exc}"
        raise ValueError(msg) from exc
    except Exception as exc:
        msg = f"Unexpected error parsing {file_path}: {exc}"
        raise ValueError(msg) from exc

    if isinstance(keys, str):
        keys = [keys]

    value: Any = data  # pyright: ignore[reportExplicitAny]
    for key in keys:
        if not isinstance(value, dict):
            return None  # Cannot traverse further
        value = value.get(key)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]

    if value is None:
        return None

    if not isinstance(value, str):
        key_path = ".".join(keys)
        msg = (
            f"Expected a string for '{key_path}' in {file_path}, "
            f"but got {type(value).__name__}."  # pyright: ignore[reportUnknownArgumentType]
        )
        raise TypeError(msg)

    # Now do a final round of parsing to ensure that it's "3.XX"
    return get_first_ok_version_as_string(value)


def infer_python_version(
    data: dict[str, Any],  # pyright: ignore[reportExplicitAny]
) -> str | None:
    """Infer Python version from raw + dependency file.

    Args:
        data: Validation context.

    Returns:
        str | None: Inferred version or None if runtime is not python.

    Raises:
        ValueError: Inference failure or runtime mismatch.
    """
    console = Console()
    final_value: str | None = data.get("raw_python_version")
    runtime = data.get("runtime")
    do_generate = cast("bool", data.get("do_generate_config_files", False))

    if runtime != Runtime.python and final_value not in {None, "auto"}:
        msg = "python_version provided but runtime is not python."
        raise ValueError(msg)
    if runtime != Runtime.python and final_value in {None, "auto"}:
        return None
    if final_value and final_value != "auto":
        return final_value

    # Auto-detect
    deps_file = data.get("python_dependencies_file")
    wd = cast("Path", data["working_directory"])
    if deps_file == PythonDepsFile.uvlock:
        final_value = try_parse_python_version_from_toml(
            file_path=(wd / "uv.lock"), keys="requires-python"
        )
    elif deps_file == PythonDepsFile.pyproject:
        final_value = try_parse_python_version_from_toml(
            file_path=(wd / "pyproject.toml"),
            keys=["project", "requires-python"],
        )
    elif deps_file == PythonDepsFile.requirements:
        if do_generate:
            prompt_text = (
                "[yellow]Cannot infer Python version from "
                "requirements.txt.[/yellow]\n"
                f"[bold blue]python_version[/bold blue]"
                f" {DESCRIPTIONS['python_version']}"
            )
            final_value = CustomPrompt.ask(
                prompt_text,
                default="3.11",
                console=console,
            )
        else:
            msg = (
                "Cannot infer python_version from requirements.txt;"
                " set python_version explicitly."
            )
            msg += (
                str(data)
                + f"{final_value=}, {deps_file=}, {wd=}, {do_generate=}"
            )
            raise ValueError(msg)

    detected_or_default: Literal["detected", "default"] = "detected"
    if final_value is None:
        final_value = "3.11"
        detected_or_default = "default"

    # Even if we inferred a value, prompt in wizard mode to confirm
    # (only for Python runtime)
    if do_generate and final_value and runtime == Runtime.python:
        prompt_text = (
            f"[bold blue]python_version[/bold blue]"
            f" {DESCRIPTIONS['python_version']} "
            f"({detected_or_default}: {final_value})"
        )
        confirmed_version = CustomPrompt.ask(
            prompt_text,
            default=final_value,
            console=console,
        )
        final_value = confirmed_version

    return final_value


def infer_python_deps(  # noqa: C901, PLR0912
    data: dict[str, Any],  # pyright: ignore[reportExplicitAny]
) -> PythonDepsFile | None:
    """Infer Python dependency file choice.

    Args:
        data: Validation context.

    Returns:
        PythonDepsFile: Inferred file enum.

    Raises:
        ValueError: Invalid or missing when needed.
    """
    console = Console()
    runtime = data.get("runtime")
    raw = data.get("raw_python_dependencies_file")
    final_value: PythonDepsFile | None = raw
    do_generate = cast("bool", data.get("do_generate_config_files", False))

    if runtime != Runtime.python:
        if raw not in {None, "auto"}:
            msg = "python_dependencies_file provided but runtime is not python."
            raise ValueError(msg)
        # It's JavaScript, so we don't need a Python dependency file
        return None
    if final_value in {None, "auto"}:
        # Auto-detect
        if data.get("uv_lock_present"):
            final_value = PythonDepsFile.uvlock
            if data.get("requirements_txt_present") and do_generate:
                console.print(
                    WARNING_RICH_PREPEND + "Both uv.lock and "
                    "requirements.txt found. "
                    "Using uv.lock."
                )
        elif data.get("requirements_txt_present"):
            final_value = PythonDepsFile.requirements
            if data.get("deps_in_pyproject") and do_generate:
                console.print(
                    WARNING_RICH_PREPEND + "Both "
                    "requirements.txt and pyproject.toml "
                    "with dependencies found. Using requirements.txt."
                )
        elif data.get("deps_in_pyproject"):
            final_value = PythonDepsFile.pyproject
        else:
            msg = (
                "No Python dependency file found (uv.lock, "
                "requirements.txt, pyproject.toml with dependencies)."
                " Either ensure that a dependency file is present or set "
                "python_dependencies_file explicitly."
            )
            raise ValueError(msg)
    else:
        mapping = {
            "requirements.txt": PythonDepsFile.requirements,
            "pyproject.toml": PythonDepsFile.pyproject,
            "uv.lock": PythonDepsFile.uvlock,
        }
        if raw not in mapping:
            msg = (
                "Invalid python_dependencies_file value; "
                "expected auto, requirements.txt, pyproject.toml,"
                " or uv.lock."
            )
            raise ValueError(msg)
        final_value = mapping[raw]

    if not final_value:
        msg = (
            "No Python dependency file found (uv.lock, "
            "requirements.txt, pyproject.toml with dependencies)."
            " Set python_dependencies_file explicitly."
        )
        raise ValueError(msg)

    # Even if we inferred a value, prompt in wizard mode to confirm
    # (only for Python runtime)
    if do_generate and runtime == Runtime.python:
        choices = ["requirements.txt", "pyproject.toml", "uv.lock"]
        prompt_text = (
            f"[bold blue]python_dependencies_file[/bold blue]"
            f" {DESCRIPTIONS['python_dependencies_file']} "
            f"(detected: {final_value.value})"
        )
        choice = CustomPrompt.ask(
            prompt_text,
            choices=choices,
            default=final_value.value,
            console=console,
        )
        mapping = {
            "requirements.txt": PythonDepsFile.requirements,
            "pyproject.toml": PythonDepsFile.pyproject,
            "uv.lock": PythonDepsFile.uvlock,
        }
        final_value = mapping[choice]

    return final_value


def infer_runtime(  # noqa: C901, PLR0912
    data: dict[str, Any],  # pyright: ignore[reportExplicitAny]
) -> Runtime:
    """Infer runtime from raw_runtime, signals & command_type.

    Args:
        data: Validation context.

    Returns:
        Runtime: Inferred runtime.

    Raises:
        ValueError: Ambiguous / missing signals or invalid raw value.
    """
    console = Console()
    raw = data.get("raw_runtime")
    final_value: Runtime | None = raw
    cmd_type = data.get("command_type")
    do_generate = cast("bool", data.get("do_generate_config_files", False))
    user_made_choice = False

    if final_value in {None, "auto"}:
        if cmd_type == CommandType.python:
            final_value = Runtime.python
        elif cmd_type == CommandType.node:
            final_value = Runtime.node
        else:
            py_sig = data.get("any_python_config_file_present")
            node_sig = data.get("package_json_present")
            if py_sig and node_sig:
                if do_generate:
                    # Prompt user to choose
                    choices = ["python", "node"]
                    prompt_text = (
                        "[yellow]Both Python and Node config files "
                        "found. "
                        "Please specify the runtime manually.[/yellow]\n"
                        f"[bold blue]runtime[/bold blue]"
                        f" {DESCRIPTIONS['runtime']}"
                    )
                    choice = CustomPrompt.ask(
                        prompt_text,
                        choices=choices,
                        console=console,
                    )
                    final_value = Runtime(choice)
                else:
                    msg = (
                        "Ambiguous project signals; both Python"
                        " and Node config files found. "
                        "Set runtime explicitly."
                    )
                    raise ValueError(msg)
            elif py_sig:
                final_value = Runtime.python
            elif node_sig:
                final_value = Runtime.node
            elif do_generate:
                # Prompt user to choose
                choices = ["python", "node"]
                prompt_text = (
                    WARNING_RICH_PREPEND + "No Python or Node config files "
                    "detected. You will have to specify one manually.\n"
                    f"[bold blue]runtime[/bold blue]"
                    f" {DESCRIPTIONS['runtime']}"
                )
                choice = CustomPrompt.ask(
                    prompt_text,
                    choices=choices,
                    console=console,
                )
                final_value = Runtime(choice)
                user_made_choice = True
            else:
                msg = (
                    "Cannot infer runtime: no Python or Node signals. "
                    "Set runtime explicitly or ensure project"
                    " files are present."
                )
                raise ValueError(msg)
    elif raw not in {"python", "node"}:
        msg = "Invalid runtime (expected python|node|auto)."
        raise ValueError(msg)
    else:
        final_value = Runtime(raw)

    # Even if we inferred a value, prompt in wizard mode to confirm
    if do_generate and final_value and not user_made_choice:
        choices = ["python", "node"]
        prompt_text = (
            f"[bold blue]runtime[/bold blue] {DESCRIPTIONS['runtime']} "
            f"(detected: {final_value.value})"
        )
        confirmed_choice = CustomPrompt.ask(
            prompt_text,
            choices=choices,
            default=final_value.value,
            console=console,
        )
        final_value = Runtime(confirmed_choice)

    return final_value
