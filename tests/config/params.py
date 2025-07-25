"""Test parameter dataclasses for configuration testing.

This module defines the structured parameter types used in configuration
tests according to specs/test_config.md.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class WizardStep:
    """Represents a single step in wizard behavior testing.

    Args:
        expected_output: Text the terminal should display since last step
        user_input: Input to provide (without newline, added automatically)
    """

    expected_output: str
    user_input: str


@dataclass
class InternalConfigParams:
    """Parameters for the internal-config command.

    Args:
        provider: Cloud provider to deploy to
        server_file_or_command: Server file or command to deploy
        directory: Directory to deploy to
        runtime: Runtime to deploy to
    """

    provider: str
    server_file_or_command: str | None = None
    runtime: str | None = None
    directory: Path | None = None


@dataclass
class ConfigTestParams:
    """Parameters for a single configuration test case.

    This dataclass encapsulates all the parameters needed to run a single
    configuration test according to the test specification.

    Args:
        test_id: Unique identifier for the test case
        description: Human-readable description of what the test validates
        public_config: Content for emsipi.yaml (None if file should not exist)
        private_config: Content for emsipi.private.yaml (None if file should
            not exist)
        files: Dictionary mapping relative file paths to their content
        cli_arguments: Raw CLI command text (e.g. "emsipi internal-config
            google --arg val")
        non_interactive_arguments: Non-interactive arguments to the
            internal-config command.
        environment_variables: Environment variables to set during test
        wizard_behavior: Expected wizard interaction steps
        expected_configuration: Subset of expected config values to validate
        expected_files: Dictionary mapping file paths to regex patterns for
            validation
        expected_validation_errors: List of expected validation error messages
        expected_error_message: Expected error message if the test should fail
        should_succeed: Whether the test is expected to succeed (default: True)
        template_vars: Variables for template substitution in fixture files
    """

    test_id: str
    description: str
    public_config: dict[str, Any] | None = None  # pyright: ignore[reportExplicitAny]
    private_config: dict[str, Any] | None = None  # pyright: ignore[reportExplicitAny]
    files: dict[str, str] | None = None
    cli_arguments: str = ""
    non_interactive_arguments: InternalConfigParams | None = None
    environment_variables: dict[str, str] | None = None
    wizard_behavior: list[WizardStep] | None = None
    expected_configuration: dict[str, Any] | None = None  # pyright: ignore[reportExplicitAny]
    expected_files: dict[str, list[str] | str] | None = None
    template_vars: dict[str, str] | None = None
    expected_validation_errors: list[str] | None = None
    expected_warnings: list[str] | None = None
    expected_error_message: str | None = None
    should_succeed: bool = True

    def __post_init__(self) -> None:
        """Validate test parameters after initialization.

        Raises:
            ValueError: If validation fails
        """
        # Validate test_id format
        if not re.match(r"^[a-zA-Z0-9_-]+$", self.test_id):
            msg = f"Invalid test_id format: {self.test_id}"
            raise ValueError(msg)

        # Ensure files dict uses relative paths only
        if self.files:
            for file_path in self.files:
                if Path(file_path).is_absolute():
                    msg = f"File path must be relative: {file_path}"
                    raise ValueError(msg)

        # Validate expected_files regex patterns
        if self.expected_files:
            for file_path, patterns in self.expected_files.items():
                pattern_list = (
                    patterns if isinstance(patterns, list) else [patterns]
                )
                for pattern in pattern_list:
                    try:
                        _ = re.compile(pattern)
                    except re.error as e:
                        msg = (
                            f"Invalid regex pattern '{pattern}' for file "
                            f"{file_path}: {e}"
                        )
                        raise ValueError(msg) from e


@dataclass
class SuiteConfig:
    """Configuration for the entire test suite.

    Args:
        tmp_dir_name: Name of temporary directory for tests (default: "tmp")
        cleanup_on_success: Whether to clean tmp directory after successful
            tests
        cleanup_on_failure: Whether to clean tmp directory after failed tests
        timeout_seconds: Timeout for CLI command execution
        verbose: Whether to enable verbose output during testing
    """

    tmp_dir_name: str = "tmp"
    cleanup_on_success: bool = True
    cleanup_on_failure: bool = False
    timeout_seconds: int = 30
    verbose: bool = False
