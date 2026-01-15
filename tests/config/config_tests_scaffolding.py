"""Parameterized test structure for configuration testing.

This module provides the pytest integration and parameterized test structure
according to specs/test_config.md.
"""

import logging
from collections.abc import Callable
from typing import Any

import pytest

from .params import (
    ConfigTestParams,
    InternalConfigParams,
    SuiteConfig,
    WizardStep,
)
from .runner import ConfigTestResult, ConfigTestRunner

logger = logging.getLogger(__name__)


# Default test suite configuration
DEFAULT_SUITE_CONFIG = SuiteConfig(
    tmp_dir_name="tmp",
    cleanup_on_success=True,
    cleanup_on_failure=False,
    timeout_seconds=10,  # Shorter timeout to prevent hanging
    verbose=False,
)


def create_test_case(  # noqa: PLR0913
    test_id: str,
    description: str,
    *,
    public_config: dict[str, Any] | None = None,  # pyright: ignore[reportExplicitAny]
    private_config: dict[str, Any] | None = None,  # pyright: ignore[reportExplicitAny]
    files: dict[str, str] | None = None,
    cli_arguments: str | None = None,
    non_interactive_arguments: InternalConfigParams | None = None,
    environment_variables: dict[str, str] | None = None,
    wizard_behavior: list[WizardStep] | None = None,
    expected_configuration: dict[str, Any] | None = None,  # pyright: ignore[reportExplicitAny]
    expected_files: dict[str, list[str] | str] | None = None,
    template_vars: dict[str, str] | None = None,
    expected_warnings: list[str] | None = None,
) -> ConfigTestParams:
    """Create a test case with the given parameters.

    This is a convenience function for creating ConfigTestParams instances
    with a more readable interface.

    Args:
        test_id: Unique identifier for the test case
        description: Human-readable description of what the test validates
        public_config: Content for emsipi.yaml (None if file should not exist)
        private_config: Content for emsipi.private.yaml (None if file should
            not exist)
        files: Dictionary mapping relative file paths to their content
        cli_arguments: Raw CLI command text (e.g. "emsipi internal-config
            google --arg val") or None if the test should not use the CLI
        non_interactive_arguments: Non-interactive arguments to the
            internal-config command.
        environment_variables: Environment variables to set during test
        wizard_behavior: Expected wizard interaction steps as (expected_output,
            user_input) tuples
        expected_configuration: Subset of expected config values to validate
        expected_files: Dictionary mapping file paths to regex patterns for
            validation
        template_vars: Variables for template substitution in fixture files

    Returns:
        ConfigTestParams: Configured test parameters
    """

    # Convert wizard behavior tuples to WizardStep objects
    wizard_steps = wizard_behavior

    return ConfigTestParams(
        test_id=test_id,
        description=description,
        public_config=public_config,
        private_config=private_config,
        files=files,
        cli_arguments=cli_arguments or "",
        non_interactive_arguments=non_interactive_arguments,
        environment_variables=environment_variables,
        wizard_behavior=wizard_steps,
        expected_configuration=expected_configuration,
        expected_files=expected_files,
        template_vars=template_vars,
        expected_warnings=expected_warnings,
    )


class ConfigTestCase:
    """Base class for configuration test case collections.

    Subclasses should define test cases by implementing the get_test_cases
    method.
    """

    @classmethod
    def get_test_cases(cls) -> list[ConfigTestParams]:  # pragma: no cover
        """Get the list of test cases for this test class."""
        msg = "Subclasses must implement get_test_cases"
        raise NotImplementedError(msg)

    @classmethod
    def get_suite_config(cls) -> SuiteConfig:  # pragma: no cover
        """Get the test suite configuration.

        Subclasses can override this to customize test behavior.

        Returns:
            SuiteConfig: Configuration for the test suite
        """
        return DEFAULT_SUITE_CONFIG


def parametrize_config_tests(
    test_class: type[ConfigTestCase],
) -> Callable[[ConfigTestParams], None]:
    """Decorator to parametrize configuration tests.

    This decorator takes a test class that defines test cases and creates
    a parametrized pytest test function.

    Args:
        test_class: Class that implements ConfigTestCase

    Returns:
        Parametrized pytest test function
    """
    # Get test cases from the class
    test_cases = test_class.get_test_cases()
    suite_config = test_class.get_suite_config()

    # Create parametrized test function
    @pytest.mark.parametrize(
        "test_params", test_cases, ids=[case.test_id for case in test_cases]
    )
    def test_config_parametrized(test_params: ConfigTestParams) -> None:
        """Run a single parametrized configuration test.

        Args:
            test_params: Test parameters for this test case
        """
        # Create test runner
        runner = ConfigTestRunner(suite_config)

        # Run the test
        result = runner.run_single_test(test_params)

        # Assert test success
        if not result.success:  # pragma: no cover
            error_details: list[str] = []
            if result.error_message:
                error_details.append(f"Error: {result.error_message}")
            if result.validation_errors:
                error_details.append(
                    f"Validation errors: {'; '.join(result.validation_errors)}"
                )
            if result.cli_result and result.cli_result.stderr:
                error_details.append(f"CLI stderr: {result.cli_result.stderr}")

            pytest.fail(
                f"Test {test_params.test_id} failed: {'; '.join(error_details)}"
            )

    return test_config_parametrized


# Should not run in pytest, but can be used programmatically
def run_config_test_suite(  # pragma: no cover
    test_cases: list[ConfigTestParams],
    suite_config: SuiteConfig | None = None,
) -> list[ConfigTestResult]:
    """Run a configuration test suite programmatically.

    This function can be used to run configuration tests outside of pytest,
    for example in standalone scripts or integration tests.

    Args:
        test_cases: List of test parameters to execute
        suite_config: Configuration for the test suite

    Returns:
        list[ConfigTestResult]: Results of all test executions
    """
    config = suite_config or DEFAULT_SUITE_CONFIG
    runner = ConfigTestRunner(config)
    return runner.run_test_suite(test_cases)


# Convenience functions for common test patterns


def create_file_test(  # noqa: PLR0913
    test_id: str,
    description: str,
    files: dict[str, str],
    cli_args: str | None = None,
    non_interactive_arguments: InternalConfigParams | None = None,
    expected_config: dict[str, Any] | None = None,  # pyright: ignore[reportExplicitAny]
    expected_files: dict[str, list[str] | str] | None = None,
) -> ConfigTestParams:
    """Create a test case that includes file setup and validation.

    Args:
        test_id: Unique identifier for the test
        description: Description of what the test validates
        files: Files to create in the test environment
        cli_args: CLI command to execute
        non_interactive_arguments: Non-interactive arguments to the
            internal-config command.
        expected_config: Expected configuration subset
        expected_files: Expected file patterns to validate

    Returns:
        ConfigTestParams: Configured test parameters
    """
    return create_test_case(
        test_id=test_id,
        description=description,
        cli_arguments=cli_args,
        non_interactive_arguments=non_interactive_arguments,
        files=files,
        expected_configuration=expected_config,
        expected_files=expected_files,
    )
