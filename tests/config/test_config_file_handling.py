"""Tests for configuration file handling."""

from typing import override

from .config_tests_scaffolding import (
    ConfigTestCase,
    parametrize_config_tests,
)
from .params import (
    ConfigTestParams,
    InternalConfigParams,
    SuiteConfig,
    WizardStep,
)


class ConfigFileHandlingTests(ConfigTestCase):
    """Tests for configuration file handling."""

    @classmethod
    @override
    def get_test_cases(cls) -> list[ConfigTestParams]:
        """Get test cases for configuration file handling.

        Returns:
            list[ConfigTestParams]: List of test parameters.
        """
        return [
            ConfigTestParams(
                test_id="no_config_files_present",
                description=(
                    "Test that wizard mode is triggered when no config files "
                    "are present."
                ),
                cli_arguments="emsipi internal-config google server.py",
                files={
                    "server.py": "fixture:simple_server.py",
                    "pyproject.toml": "fixture:pyproject_basic.toml",
                },
                wizard_behavior=[
                    WizardStep(
                        expected_output="server_name",
                        user_input="my-test-server",
                    ),
                    WizardStep(
                        expected_output="runtime",
                        user_input="",
                    ),
                    WizardStep(
                        expected_output="python_dependencies_file",
                        user_input="",
                    ),
                    WizardStep(expected_output="python_version", user_input=""),
                ],
                expected_configuration={
                    "do_generate_config_files": True,
                    "server_name": "my-test-server",
                    "server_file": "server.py",
                },
            ),
            ConfigTestParams(
                test_id="deep_merge_private_config",
                description=(
                    "Test that private config values properly override "
                    "public config values with deep merge."
                ),
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
                            "artifact_registry": "public-repo",
                        }
                    },
                    "environment-variables": {"ENV_VAR_1": "public_value"},
                },
                private_config={
                    "server-name": "private-server",
                    "providers": {
                        "google": {
                            "project": "private-project",
                            "artifact_registry": "private-repo",
                        }
                    },
                    "environment-variables": {"ENV_VAR_2": "private_value"},
                },
                files={
                    "server.py": "fixture:simple_server.py",
                    "pyproject.toml": "fixture:pyproject_basic.toml",
                },
                expected_configuration={
                    "server_name": "private-server",
                    "providers": {
                        "google": {
                            "project": "private-project",
                            "region": "us-central1",
                            "artifact_registry": "private-repo",
                            "service_name": "private-server-service",
                        }
                    },
                    "environment_variables": {
                        "ENV_VAR_1": "public_value",
                        "ENV_VAR_2": "private_value",
                    },  # This is not a deep merge, it's a complete override
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
test_config_file_handling = parametrize_config_tests(ConfigFileHandlingTests)
