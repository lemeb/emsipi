"""Tests for Dockerfile detection logic."""

from typing import override

from .config_tests_scaffolding import (
    ConfigTestCase,
    create_test_case,
    parametrize_config_tests,
)
from .params import ConfigTestParams, InternalConfigParams, SuiteConfig


class DockerfileDetectionTests(ConfigTestCase):
    """Tests for Dockerfile detection logic."""

    @classmethod
    @override
    def get_test_cases(cls) -> list[ConfigTestParams]:
        """Get test cases for Dockerfile detection.

        Returns:
            list[ConfigTestParams]: List of test parameters.
        """
        return [
            create_test_case(
                test_id="dockerfile_exists_no_overwrite",
                description=(
                    "Test that an existing Dockerfile without "
                    "the overwrite comment is not regenerated."
                ),
                non_interactive_arguments=InternalConfigParams(
                    provider="google",
                    server_file_or_command="server.py",
                ),
                files={
                    "server.py": "fixture:simple_server.py",
                    "Dockerfile": "FROM python:3.11-slim",
                    "pyproject.toml": "fixture:pyproject_basic.toml",
                    "emsipi.yaml": "fixture:emsipi_simple.yaml",
                },
                expected_configuration={
                    "do_generate_dockerfile": False,
                },
            ),
            create_test_case(
                test_id="dockerfile_custom_path",
                description="Test that a custom Dockerfile path is used.",
                non_interactive_arguments=InternalConfigParams(
                    provider="google",
                    server_file_or_command="server.py",
                ),
                public_config={
                    "server-name": "test-server",
                    "dockerfile": "MyDockerfile",
                    "providers": {"google": {"project": "test-project"}},
                },
                files={
                    "server.py": "fixture:simple_server.py",
                    "MyDockerfile": "# OVERWRITE:OK\nFROM python:3.11-slim",
                    "pyproject.toml": "fixture:pyproject_basic.toml",
                },
                expected_configuration={
                    "do_generate_dockerfile": True,
                    "dockerfile": "MyDockerfile",
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
test_dockerfile_detection = parametrize_config_tests(DockerfileDetectionTests)
