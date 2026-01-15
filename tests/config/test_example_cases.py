"""Example configuration test cases.

This module provides proof-of-concept test cases that demonstrate
how to use the configuration testing scaffolding.
"""

from typing import override

import rich

from .config_tests_scaffolding import (
    ConfigTestCase,
    create_file_test,
    parametrize_config_tests,
)
from .params import ConfigTestParams, InternalConfigParams, SuiteConfig
from .runner import ConfigTestRunner


class ExampleConfigTests(ConfigTestCase):
    """Example configuration test cases for demonstration."""

    @classmethod
    @override
    def get_test_cases(cls) -> list[ConfigTestParams]:
        """Get example test cases.

        Returns:
            list[ConfigTestParams]: List of example test parameters
        """
        return [
            # Test case 1: Simple configuration test with existing config files
            create_file_test(
                test_id="simple_existing_config",
                description=(
                    "Test configuration loading with existing emsipi.yaml"
                ),
                non_interactive_arguments=InternalConfigParams(
                    provider="google",
                    server_file_or_command="server.py",
                ),
                files={
                    "server.py": "fixture:simple_server.py",
                    "emsipi.yaml": "fixture:emsipi_simple.yaml",
                    "pyproject.toml": "fixture:pyproject_basic.toml",
                },
                expected_config={
                    "server_name": "test-server",
                    "runtime": "python",
                    "python_version": "3.11.0",
                    "python_dependencies_file": "pyproject.toml",
                },
            ),
            # Test case 2: Test with templating feature
            ConfigTestParams(
                test_id="templated_config_test",
                description="Test configuration with templated fixtures",
                non_interactive_arguments=InternalConfigParams(
                    provider="google",
                    server_file_or_command="server.py",
                ),
                files={
                    "server.py": "fixture:simple_server.py",
                    "emsipi.yaml": "fixture:emsipi_template.yaml",
                    "pyproject.toml": "fixture:pyproject_template.toml",
                },
                template_vars={
                    "server_name": "templated-server",
                    "project_id": "my-templated-project",
                    "region": "us-east1",
                    "project_name": "templated-server",
                    "version": "1.0.0",
                    "python_version": "3.11",
                    "fastmcp_version": "0.2.0",
                },
                expected_configuration={
                    "server_name": "templated-server",
                    "runtime": "python",
                    "python_dependencies_file": "pyproject.toml",
                },
                expected_files={
                    "emsipi.yaml": [
                        r"server-name: templated-server",
                        r"project: my-templated-project",
                        r"region: us-east1",
                    ],
                    "pyproject.toml": [
                        r'name = "templated-server"',
                        r'version = "1.0.0"',
                        r'requires-python = ">=3.11"',
                        r"fastmcp>=0.2.0",
                    ],
                },
            ),
            # Test case 3: Test with file setup and validation
            create_file_test(
                test_id="python_server_with_deps",
                description="Test Python server configuration with uv.lock",
                non_interactive_arguments=InternalConfigParams(
                    provider="google",
                    server_file_or_command="server.py",
                ),
                files={
                    "server.py": "fixture:server_with_tool.py",
                    "uv.lock": "fixture:uv_lock_basic.txt",
                    "pyproject.toml": "fixture:pyproject_with_version.toml",
                    "emsipi.yaml": "fixture:emsipi_simple.yaml",
                },
                expected_config={
                    "server_name": "test-server",
                    "runtime": "python",
                    "python_dependencies_file": "uv.lock",
                },
                expected_files={
                    "server.py": [
                        r"from fastmcp import FastMCP",
                        r"def add\(",
                    ],
                    "uv.lock": [
                        r"version = 1",  # Basic uv.lock pattern
                    ],
                },
            ),
        ]

    @classmethod
    @override
    def get_suite_config(cls) -> SuiteConfig:
        """Get test suite configuration for examples.

        Returns:
            SuiteConfig: Configuration with verbose output enabled
        """
        return SuiteConfig(
            tmp_dir_name="tmp",
            cleanup_on_success=True,
            cleanup_on_failure=False,
            timeout_seconds=10,  # Shorter timeout to avoid hanging
            verbose=True,  # Enable verbose output for debugging
        )


# Apply parametrization decorator to create pytest test function
test_example_config_cases = parametrize_config_tests(ExampleConfigTests)


# Alternative approach: Manual test cases for more complex scenarios
def test_manual_config_case() -> None:
    """Example of manually written configuration test."""

    # Create a simple manual test case (non-wizard)
    test_params = ConfigTestParams(
        test_id="manual_simple_test",
        description="Manual test without wizard interaction",
        non_interactive_arguments=InternalConfigParams(
            provider="google",
            server_file_or_command="server.py",
        ),
        files={
            "server.py": "fixture:simple_server.py",
            "emsipi.yaml": "fixture:emsipi_manual.yaml",
            "pyproject.toml": "fixture:pyproject_basic.toml",
        },
        wizard_behavior=None,
        expected_configuration={
            "server_name": "manual-test-server",
            "runtime": "python",
            "python_dependencies_file": "pyproject.toml",
        },
    )

    # Run the test
    runner = ConfigTestRunner(SuiteConfig(verbose=True, timeout_seconds=10))
    result = runner.run_single_test(test_params)

    # Assert success
    assert result.success, f"Test failed: {result.error_message}"
    assert result.cli_result is not None
    assert result.cli_result.configuration_json is not None

    # Additional assertions on the configuration
    config = result.cli_result.configuration_json
    assert config["server_name"] == "manual-test-server"
    assert config["runtime"] == "python"


if __name__ == "__main__":
    # Example of running tests programmatically
    import logging

    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Get test cases
    test_cases = ExampleConfigTests.get_test_cases()
    suite_config = ExampleConfigTests.get_suite_config()

    # Run tests
    from .config_tests_scaffolding import run_config_test_suite

    results = run_config_test_suite(test_cases, suite_config)

    # Print summary
    from .runner import ConfigTestRunner

    runner = ConfigTestRunner(suite_config)
    summary = runner.generate_summary_report(results)
    rich.print(summary)
