"""Tests for Node.js-specific configuration."""

from typing import override

from .config_tests_scaffolding import (
    ConfigTestCase,
    parametrize_config_tests,
)
from .params import ConfigTestParams, InternalConfigParams, SuiteConfig


class NodeConfigTests(ConfigTestCase):
    """Tests for Node.js-specific configuration."""

    @classmethod
    @override
    def get_test_cases(cls) -> list[ConfigTestParams]:
        """Get test cases for Node.js configuration.

        Returns:
            list[ConfigTestParams]: List of test parameters.
        """
        return [
            ConfigTestParams(
                test_id="node_version_validation",
                description=(
                    "Test validation error when node_version is missing for a "
                    "Node.js project."
                ),
                non_interactive_arguments=InternalConfigParams(
                    provider="google",
                    server_file_or_command="server.js",
                ),
                public_config={
                    "server-name": "test-server",
                    "providers": {"google": {"project": "test-project"}},
                },
                files={
                    "server.js": "fixture:server_basic.js",
                    "package.json": "fixture:package_basic.json",
                },
                expected_validation_errors=[
                    "node_version is required when runtime is node"
                ],
                should_succeed=False,
            ),
            ConfigTestParams(
                test_id="node_version_with_python_runtime",
                description=(
                    "Test validation error when node_version is provided for a "
                    "Python project."
                ),
                non_interactive_arguments=InternalConfigParams(
                    provider="google",
                    server_file_or_command="server.py",
                ),
                public_config={
                    "server-name": "test-server",
                    "node-version": "20",
                    "providers": {"google": {"project": "test-project"}},
                },
                files={
                    "server.py": "fixture:simple_server.py",
                    "pyproject.toml": "fixture:pyproject_basic.toml",
                },
                expected_validation_errors=[
                    "node_version provided but runtime is not node"
                ],
                should_succeed=False,
            ),
            ConfigTestParams(
                test_id="run_npm_build_with_python_runtime",
                description=(
                    "Test validation error when run_npm_build is provided for "
                    "a Python project."
                ),
                non_interactive_arguments=InternalConfigParams(
                    provider="google",
                    server_file_or_command="server.py",
                ),
                public_config={
                    "server-name": "test-server",
                    "run-npm-build": True,
                    "providers": {"google": {"project": "test-project"}},
                },
                files={
                    "server.py": "fixture:simple_server.py",
                    "pyproject.toml": "fixture:pyproject_basic.toml",
                },
                expected_validation_errors=[
                    "run_npm_build provided but runtime is not node"
                ],
                should_succeed=False,
            ),
            ConfigTestParams(
                test_id="node_server_with_npm_build",
                description="Test Node.js server with npm build enabled.",
                non_interactive_arguments=InternalConfigParams(
                    provider="google",
                    server_file_or_command="server.js",
                ),
                public_config={
                    "server-name": "test-server",
                    "run-npm-build": True,
                    "node-version": "20",
                    "providers": {"google": {"project": "test-project"}},
                },
                files={
                    "server.js": "fixture:server_basic.js",
                    "package.json": "fixture:package_basic.json",
                },
                expected_configuration={
                    "run_npm_build": True,
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
test_node_config_cases = parametrize_config_tests(NodeConfigTests)
