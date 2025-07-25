"""CLI execution wrapper with wizard behavior simulation.

This module provides utilities for executing the emsipi CLI in test environments
and simulating user interactions according to specs/test_config.md.
"""

import contextlib
import copy
import io
import json
import logging
import os
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, cast, final, override

import pexpect
import rich
from pydantic import ValidationError

from emsipi.main import internal_config_command
from emsipi.printshop import WARNING_RICH_PREPEND

from .params import (
    ConfigTestParams,
    InternalConfigParams,
    SuiteConfig,
    WizardStep,
)
from .virtual_directory import VirtualDirectory

logger = logging.getLogger(__name__)


@final
class CLIExecutionResult:
    """Result of CLI command execution."""

    def __init__(  # noqa: PLR0913
        self,
        return_code: int,
        stdout: str,
        stderr: str,
        execution_time: float,
        *,
        configuration_json: dict[str, Any] | None = None,  # pyright: ignore[reportExplicitAny]
        validation_error: ValidationError | None = None,
        warnings: list[str] | None = None,
    ) -> None:
        """Initialize execution result.

        Args:
            return_code: Process return code
            stdout: Standard output content
            stderr: Standard error content
            execution_time: Time taken for execution in seconds
            configuration_json: Parsed JSON configuration if available
            validation_error: Pydantic ValidationError if configuration failed
        """
        self.return_code = return_code
        self.stdout = stdout
        self.stderr = stderr
        self.execution_time = execution_time
        self.configuration_json = configuration_json
        self.validation_error = validation_error
        self.warnings = warnings or []

    @property
    def success(self) -> bool:
        """Check if the command executed successfully.

        Returns:
            bool: True if return code is 0
        """
        return self.return_code == 0

    @override
    def __repr__(self) -> str:
        """String representation of the result.

        Returns:
            str: Formatted result information
        """
        return (
            f"CLIExecutionResult(return_code={self.return_code}, "
            f"success={self.success}, "
            f"execution_time={self.execution_time:.2f}s)"
        )


class WizardInteractionError(Exception):
    """Raised when wizard interaction fails."""


@final
class CLIExecutor:
    """Executes CLI commands with wizard behavior simulation."""

    def __init__(self, suite_config: SuiteConfig) -> None:
        """Initialize the CLI executor.

        Args:
            suite_config: Configuration for the test suite
        """
        self.suite_config = suite_config
        self.timeout = suite_config.timeout_seconds

    @staticmethod
    def _parse_cli_arguments(cli_arguments: str) -> list[str]:
        """Parse CLI arguments string into a list.

        Args:
            cli_arguments: Raw CLI command string

        Returns:
            list[str]: Parsed command arguments
        """
        # Simple parsing - split by whitespace but handle quoted arguments

        return shlex.split(cli_arguments)

    @staticmethod
    def _extract_json_from_output(
        output: str,
    ) -> dict[str, Any] | None:  # pyright: ignore[reportExplicitAny]
        """Extract JSON configuration from command output.

        Args:
            output: Command output that may contain JSON

        Returns:
            dict[str, Any] | None: Parsed JSON if found, None otherwise
        """
        # Look for JSON in the output
        # The internal-config command should output JSON to stdout
        lines = output.strip().split("\n")

        # Try to find JSON content
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            if stripped_line.startswith("{"):
                # Potential JSON start - try to parse from here
                json_candidate = "\n".join(lines[i:])
                try:
                    return json.loads(json_candidate)  # type: ignore[no-any-return] # pyright: ignore[reportAny]
                except json.JSONDecodeError:
                    continue

        # If no JSON found in individual lines, try the entire output
        try:
            return json.loads(output.strip())  # type: ignore[no-any-return] # pyright: ignore[reportAny]
        except json.JSONDecodeError:
            rich.print(
                WARNING_RICH_PREPEND + "No valid JSON found in command output"
            )
            return None

    def _execute_simple_command(
        self,
        args: list[str] | InternalConfigParams,
        working_dir: Path,
        env_vars: dict[str, str] | None = None,
    ) -> CLIExecutionResult:
        """Execute a simple CLI command without wizard interaction.

        Args:
            args: Command arguments
            working_dir: Working directory for the command
            env_vars: Additional environment variables

        Returns:
            CLIExecutionResult: Execution result
        """
        start_time = time.time()

        # Prepare environment
        env = os.environ.copy()
        stdout: str = ""
        stderr: str = ""
        return_code: int = 0
        output: str = ""
        validation_error: ValidationError | None = None

        if env_vars:
            env.update(env_vars)

        try:
            # Execute the command
            if isinstance(args, list):
                result = subprocess.run(  # noqa: S603
                    args,
                    check=False,
                    cwd=working_dir,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                )
                output = result.stdout
                stdout = result.stdout
                return_code = result.returncode
                stderr = result.stderr

            else:
                with (
                    contextlib.redirect_stdout(io.StringIO()) as f,
                    contextlib.redirect_stderr(io.StringIO()) as g,
                ):
                    try:
                        _ = str(
                            internal_config_command(
                                provider=args.provider,
                                server_file_or_command=args.server_file_or_command,
                                directory=working_dir,
                                runtime=args.runtime,
                            )
                        )
                        stdout = f.getvalue()
                        output = stdout
                        stderr = g.getvalue()
                        return_code = 0
                    except ValidationError as ve:
                        # Capture Pydantic validation errors
                        validation_error = ve
                        stdout = f.getvalue()
                        output = stdout
                        stderr = g.getvalue() + str(ve)
                        return_code = 1

            config_json = self._extract_json_from_output(output)

            execution_time = time.time() - start_time

            return CLIExecutionResult(
                return_code=return_code,
                stdout=stdout,
                stderr=stderr,
                execution_time=execution_time,
                configuration_json=config_json,
                validation_error=validation_error,
            )

        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            msg = f"Command timed out after {self.timeout} seconds"
            return CLIExecutionResult(
                return_code=-1,
                stdout="",
                stderr=msg,
                execution_time=execution_time,
                validation_error=None,
            )
        except Exception as e:  # noqa: BLE001
            execution_time = time.time() - start_time
            return CLIExecutionResult(
                return_code=-1,
                stdout="",
                stderr=f"Command execution failed: {e}",
                execution_time=execution_time,
                validation_error=None,
            )

    def _setup_wizard_process(
        self,
        args: list[str],
        working_dir: Path,
        env_vars: dict[str, str] | None = None,
    ) -> "pexpect.spawn[str]":
        """Set up the pexpect process for wizard interaction.

        Args:
            args: Command arguments
            working_dir: Working directory for the command
            env_vars: Additional environment variables

        Returns:
            pexpect.spawn[str]: Spawned process ready for interaction
        """
        # Prepare environment
        env = copy.deepcopy(os.environ)
        if env_vars:
            env.update(env_vars)

        args = [*args]
        # Build command string for pexpect
        cmd = " ".join(args)

        # Spawn the process with pexpect for interactive control
        return cast(
            "pexpect.spawn[str]",
            pexpect.spawn(
                cmd,
                cwd=str(working_dir),
                env=env,
                timeout=self.timeout,
                encoding="utf-8",
                codec_errors="replace",
            ),
        )

    def _process_wizard_step(
        self,
        child: "pexpect.spawn[str]",
        step: WizardStep,
        step_index: int,
        args: list[str],
        working_dir: Path,
    ) -> None:
        """Process a single wizard interaction step.

        Args:
            child: The pexpect process
            step: The wizard step to process
            step_index: Index of the current step (for error messages)
            args: Command arguments
            working_dir: Working directory for the command

        Raises:
            WizardInteractionError: If the step fails
        """
        try:
            # Wait for expected output
            _ = child.expect(step.expected_output, timeout=self.timeout)

            if self.suite_config.verbose:
                msg = (
                    f"Step {step_index + 1}: Found expected output: "
                    f"{step.expected_output}"
                )
                logger.info(msg)

            # Send user input
            _ = child.sendline(step.user_input)

            if self.suite_config.verbose:
                msg = f"Step {step_index + 1}: Sent input: {step.user_input}"
                logger.info(msg)

        except pexpect.TIMEOUT:
            before_output = child.before or ""
            # This regex handles most common ANSI escape codes
            ansi_escape = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
            clean_output = ansi_escape.sub("", before_output)
            clean_output = clean_output.replace("\r\n", "\n").strip()

            msg = (
                f"Wizard step {step_index + 1} timed out.\n"
                f"  Expected to see pattern: '{step.expected_output}'\n"
                f"  Instead, got this (cleaned) output:\n"
                f"  ---\n"
                f"{clean_output}\n"
                f"  ---\n"
                f"To debug, run the following command:\n"
                f"cd {working_dir} && {' '.join(args)}"
            )
            raise WizardInteractionError(msg) from None
        except pexpect.EOF:
            msg = (
                f"Wizard step {step_index + 1} encountered "
                "unexpected EOF "
                f"while waiting for: '{step.expected_output}'"
                f"To debug, run the following command:\n"
                f"cd {working_dir} && {' '.join(args)}"
            )
            raise WizardInteractionError(msg) from None

    def _finalize_wizard_process(
        self, child: "pexpect.spawn[str]", start_time: float
    ) -> CLIExecutionResult:
        """Finalize the wizard process and extract results.

        Args:
            child: The pexpect process
            start_time: Start time of the process

        Returns:
            CLIExecutionResult: Execution result with extracted data
        """
        # Wait for the process to complete
        _ = child.expect(pexpect.EOF, timeout=self.timeout)
        child.close()

        execution_time = time.time() - start_time

        # Get output and return code
        stdout = child.before or ""
        # Take stdout only after '{\n'
        stdout = "\n{" + stdout.split("\n{")[1]
        stderr = ""  # pexpect doesn't separate stderr easily
        return_code = child.exitstatus if child.exitstatus is not None else -1

        # Try to extract JSON from output
        config_json = self._extract_json_from_output(stdout)

        return CLIExecutionResult(
            return_code=return_code,
            stdout=stdout,
            stderr=stderr,
            execution_time=execution_time,
            configuration_json=config_json,
            validation_error=None,
        )

    def _handle_wizard_timeout(
        self, child: "pexpect.spawn[str]", start_time: float
    ) -> CLIExecutionResult:
        """Handle wizard command timeout.

        Args:
            child: The pexpect process that timed out
            start_time: Start time of the process

        Returns:
            CLIExecutionResult: Error result for timeout
        """
        execution_time = time.time() - start_time
        msg = f"Wizard command timed out after {self.timeout} seconds"
        # Try to close the child process
        with contextlib.suppress(Exception):
            child.close(force=True)
        return CLIExecutionResult(
            return_code=-1,
            stdout="",
            stderr=msg,
            execution_time=execution_time,
            validation_error=None,
        )

    def _execute_wizard_command(
        self,
        args: list[str],
        working_dir: Path,
        wizard_steps: list[WizardStep],
        env_vars: dict[str, str] | None = None,
    ) -> CLIExecutionResult:
        """Execute a CLI command with wizard interaction simulation.

        Args:
            args: Command arguments
            working_dir: Working directory for the command
            wizard_steps: Expected wizard interaction steps
            env_vars: Additional environment variables

        Returns:
            CLIExecutionResult: Execution result

        Raises:
            WizardInteractionError: If wizard interaction fails
        """
        start_time = time.time()

        try:
            child = self._setup_wizard_process(args, working_dir, env_vars)

            # Process wizard steps
            for step_index, step in enumerate(wizard_steps):
                self._process_wizard_step(
                    child, step, step_index, args, working_dir
                )

            return self._finalize_wizard_process(child, start_time)

        except pexpect.TIMEOUT:
            return self._handle_wizard_timeout(child, start_time)  # pyright: ignore[reportPossiblyUnboundVariable]
        except WizardInteractionError:
            # Re-raise wizard-specific errors
            raise
        except Exception as e:  # noqa: BLE001
            execution_time = time.time() - start_time
            return CLIExecutionResult(
                return_code=-1,
                stdout="",
                stderr=f"Wizard command execution failed: {e}",
                execution_time=execution_time,
                validation_error=None,
            )

    def execute_test_command(
        self,
        test_params: ConfigTestParams,
        virtual_dir: VirtualDirectory,
    ) -> CLIExecutionResult:
        """Execute the CLI command for a test case.

        Args:
            test_params: Test parameters containing CLI configuration
            virtual_dir: Virtual directory for the test

        Returns:
            CLIExecutionResult: Execution result

        Raises:
            ValueError: If no CLI arguments are provided in test parameters
        """

        working_dir: Path = virtual_dir.get_path()

        # Parse CLI arguments
        args: list[str] | InternalConfigParams
        if test_params.non_interactive_arguments:
            args = test_params.non_interactive_arguments
        else:
            args = self._parse_cli_arguments(test_params.cli_arguments)

            # Make sure we're using the Python module correctly
            # Replace 'emsipi' with the full module path if needed
            if args[0] == "emsipi":
                # Use the current Python interpreter to run the emsipi module
                emsipi_main_path = (
                    Path(__file__).parent.parent.parent
                    / "src"
                    / "emsipi"
                    / "main.py"
                )
                args = [sys.executable, str(emsipi_main_path), *args[1:]]
            if self.suite_config.verbose:
                logger.info(f"Executing command: {' '.join(args)}")
                logger.info(f"Working directory: {working_dir}")

        # Choose execution method based on whether wizard steps are provided
        if test_params.wizard_behavior:
            if not isinstance(args, list):
                msg = (
                    "Wizard steps provided but non-interactive arguments are "
                    "not supported"
                )
                raise ValueError(msg)
            return self._execute_wizard_command(
                args=args,
                working_dir=working_dir,
                wizard_steps=test_params.wizard_behavior,
                env_vars=test_params.environment_variables,
            )
        return self._execute_simple_command(
            args=args,
            working_dir=working_dir,
            env_vars=test_params.environment_variables,
        )
