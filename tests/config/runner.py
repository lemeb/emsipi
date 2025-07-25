"""Test runner that orchestrates the full test lifecycle.

This module provides the main test runner that coordinates all components
to execute configuration tests according to specs/test_config.md.
"""

import logging
import re
from typing import Any, final, override

import rich
from pydantic import ValidationError

from emsipi.printshop import WARNING_RICH_PREPEND

from .cli_executor import (
    CLIExecutionResult,
    CLIExecutor,
    WizardInteractionError,
)
from .loader import ConfigTestLoader
from .params import ConfigTestParams, SuiteConfig
from .virtual_directory import VirtualDirectory, VirtualDirectoryManager

logger = logging.getLogger(__name__)


@final
class ConfigTestResult:
    """Result of a single configuration test."""

    def __init__(  # noqa: PLR0913
        self,
        test_params: ConfigTestParams,
        error_message: str | None = None,
        cli_result: CLIExecutionResult | None = None,
        validation_errors: list[str] | None = None,
        pydantic_errors: list[str] | None = None,
        *,
        success: bool,
    ) -> None:
        """Initialize test result.

        Args:
            test_params: Test parameters that were executed
            success: Whether the test passed
            error_message: Error message if test failed
            cli_result: CLI execution result
            validation_errors: List of validation error messages
        """
        self.test_params = test_params
        self.success = success
        self.error_message = error_message
        self.cli_result = cli_result
        self.validation_errors = validation_errors or []
        self.pydantic_errors = pydantic_errors or []

    @property
    def test_id(self) -> str:
        """Get the test ID.

        Returns:
            str: Test identifier
        """
        return self.test_params.test_id

    @override
    def __repr__(self) -> str:
        """String representation of the result.

        Returns:
            str: Formatted result information
        """
        status = "PASS" if self.success else "FAIL"
        return f"ConfigTestResult({self.test_id}: {status})"


class ConfigValidator:
    """Validates configuration and file outputs from tests."""

    @staticmethod
    def validate_pydantic_errors(
        validation_error: ValidationError | None,
        expected_errors: list[str] | None,
    ) -> list[str]:
        """Validate that Pydantic validation errors match expectations.

        Args:
            validation_error: The actual ValidationError from Pydantic
            expected_errors: List of expected error message patterns

        Returns:
            list[str]: List of validation error messages (empty if valid)
        """
        errors: list[str] = []
        actual_error_messages: list[str] = []

        if expected_errors is None:
            return errors

        if validation_error is None:
            errors.append(
                "Expected Pydantic validation errors but none were raised"
            )
            return errors

        # Extract error messages from the ValidationError
        for error in validation_error.errors():
            # Construct error message similar to Pydantic's default format
            field_path = (
                ".".join(str(loc) for loc in error["loc"])
                if error["loc"]
                else "__root__"
            )
            error_msg = f"{field_path}: {error['msg']}"
            actual_error_messages.append(error_msg)

        # Check if each expected error pattern is found
        for expected_pattern in expected_errors:
            pattern_found = False
            for actual_msg in actual_error_messages:
                if re.search(expected_pattern, actual_msg, re.IGNORECASE):
                    pattern_found = True
                    break

            if not pattern_found:
                msg = (
                    f"Expected error pattern '{expected_pattern}' not found in "
                    f"actual errors: {actual_error_messages}"
                )
                errors.append(msg)

        return errors

    @staticmethod
    def validate_warnings(
        actual_warnings: list[str] | None,
        expected_warnings: list[str] | None,
    ) -> list[str]:
        """Validate that warnings match expectations.

        Args:
            actual_warnings: The actual warnings from CLI output
            expected_warnings: The expected warnings

        Returns:
            list[str]: List of validation error messages (empty if valid)
        """
        errors: list[str] = []

        if expected_warnings is None:
            return errors

        if actual_warnings is None:
            errors.append("Expected warnings but got None")
            return errors

        errors.extend(
            f"Expected warning '{w}' not found in actual warnings"
            for w in expected_warnings
            if w not in actual_warnings
        )

        return errors

    @staticmethod
    def validate_configuration(
        actual_config: dict[str, Any] | None,  # pyright: ignore[reportExplicitAny]
        expected_config: dict[str, Any] | None,  # pyright: ignore[reportExplicitAny]
    ) -> list[str]:
        """Validate the configuration output matches expectations.

        Args:
            actual_config: The actual configuration from CLI output
            expected_config: The expected configuration subset

        Returns:
            list[str]: List of validation error messages (empty if valid)
        """
        errors: list[str] = []

        if expected_config is None:
            return errors

        if actual_config is None:
            errors.append("Expected configuration output but got None")
            return errors

        # Validate each expected key-value pair
        for key, expected_value in expected_config.items():  # pyright: ignore[reportAny]
            if key not in actual_config:
                errors.append(
                    f"Expected key '{key}' not found in configuration"
                )
                continue

            actual_value = actual_config[key]  # pyright: ignore[reportAny]
            if actual_value != expected_value:
                msg = (
                    f"Configuration mismatch for '{key}': "
                    f"expected {expected_value}, got {actual_value}"
                )
                errors.append(msg)

        return errors

    @staticmethod
    def validate_files(
        virtual_dir: VirtualDirectory,
        expected_files: dict[str, list[str] | str] | None,
    ) -> list[str]:
        """Validate that generated files match expected patterns.

        Args:
            virtual_dir: Virtual directory containing the files
            expected_files: Dictionary mapping file paths to regex patterns

        Returns:
            list[str]: List of validation error messages (empty if valid)
        """
        errors: list[str] = []

        if expected_files is None:
            return errors

        for file_path, patterns in expected_files.items():
            if not virtual_dir.file_exists(file_path):
                errors.append(f"Expected file not found: {file_path}")
                continue

            try:
                file_content = virtual_dir.read_file(file_path)
                pattern_list = (
                    patterns if isinstance(patterns, list) else [patterns]
                )

                for pattern in pattern_list:
                    if not re.search(
                        pattern, file_content, re.MULTILINE | re.DOTALL
                    ):
                        msg = (
                            f"File '{file_path}' does not match pattern: "
                            f"{pattern}"
                        )
                        errors.append(msg)
            except FileNotFoundError:
                errors.append(f"Could not read expected file: {file_path}")
            except re.error as e:
                errors.append(
                    f"Invalid regex pattern for file '{file_path}': {e}"
                )

        return errors


@final
class ConfigTestRunner:
    """Main test runner for configuration tests."""

    def __init__(self, suite_config: SuiteConfig | None = None) -> None:
        """Initialize the test runner.

        Args:
            suite_config: Configuration for the test suite
        """
        self.suite_config = suite_config or SuiteConfig()
        self.test_loader = ConfigTestLoader(self.suite_config)
        self.dir_manager = VirtualDirectoryManager(self.suite_config)
        self.cli_executor = CLIExecutor(self.suite_config)
        self.validator = ConfigValidator()

    def run_single_test(  # noqa: C901, PLR0911, PLR0912, PLR0915
        self, test_params: ConfigTestParams
    ) -> ConfigTestResult:
        """Run a single configuration test.

        Args:
            test_params: Parameters for the test to run

        Returns:
            ConfigTestResult: Result of the test execution
        """
        test_id = test_params.test_id
        logger.info(f"Running test: {test_id}")

        virtual_dir: VirtualDirectory | None = None
        success = False

        try:
            # 1. Load and process test case
            processed_params = self.test_loader.load_test_case(test_params)

            # 2. Set up virtual directory
            virtual_dir = self.dir_manager.setup_test_environment(
                processed_params
            )

            # 3. Execute CLI command
            cli_result = self.cli_executor.execute_test_command(
                processed_params, virtual_dir
            )

            # 4. Handle expected validation errors
            if processed_params.expected_validation_errors is not None:
                # Test expects Pydantic validation errors
                if cli_result.validation_error is None:
                    error_msg = (
                        "Expected Pydantic validation errors but none occurred"
                    )
                    return ConfigTestResult(
                        test_params=processed_params,
                        success=False,
                        error_message=error_msg,
                        cli_result=cli_result,
                    )

                # Validate the Pydantic errors match expectations
                pydantic_validation_errors = (
                    self.validator.validate_pydantic_errors(
                        cli_result.validation_error,
                        processed_params.expected_validation_errors,
                    )
                )

                if pydantic_validation_errors:
                    error_msg = "; ".join(pydantic_validation_errors)
                    return ConfigTestResult(
                        test_params=processed_params,
                        success=False,
                        error_message=error_msg,
                        cli_result=cli_result,
                        pydantic_errors=pydantic_validation_errors,
                    )

                # Test passed - expected validation errors were found
                return ConfigTestResult(
                    test_params=processed_params,
                    success=True,
                    cli_result=cli_result,
                    pydantic_errors=[],
                )

            if processed_params.expected_error_message is not None:
                if cli_result.success:
                    error_msg = "Expected CLI command to fail but it succeeded"
                    return ConfigTestResult(
                        test_params=processed_params,
                        success=False,
                        error_message=error_msg,
                        cli_result=cli_result,
                    )
                if not cli_result.stderr:
                    error_msg = (
                        "Expected CLI command to fail with an error message, "
                        "but no stderr output was captured"
                    )
                    return ConfigTestResult(
                        test_params=processed_params,
                        success=False,
                        error_message=error_msg,
                        cli_result=cli_result,
                    )
                if not re.search(
                    processed_params.expected_error_message,
                    cli_result.stderr,
                    re.IGNORECASE,
                ):
                    error_msg = (
                        f"CLI command failed but stderr does not match "
                        f"expected pattern: "
                        f"{processed_params.expected_error_message}"
                    )
                    return ConfigTestResult(
                        test_params=processed_params,
                        success=False,
                        error_message=error_msg,
                        cli_result=cli_result,
                    )
                return ConfigTestResult(
                    test_params=processed_params,
                    success=True,
                    cli_result=cli_result,
                )

            # 5. Check for unexpected validation errors
            if cli_result.validation_error is not None:
                error_msg = (
                    f"Unexpected Pydantic validation error occurred: "
                    f"{cli_result.validation_error}"
                )
                return ConfigTestResult(
                    test_params=processed_params,
                    success=False,
                    error_message=error_msg,
                    cli_result=cli_result,
                )

            # 6. Validate CLI execution success for normal tests
            if not cli_result.success:
                error_msg = (
                    f"CLI command failed with return code "
                    f"{cli_result.return_code}. stderr: {cli_result.stderr}"
                )
                return ConfigTestResult(
                    test_params=processed_params,
                    success=False,
                    error_message=error_msg,
                    cli_result=cli_result,
                )

            # 7. Validate configuration output
            validation_errors: list[str] = []

            config_errors = self.validator.validate_configuration(
                cli_result.configuration_json,
                processed_params.expected_configuration,
            )
            validation_errors.extend(config_errors)

            # 8. Validate generated files
            file_errors = self.validator.validate_files(
                virtual_dir,
                processed_params.expected_files,
            )
            validation_errors.extend(file_errors)

            # 9. Determine test success
            success = len(validation_errors) == 0
            error_message = None if success else "; ".join(validation_errors)

            result = ConfigTestResult(
                test_params=processed_params,
                success=success,
                error_message=error_message,
                cli_result=cli_result,
                validation_errors=validation_errors,
            )

            if success:
                logger.info(f"Test {test_id} PASSED")
            else:
                rich.print(
                    WARNING_RICH_PREPEND
                    + f"Test {test_id} FAILED: {error_message}"
                )

        except WizardInteractionError as e:
            error_msg = f"Wizard interaction failed: {e}"
            msg = f"Test {test_id} FAILED: {error_msg}"
            logger.exception(msg)
            return ConfigTestResult(
                test_params=test_params,
                success=False,
                error_message=error_msg,
            )
        except Exception as e:
            error_msg = f"Test execution failed: {e}"
            logger.exception(f"Test {test_id} FAILED: {error_msg}")
            return ConfigTestResult(
                test_params=test_params,
                success=False,
                error_message=error_msg,
            )
        finally:
            # 10. Cleanup virtual directory
            if virtual_dir:
                should_cleanup = (
                    success and self.suite_config.cleanup_on_success
                ) or (not success and self.suite_config.cleanup_on_failure)
                if should_cleanup:
                    self.dir_manager.cleanup_test(test_id)

        return result

    def run_test_suite(
        self, test_cases: list[ConfigTestParams]
    ) -> list[ConfigTestResult]:
        """Run a suite of configuration tests.

        Args:
            test_cases: List of test parameters to execute

        Returns:
            list[ConfigTestResult]: Results of all test executions
        """
        logger.info(f"Running test suite with {len(test_cases)} test cases")

        results: list[ConfigTestResult] = []

        try:
            for test_params in test_cases:
                result = self.run_single_test(test_params)
                results.append(result)
        finally:
            # Always cleanup remaining directories
            self.dir_manager.cleanup_all()

        # Summary logging
        passed = sum(1 for r in results if r.success)
        failed = len(results) - passed

        logger.info(f"Test suite completed: {passed} passed, {failed} failed")

        return results

    @staticmethod
    def generate_summary_report(results: list[ConfigTestResult]) -> str:
        """Generate a summary report of test results.

        Args:
            results: List of test results

        Returns:
            str: Formatted summary report
        """
        total = len(results)
        passed = sum(1 for r in results if r.success)
        failed = total - passed

        report_lines = [
            "=" * 60,
            "CONFIGURATION TEST SUMMARY",
            "=" * 60,
            f"Total tests: {total}",
            f"Passed: {passed}",
            f"Failed: {failed}",
            f"Success rate: {(passed / total * 100):.1f}%"
            if total > 0
            else "N/A",
            "",
        ]

        if failed > 0:
            report_lines.extend(
                [
                    "FAILED TESTS:",
                    "-" * 20,
                ]
            )

            for result in results:
                if not result.success:
                    report_lines.extend(
                        [
                            f"• {result.test_id}: {result.error_message}",
                            f"  Description: {result.test_params.description}",
                            "",
                        ]
                    )

        return "\n".join(report_lines)
