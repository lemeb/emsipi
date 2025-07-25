"""Tests for environment variables configuration."""

from typing import override

from .config_tests_scaffolding import (
    ConfigTestCase,
    parametrize_config_tests,
)
from .params import ConfigTestParams, InternalConfigParams, SuiteConfig


class EnvironmentVariablesTests(ConfigTestCase):
    """Tests for environment variables configuration."""

    @classmethod
    @override
    def get_test_cases(cls) -> list[ConfigTestParams]:
        """Get test cases for environment variables configuration.

        Returns:
            list[ConfigTestParams]: List of test parameters.
        """
        return [
            ConfigTestParams(
                test_id="environment_variables_set",
                description=(
                    "Test that custom environment variables are properly "
                    "included."
                ),
                non_interactive_arguments=InternalConfigParams(
                    provider="google",
                    server_file_or_command="server.py",
                ),
                public_config={
                    "server-name": "test-server",
                    "environment-variables": {
                        "MY_ENV_VAR": "my_value",
                        "ANOTHER_VAR": "another_value",
                    },
                    "providers": {"google": {"project": "test-project"}},
                },
                files={
                    "server.py": "fixture:simple_server.py",
                    "pyproject.toml": "fixture:pyproject_basic.toml",
                },
                expected_configuration={
                    "environment_variables": {
                        "MY_ENV_VAR": "my_value",
                        "ANOTHER_VAR": "another_value",
                    }
                },
            ),
        ]

    @classmethod
    @override
    def get_suite_config(cls) -> SuiteConfig:
        """Get test suite configuration for these tests.

        Returns:
            SuiteConfig: Default suite configuration.
        """
        return SuiteConfig()


# Apply parametrization decorator to create pytest test function
test_environment_variables = parametrize_config_tests(EnvironmentVariablesTests)
