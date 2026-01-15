"""Core configuration validation test cases.

This module tests basic validation scenarios for configuration parameters.
"""

from typing import override

from .config_tests_scaffolding import ConfigTestCase, parametrize_config_tests
from .params import ConfigTestParams, InternalConfigParams, SuiteConfig


class CoreValidationTests(ConfigTestCase):
    """Core configuration validation test cases."""

    @classmethod
    @override
    def get_test_cases(cls) -> list[ConfigTestParams]:
        """Get core validation test cases.

        Returns:
            list[ConfigTestParams]: List of core validation test parameters
        """
        return [
            # Test invalid server name format
            ConfigTestParams(
                test_id="invalid_server_name_format",
                description=(
                    "Test validation error for server name with"
                    " invalid characters"
                ),
                non_interactive_arguments=InternalConfigParams(
                    provider="google",
                    server_file_or_command="server.py",
                ),
                public_config={
                    "server-name": "my invalid server name!",
                    "providers": {"google": {"project": "test-project"}},
                },
                files={
                    "server.py": "fixture:simple_server.py",
                    "uv.lock": "fixture:uv_lock_basic.txt",
                },
                expected_validation_errors=[
                    (
                        r"server_name must be at least 3 characters and contain"
                        " only letters, digits, and dashes"
                    )
                ],
                should_succeed=False,
            ),
            # Test server file outside working directory
            ConfigTestParams(
                test_id="server_file_outside_working_dir",
                description=(
                    "Test validation error for server file outside"
                    " working directory"
                ),
                non_interactive_arguments=InternalConfigParams(
                    provider="google",
                    server_file_or_command="../outside.py",
                ),
                public_config={
                    "server-name": "test-server",
                    "providers": {"google": {"project": "test-project"}},
                },
                files={
                    "server.py": "fixture:simple_server.py",
                    "uv.lock": "fixture:uv_lock_basic.txt",
                },
                expected_validation_errors=[
                    r"server_file must reside within working_directory"
                ],
                should_succeed=False,
            ),
            # Test server file with invalid extension
            ConfigTestParams(
                test_id="server_file_invalid_extension",
                description=(
                    "Test validation error for server file with"
                    " invalid extension"
                ),
                non_interactive_arguments=InternalConfigParams(
                    provider="google",
                ),
                public_config={
                    "server-name": "test-server",
                    "providers": {"google": {"project": "test-project"}},
                    "server-file": "server.txt",
                },
                files={
                    "server.txt": "# This is not a valid server file",
                    "uv.lock": "fixture:uv_lock_basic.txt",
                },
                expected_validation_errors=[
                    r"server_file must end with \.py or \.js"
                ],
                should_succeed=False,
            ),
            # Test with both server_file and server_command defined
            ConfigTestParams(
                test_id="both_server_file_and_command",
                description=(
                    "Test validation error when both server_file and"
                    " server_command are set"
                ),
                non_interactive_arguments=InternalConfigParams(
                    provider="google",
                    server_file_or_command="server.py",
                ),
                public_config={
                    "server-name": "test-server",
                    "server-command": "echo 'hello'",
                    "providers": {"google": {"project": "test-project"}},
                },
                files={
                    "server.py": "fixture:simple_server.py",
                    "uv.lock": "fixture:uv_lock_basic.txt",
                },
                expected_validation_errors=[
                    "server_command and server_file are mutually exclusive."
                ],
                should_succeed=False,
            ),
            # Test with neither server_file nor server_command defined
            ConfigTestParams(
                test_id="neither_server_file_nor_command",
                description=(
                    "Test validation error when neither server_file"
                    " nor server_command is set"
                ),
                non_interactive_arguments=InternalConfigParams(
                    provider="google",
                    server_file_or_command="",
                ),
                public_config={
                    "server-name": "test-server",
                    "providers": {"google": {"project": "test-project"}},
                },
                files={"uv.lock": "fixture:uv_lock_basic.txt"},
                expected_validation_errors=[
                    (
                        r"command_type.*Provide either `server_file` or"
                        " `server_command`"
                    ),
                ],
                should_succeed=False,
            ),
        ]

    @classmethod
    @override
    def get_suite_config(cls) -> SuiteConfig:
        """Get test suite configuration for core validation tests.

        Returns:
            SuiteConfig: Configuration for validation tests
        """
        return SuiteConfig(
            tmp_dir_name="tmp",
            cleanup_on_success=True,
            cleanup_on_failure=False,
            timeout_seconds=10,
            verbose=True,
        )


# Apply parametrization decorator to create pytest test function
test_core_validation_cases = parametrize_config_tests(CoreValidationTests)
