"""Runtime detection test cases.

This module tests runtime detection scenarios based on dependency files present.
"""

from typing import override

from .config_tests_scaffolding import ConfigTestCase, parametrize_config_tests
from .params import ConfigTestParams, InternalConfigParams, SuiteConfig


class RuntimeDetectionTests(ConfigTestCase):
    """Runtime detection test cases."""

    @classmethod
    @override
    def get_test_cases(cls) -> list[ConfigTestParams]:
        """Get runtime detection test cases.

        Returns:
            list[ConfigTestParams]: List of runtime detection test parameters
        """
        return [
            # Test project with no dependency files present
            ConfigTestParams(
                test_id="no_dependency_files_present",
                description=(
                    "Test validation error when no Python or Node.js"
                    " dependency files are present"
                ),
                non_interactive_arguments=InternalConfigParams(
                    provider="google",
                    server_file_or_command="server.py",
                    # Let runtime be auto-detected
                ),
                public_config={
                    "server-name": "test-server",
                    "providers": {"google": {"project": "test-project"}},
                },
                files={
                    "server.py": "fixture:simple_server.py",
                    # No dependency files present
                },
                should_succeed=False,
                expected_error_message=(
                    "No Python dependency file"
                    " found.*Either ensure that a dependency file is present"
                    " or set python_dependencies_file explicitly"
                ),
            ),
            # Test project with both Python and Node.js dependencies
            ConfigTestParams(
                test_id="python_and_node_deps_present",
                description=(
                    "Test validation error when both Python and"
                    " Node.js deps are present"
                ),
                non_interactive_arguments=InternalConfigParams(
                    provider="google",
                    server_file_or_command="exec-my-command",
                    # Let runtime be auto-detected
                ),
                public_config={
                    "server-name": "test-server",
                    "providers": {"google": {"project": "test-project"}},
                },
                files={},
                should_succeed=False,
                expected_error_message=(
                    "Cannot infer runtime: no Python or Node signals."
                ),
            ),
            # Test runtime auto detection for python-only project
            ConfigTestParams(
                test_id="runtime_auto_detection_python",
                description=(
                    "Test automatic runtime detection for Python-only project"
                ),
                non_interactive_arguments=InternalConfigParams(
                    provider="google",
                    server_file_or_command="server.py",
                    # Let runtime be auto-detected
                ),
                public_config={
                    "server-name": "test-server",
                    "providers": {"google": {"project": "test-project"}},
                },
                files={
                    "server.py": "fixture:simple_server.py",
                    "uv.lock": "fixture:uv_lock_basic.txt",  # Only Python deps
                    # No package.json
                },
                expected_configuration={
                    "runtime": "python",
                    "python_dependencies_file": "uv.lock",
                },
                should_succeed=True,
            ),
            # Test runtime auto detection for node-only project
            ConfigTestParams(
                test_id="runtime_auto_detection_node",
                description=(
                    "Test automatic runtime detection for Node.js-only project"
                ),
                non_interactive_arguments=InternalConfigParams(
                    provider="google",
                    server_file_or_command="server.js",
                    # Let runtime be auto-detected
                ),
                public_config={
                    "server-name": "test-server",
                    "providers": {"google": {"project": "test-project"}},
                    "node-version": "20",
                },
                files={
                    "server.js": "fixture:server_basic.js",
                    "package.json": "fixture:package_basic.json",
                },
                expected_configuration={
                    "runtime": "node",
                },
                should_succeed=True,
            ),
        ]

    @classmethod
    @override
    def get_suite_config(cls) -> SuiteConfig:
        """Get test suite configuration for runtime detection tests.

        Returns:
            SuiteConfig: Configuration for runtime detection tests
        """
        return SuiteConfig(
            tmp_dir_name="tmp",
            cleanup_on_success=True,
            cleanup_on_failure=False,
            timeout_seconds=10,
            verbose=True,
        )


# Apply parametrization decorator to create pytest test function
test_runtime_detection_cases = parametrize_config_tests(RuntimeDetectionTests)


class PythonVersionDetectionTests(ConfigTestCase):
    """Test cases for Python version detection."""

    @classmethod
    @override
    def get_test_cases(cls) -> list[ConfigTestParams]:
        """Get test cases for Python version detection.

        Returns:
            list[ConfigTestParams]: List of test parameters.
        """
        return [
            ConfigTestParams(
                test_id="python_version_from_pyproject",
                description="Test Python version detection from pyproject.toml",
                non_interactive_arguments=InternalConfigParams(
                    provider="google",
                    server_file_or_command="server.py",
                ),
                public_config={
                    "server-name": "test-server",
                    "providers": {"google": {"project": "test-project"}},
                },
                files={
                    "server.py": "fixture:simple_server.py",
                    "pyproject.toml": "fixture:pyproject_with_version.toml",
                },
                expected_configuration={
                    "python_version": "3.11.0",
                },
            ),
            ConfigTestParams(
                test_id="python_version_from_uv_lock",
                description="Test Python version detection from uv.lock",
                non_interactive_arguments=InternalConfigParams(
                    provider="google",
                    server_file_or_command="server.py",
                ),
                public_config={
                    "server-name": "test-server",
                    "providers": {"google": {"project": "test-project"}},
                },
                files={
                    "server.py": "fixture:simple_server.py",
                    "uv.lock": "fixture:uv_lock_basic.txt",
                },
                expected_configuration={
                    "python_version": "3.11.0",
                },
            ),
            ConfigTestParams(
                test_id="python_version_requirements_txt_error",
                description=(
                    "Test validation error for python_version with"
                    " requirements.txt"
                ),
                non_interactive_arguments=InternalConfigParams(
                    provider="google",
                    server_file_or_command="server.py",
                ),
                public_config={
                    "server-name": "test-server",
                    "providers": {"google": {"project": "test-project"}},
                },
                files={
                    "server.py": "fixture:simple_server.py",
                    "requirements.txt": "fixture:requirements_basic.txt",
                },
                expected_error_message=(
                    "Cannot infer python_version from requirements.txt"
                ),
                should_succeed=False,
            ),
        ]

    @classmethod
    @override
    def get_suite_config(cls) -> SuiteConfig:
        """Get test suite configuration for these tests.

        Returns:
            SuiteConfig: Configuration for the test suite.
        """
        return SuiteConfig(
            tmp_dir_name="tmp",
            cleanup_on_success=True,
            cleanup_on_failure=False,
            timeout_seconds=10,
            verbose=True,
        )


# Apply parametrization decorator to create pytest test function
test_python_version_detection_cases = parametrize_config_tests(
    PythonVersionDetectionTests
)
