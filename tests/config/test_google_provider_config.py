"""Tests for Google Provider configuration."""

from typing import override

from .config_tests_scaffolding import (
    ConfigTestCase,
    parametrize_config_tests,
)
from .params import ConfigTestParams, InternalConfigParams, SuiteConfig


class GoogleProviderConfigTests(ConfigTestCase):
    """Tests for Google Provider configuration."""

    @classmethod
    @override
    def get_test_cases(cls) -> list[ConfigTestParams]:
        """Get test cases for Google Provider configuration.

        Returns:
            list[ConfigTestParams]: List of test parameters.
        """
        return [
            ConfigTestParams(
                test_id="google_provider_missing_project",
                description=(
                    "Test validation error when Google provider config is "
                    "missing project ID."
                ),
                non_interactive_arguments=InternalConfigParams(
                    provider="google",
                    server_file_or_command="server.py",
                ),
                public_config={
                    "server-name": "test-server",
                    "providers": {"google": {}},
                },
                files={
                    "server.py": "fixture:simple_server.py",
                    "pyproject.toml": "fixture:pyproject_basic.toml",
                },
                expected_validation_errors=[
                    "providers.*google.*project.*is required"
                ],
                should_succeed=False,
            ),
            ConfigTestParams(
                test_id="google_provider_default_values",
                description=(
                    "Test that Google provider uses default values for region, "
                    "artifact_registry, service_name."
                ),
                non_interactive_arguments=InternalConfigParams(
                    provider="google",
                    server_file_or_command="server.py",
                ),
                public_config={
                    "server-name": "test-server",
                    "providers": {"google": {"project": "my-gcp-project"}},
                },
                files={
                    "server.py": "fixture:simple_server.py",
                    "pyproject.toml": "fixture:pyproject_basic.toml",
                },
                expected_configuration={
                    "providers": {
                        "google": {
                            "project": "my-gcp-project",
                            "region": "us-central1",
                            "artifact_registry": "test-server-repo",
                            "service_name": "test-server-service",
                        }
                    }
                },
            ),
            ConfigTestParams(
                test_id="google_provider_custom_values",
                description=(
                    "Test that Google provider uses all specified custom "
                    "values."
                ),
                non_interactive_arguments=InternalConfigParams(
                    provider="google",
                    server_file_or_command="server.py",
                ),
                public_config={
                    "server-name": "test-server",
                    "providers": {
                        "google": {
                            "project": "custom-project",
                            "region": "europe-west1",
                            "artifact_registry": "custom-repo",
                            "service_name": "custom-service",
                        }
                    },
                },
                files={
                    "server.py": "fixture:simple_server.py",
                    "pyproject.toml": "fixture:pyproject_basic.toml",
                },
                expected_configuration={
                    "providers": {
                        "google": {
                            "project": "custom-project",
                            "region": "europe-west1",
                            "artifact_registry": "custom-repo",
                            "service_name": "custom-service",
                        }
                    }
                },
            ),
            ConfigTestParams(
                test_id="empty_project_id",
                description=(
                    "Test validation error when Google project ID is empty."
                ),
                non_interactive_arguments=InternalConfigParams(
                    provider="google",
                    server_file_or_command="server.py",
                ),
                public_config={
                    "server-name": "test-server",
                    "providers": {"google": {"project": ""}},
                },
                files={
                    "server.py": "fixture:simple_server.py",
                    "pyproject.toml": "fixture:pyproject_basic.toml",
                },
                expected_validation_errors=["Project ID cannot be empty"],
                should_succeed=False,
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
test_google_provider_config = parametrize_config_tests(
    GoogleProviderConfigTests
)
