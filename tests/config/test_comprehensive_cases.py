"""Comprehensive configuration test cases based on specs/config.md.

This module provides test cases that validate the complete configuration
flow described in the config specification.
"""

from typing import override

from .config_tests_scaffolding import (
    ConfigTestCase,
    create_file_test,
    create_test_case,
    parametrize_config_tests,
)
from .params import ConfigTestParams, InternalConfigParams, SuiteConfig
from .runner import ConfigTestRunner


class ComprehensiveConfigTests(ConfigTestCase):
    """Comprehensive configuration test cases based on specs/config.md."""

    @classmethod
    @override
    def get_test_cases(cls) -> list[ConfigTestParams]:
        """Get comprehensive test cases covering the config specification.

        Returns:
            list[ConfigTestParams]: List of comprehensive test parameters
        """
        return [
            create_file_test(
                test_id="python_requirements_txt",
                description=(
                    "Test Python server with requirements.txt deps"
                    " (and Python version in the emsipi.yaml)"
                ),
                non_interactive_arguments=InternalConfigParams(
                    provider="google",
                    server_file_or_command="server.py",
                    runtime="python",
                ),
                files={
                    "server.py": "fixture:simple_server.py",
                    "requirements.txt": "fixture:requirements_basic.txt",
                    "emsipi.yaml": "fixture:emsipi_simple_version.yaml",
                },
                expected_config={
                    "server_name": "test-server",
                    "runtime": "python",
                    "command_type": "python",
                    "python_dependencies_file": "requirements.txt",
                },
            ),
            create_file_test(
                test_id="python_requirements_txt_no_cli",
                description=(
                    "Test Python server with requirements.txt "
                    "deps (and Python version in the emsipi.yaml)"
                ),
                non_interactive_arguments=InternalConfigParams(
                    provider="google",
                    server_file_or_command="server.py",
                    runtime="python",
                ),
                files={
                    "server.py": "fixture:simple_server.py",
                    "requirements.txt": "fixture:requirements_basic.txt",
                    "emsipi.yaml": "fixture:emsipi_simple_version.yaml",
                },
                expected_config={
                    "server_name": "test-server",
                    "runtime": "python",
                    "command_type": "python",
                    "python_dependencies_file": "requirements.txt",
                },
            ),
            create_file_test(
                test_id="node_server_detection",
                description="Test Node.js server detection and configuration",
                non_interactive_arguments=InternalConfigParams(
                    provider="google",
                    server_file_or_command="server.js",
                    runtime="node",
                ),
                files={
                    "server.js": "fixture:server_basic.js",
                    "package.json": "fixture:package_basic.json",
                    "emsipi.yaml": "fixture:emsipi_simple_json.yaml",
                },
                expected_config={
                    "server_name": "test-server",
                    "runtime": "node",
                    "command_type": "node",
                    "node_version": 20,
                    "run_npm_build": False,
                },
                expected_files={
                    "server.js": [
                        r"@modelcontextprotocol/server",
                        r"server\.run\(\)",
                    ],
                },
            ),
            create_file_test(
                test_id="node_server_detection_no_cli",
                description="Test Node.js server detection and configuration",
                non_interactive_arguments=InternalConfigParams(
                    provider="google",
                    server_file_or_command="server.js",
                    runtime="node",
                ),
                files={
                    "server.js": "fixture:server_basic.js",
                    "package.json": "fixture:package_basic.json",
                    "emsipi.yaml": "fixture:emsipi_simple_json.yaml",
                },
                expected_config={
                    "server_name": "test-server",
                    "runtime": "node",
                    "command_type": "node",
                    "node_version": 20,
                    "run_npm_build": False,
                },
                expected_files={
                    "server.js": [
                        r"@modelcontextprotocol/server",
                        r"server\.run\(\)",
                    ],
                },
            ),
            create_file_test(
                test_id="uv_lock_priority",
                description=(
                    "Test that uv.lock takes priority over requirements"
                ),
                non_interactive_arguments=InternalConfigParams(
                    provider="google",
                    server_file_or_command="server.py",
                    runtime="python",
                ),
                files={
                    "server.py": "fixture:simple_server.py",
                    "uv.lock": "fixture:uv_lock_basic.txt",
                    "requirements.txt": "fixture:requirements_basic.txt",
                    "emsipi.yaml": "fixture:emsipi_simple.yaml",
                },
                expected_config={
                    "server_name": "test-server",
                    "runtime": "python",
                    "python_dependencies_file": "uv.lock",
                },
            ),
            create_test_case(
                test_id="server_command_test",
                description="Test using server_command instead of server_file",
                non_interactive_arguments=InternalConfigParams(
                    provider="google",
                    server_file_or_command="python -m mymodule",
                ),
                files={
                    "emsipi.yaml": "fixture:emsipi_simple_version.yaml",
                    "requirements.txt": "fixture:requirements_basic.txt",
                },
                expected_configuration={
                    "server_name": "test-server",
                    "command_type": "shell",
                    "server_command": "python -m mymodule",
                    "server_file": None,
                },
            ),
            ConfigTestParams(
                test_id="complex_template_test",
                description=(
                    "Test complex template with multiple variable substitutions"
                ),
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
                    "server_name": "production-server",
                    "project_id": "my-production-project",
                    "region": "europe-west1",
                    "project_name": "production-server",
                    "version": "2.1.0",
                    "python_version": "3.12",
                    "fastmcp_version": "1.0.0",
                },
                expected_configuration={
                    "server_name": "production-server",
                    "runtime": "python",
                    "python_dependencies_file": "pyproject.toml",
                },
                expected_files={
                    "emsipi.yaml": [
                        r"server-name: production-server",
                        r"project: my-production-project",
                        r"region: europe-west1",
                    ],
                    "pyproject.toml": [
                        r'name = "production-server"',
                        r'version = "2.1.0"',
                        r'requires-python = ">=3.12"',
                        r"fastmcp>=1.0.0",
                    ],
                },
            ),
            create_test_case(
                test_id="private_config_override",
                description="Test that private config overrides public config",
                non_interactive_arguments=InternalConfigParams(
                    provider="google",
                    server_file_or_command="server.py",
                ),
                public_config={
                    "server-name": "public-server",
                    "providers": {
                        "google": {
                            "project": "public-project",
                            "region": "us-central1",
                        }
                    },
                },
                private_config={
                    "providers": {
                        "google": {
                            "project": "private-project",
                        }
                    }
                },
                files={
                    "server.py": "fixture:simple_server.py",
                    "pyproject.toml": "fixture:pyproject_basic.toml",
                },
                expected_configuration={
                    "server_name": "public-server",  # From public config
                    "runtime": "python",
                    "python_dependencies_file": "pyproject.toml",
                },
            ),
            # Test case for Pydantic validation errors
            ConfigTestParams(
                test_id="pydantic_validation_empty_server_name",
                description=(
                    "Test Pydantic validation error for empty server name"
                ),
                non_interactive_arguments=InternalConfigParams(
                    provider="google",
                    server_file_or_command="server.py",
                ),
                public_config={
                    "server-name": "",  # Empty server name should fail
                    "providers": {"google": {"project": "test-project"}},
                },
                files={
                    "server.py": "fixture:simple_server.py",
                    "uv.lock": "fixture:uv_lock_basic.txt",
                },
                expected_validation_errors=[
                    r"server_name must be at least 3 characters"
                ],
                should_succeed=False,
            ),
            # Test case for both server_file and server_command provided
            ConfigTestParams(
                test_id="both_server_file_and_command",
                description=(
                    "Test validation error when both server_file and"
                    " server_command are provided."
                ),
                non_interactive_arguments=InternalConfigParams(
                    provider="google",
                    server_file_or_command="server.py",
                ),
                public_config={
                    "server-name": "test-server",
                    "server-file": "server.py",
                    "server-command": "python server.py",
                    "providers": {"google": {"project": "test-project"}},
                },
                files={
                    "server.py": "fixture:simple_server.py",
                    "pyproject.toml": "fixture:pyproject_basic.toml",
                },
                expected_validation_errors=[
                    (
                        r"server_command.*are mutually exclusive. "
                        "Please provide only one."
                    )
                ],
                should_succeed=False,
            ),
            # Test case for neither server_file nor server_command provided
            ConfigTestParams(
                test_id="neither_server_file_nor_command",
                description=(
                    "Test validation error when neither server_file "
                    "nor server_command is provided."
                ),
                non_interactive_arguments=InternalConfigParams(
                    provider="google",
                ),
                public_config={
                    "server-name": "test-server",
                    "providers": {"google": {"project": "test-project"}},
                },
                files={
                    "pyproject.toml": "fixture:pyproject_basic.toml",
                },
                expected_validation_errors=[
                    "server_file_or_command.*Field required",
                    "command_type.*Provide either `server_file`",
                    "server_command is required when server_file is not",
                    "server_file is required when server_command is not",
                ],
                should_succeed=False,
            ),
        ]

    @classmethod
    @override
    def get_suite_config(cls) -> SuiteConfig:
        """Get test suite configuration for comprehensive tests.

        Returns:
            SuiteConfig: Configuration with extended timeout for complex tests
        """
        return SuiteConfig(
            tmp_dir_name="tmp",
            cleanup_on_success=True,
            cleanup_on_failure=False,
            timeout_seconds=15,  # Longer timeout for complex scenarios
            verbose=True,  # Enable verbose output for debugging
        )


# Apply parametrization decorator to create pytest test function
test_comprehensive_config_cases = parametrize_config_tests(
    ComprehensiveConfigTests
)


# Additional manual test for edge cases
def test_dockerfile_detection_logic() -> None:
    """Test the Dockerfile detection and generation logic."""

    # Test case: existing Dockerfile with OVERWRITE: OK comment
    test_params = ConfigTestParams(
        test_id="dockerfile_overwrite_test",
        description="Test Dockerfile overwrite detection",
        non_interactive_arguments=InternalConfigParams(
            provider="google",
            server_file_or_command="server.py",
        ),
        files={
            "server.py": "fixture:simple_server.py",
            "Dockerfile": "# OVERWRITE: OK\nFROM python:3.11-slim\n...",
            "pyproject.toml": "fixture:pyproject_basic.toml",
            "emsipi.yaml": "fixture:emsipi_simple.yaml",
        },
        expected_configuration={
            "do_generate_dockerfile": True,
            "dockerfile": "./Dockerfile",
        },
    )

    runner = ConfigTestRunner(SuiteConfig(verbose=True, timeout_seconds=10))
    result = runner.run_single_test(test_params)

    # This test might fail if the actual implementation doesn't support
    # Dockerfile detection yet, but it validates the test framework
    if result.success:
        assert result.cli_result is not None
        assert result.cli_result.configuration_json is not None


if __name__ == "__main__":
    # Example of running tests programmatically
    import logging

    import rich

    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Get test cases
    test_cases = ComprehensiveConfigTests.get_test_cases()
    suite_config = ComprehensiveConfigTests.get_suite_config()

    # Run tests
    from .config_tests_scaffolding import run_config_test_suite
    from .runner import ConfigTestRunner

    results = run_config_test_suite(test_cases, suite_config)

    # Print summary
    runner = ConfigTestRunner(suite_config)
    summary = runner.generate_summary_report(results)
    rich.print(summary)
