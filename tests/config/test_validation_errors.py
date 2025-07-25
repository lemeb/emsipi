from typing import override

from .config_tests_scaffolding import (
    ConfigTestCase,
    parametrize_config_tests,
)
from .params import ConfigTestParams, InternalConfigParams, SuiteConfig


class TestValidationErrors(ConfigTestCase):
    """Test cases for specific validation errors."""

    @classmethod
    @override
    def get_test_cases(cls) -> list[ConfigTestParams]:
        """Get test cases for validation errors.

        Returns:
            list[ConfigTestParams]: List of test parameters
        """
        return [
            ConfigTestParams(
                test_id="empty_project_id",
                description="Test validation error for empty project ID",
                non_interactive_arguments=InternalConfigParams(
                    provider="google",
                    server_file_or_command="server.py",
                ),
                public_config={
                    "server-name": "test-server",  # Added server-name
                    "providers": {
                        "google": {
                            "project": "",
                        }
                    },
                },
                files={
                    "server.py": "fixture:simple_server.py",
                    "pyproject.toml": "fixture:pyproject_basic.toml",
                },
                expected_validation_errors=[r"Project ID cannot be empty"],
                should_succeed=False,
            ),
            ConfigTestParams(
                test_id="empty_region",
                description="Test validation error for empty region",
                non_interactive_arguments=InternalConfigParams(
                    provider="google",
                    server_file_or_command="server.py",
                ),
                public_config={
                    "server-name": "test-server",  # Added server-name
                    "providers": {
                        "google": {
                            "project": "test-project",
                            "region": "",
                        }
                    },
                },
                files={
                    "server.py": "fixture:simple_server.py",
                    "pyproject.toml": "fixture:pyproject_basic.toml",
                },
                expected_validation_errors=[r"Region cannot be empty"],
                should_succeed=False,
            ),
            ConfigTestParams(
                test_id="dockerfile_path_is_absolute",
                description="Test when df_path.is_absolute() is True",
                non_interactive_arguments=InternalConfigParams(
                    provider="google",
                    server_file_or_command="server.py",
                ),
                public_config={
                    "server-name": "test-server",
                    "providers": {"google": {"project": "test-project"}},
                    "dockerfile": "{virtual_dir}/my_absolute_dockerfile",
                },
                files={
                    "server.py": "fixture:simple_server.py",
                    "pyproject.toml": "fixture:pyproject_basic.toml",
                    "my_absolute_dockerfile": "FROM python:3.9",
                },
                expected_configuration={
                    "dockerfile": "my_absolute_dockerfile",
                    "do_generate_dockerfile": False,
                },
            ),
        ]

    @classmethod
    @override
    def get_suite_config(cls) -> SuiteConfig:
        """Get test suite configuration for validation error tests.

        Returns:
            SuiteConfig: Configuration for these tests
        """
        return SuiteConfig(
            tmp_dir_name="tmp_validation_errors",
            cleanup_on_success=True,
            cleanup_on_failure=False,
            timeout_seconds=10,
            verbose=True,
        )


test_validation_errors = parametrize_config_tests(TestValidationErrors)
