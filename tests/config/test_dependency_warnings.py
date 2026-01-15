"""Test cases for dependency warning messages."""

from typing import override

from .config_tests_scaffolding import (
    ConfigTestCase,
    create_test_case,
    parametrize_config_tests,
)
from .params import ConfigTestParams, InternalConfigParams, SuiteConfig


class DependencyWarningTests(ConfigTestCase):
    """Test cases for dependency warning messages."""

    @classmethod
    @override
    def get_test_cases(cls) -> list[ConfigTestParams]:
        """Get test cases for dependency warnings.

        Returns:
            list[ConfigTestParams]: List of test parameters.
        """
        return [
            create_test_case(
                test_id="pyproject_with_uv_lock_warning",
                description="Test warning for pyproject.toml with uv.lock",
                non_interactive_arguments=InternalConfigParams(
                    provider="google",
                    server_file_or_command="server.py",
                ),
                files={
                    "server.py": "fixture:simple_server.py",
                    "pyproject.toml": "fixture:pyproject_basic.toml",
                    "uv.lock": "fixture:uv_lock_basic.txt",
                    "emsipi.yaml": "fixture:emsipi_simple.yaml",
                },
                expected_warnings=[
                    (
                        "Found uv.lock, pyproject.toml, and requirements.txt."
                        " Using uv.lock."
                    )
                ],
            ),
            create_test_case(
                test_id="requirements_with_pyproject_warning",
                description=(
                    "Test warning for requirements.txt with pyproject.toml"
                ),
                non_interactive_arguments=InternalConfigParams(
                    provider="google",
                    server_file_or_command="server.py",
                ),
                files={
                    "server.py": "fixture:simple_server.py",
                    "requirements.txt": "fixture:requirements_basic.txt",
                    "pyproject.toml": "fixture:pyproject_basic.toml",
                    "emsipi.yaml": "fixture:emsipi_simple_version.yaml",
                },
                expected_warnings=[
                    (
                        "Found pyproject.toml and requirements.txt. Using"
                        " pyproject.toml."
                    )
                ],
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
test_dependency_warnings = parametrize_config_tests(DependencyWarningTests)
