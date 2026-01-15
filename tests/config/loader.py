"""Test loader for configuration testing.

This module handles pre-loading fixture files and managing test data
according to specs/test_config.md.
"""

import logging
from pathlib import Path
from typing import Any, final

import rich

from emsipi.printshop import WARNING_RICH_PREPEND

from .params import ConfigTestParams, SuiteConfig

logger = logging.getLogger(__name__)


@final
class FixtureLoader:
    """Loads and caches fixture files for efficient test execution."""

    def __init__(self, fixtures_dir: Path) -> None:
        """Initialize the fixture loader.

        Args:
            fixtures_dir: Path to the fixtures directory
        """
        self.fixtures_dir = fixtures_dir
        self._fixture_cache: dict[str, str] = {}
        self._load_all_fixtures()

    def _load_all_fixtures(self) -> None:
        """Pre-load all fixture files into memory."""
        if not self.fixtures_dir.exists():
            rich.print(
                WARNING_RICH_PREPEND
                + f"Fixtures directory does not exist: {self.fixtures_dir}"
            )
            return

        # Load all text files in fixtures directory
        for fixture_file in self.fixtures_dir.iterdir():
            if fixture_file.is_file() and fixture_file.suffix in {
                ".txt",
                ".json",
                ".toml",
                ".yaml",
                ".yml",
                ".py",
                ".js",
            }:
                try:
                    with fixture_file.open(encoding="utf-8") as f:
                        content = f.read()
                        self._fixture_cache[fixture_file.name] = content
                        logger.debug(f"Loaded fixture: {fixture_file.name}")
                except (OSError, UnicodeDecodeError) as e:
                    rich.print(
                        WARNING_RICH_PREPEND
                        + f"Error loading fixture {fixture_file.name}: {e}"
                    )

    def get_fixture(self, filename: str) -> str:
        """Get the content of a fixture file.

        Args:
            filename: Name of the fixture file

        Returns:
            str: Content of the fixture file

        Raises:
            KeyError: If fixture file not found
        """
        if filename not in self._fixture_cache:
            msg = (
                f"Fixture file not found: {filename}. Available fixtures: "
                f"{list(self._fixture_cache.keys())}"
            )
            raise KeyError(msg)
        return self._fixture_cache[filename]

    def list_fixtures(self) -> list[str]:
        """List all available fixture files.

        Returns:
            list[str]: List of fixture filenames
        """
        return list(self._fixture_cache.keys())


@final
class ConfigTestLoader:
    """Loads and manages configuration test cases."""

    def __init__(self, suite_config: SuiteConfig | None = None) -> None:
        """Initialize the test loader.

        Args:
            suite_config: Configuration for the test suite
        """
        self.suite_config = suite_config or SuiteConfig()
        self.tests_dir = Path(__file__).parent.parent
        self.fixtures_dir = self.tests_dir / "fixtures"
        self.fixture_loader = FixtureLoader(self.fixtures_dir)

    def expand_file_references(
        self,
        files: dict[str, str] | None,
        template_vars: dict[str, str] | None = None,
    ) -> dict[str, str]:
        """Expand fixture references in file dictionary.

        This method processes file dictionaries and expands references to
        fixtures. References should be in the format "fixture:filename.ext".
        Template files can use {variable} placeholders that will be replaced
        with values from template_vars.

        Args:
            files: Dictionary mapping file paths to content or fixture
                references
            template_vars: Variables for template substitution

        Returns:
            dict[str, str]: Dictionary with fixture references expanded to
                 actual content

        Raises:
            KeyError: If fixture file not found
            ValueError: If template variable is missing
        """
        if not files:
            return {}

        template_vars = template_vars or {}
        expanded_files: dict[str, str] = {}

        for file_path, content in files.items():
            if content.startswith("fixture:"):
                # Extract fixture filename
                fixture_name = content[8:]  # Remove "fixture:" prefix
                try:
                    expanded_content = self.fixture_loader.get_fixture(
                        fixture_name
                    )

                    # Apply template substitution if needed
                    if template_vars and "{" in expanded_content:
                        try:
                            expanded_content = expanded_content.format(
                                **template_vars
                            )
                        except KeyError as e:
                            msg = (
                                f"Template variable missing for {file_path} "
                                f"(fixture: {fixture_name}): {e}"
                            )
                            raise ValueError(msg) from e

                    expanded_files[file_path] = expanded_content
                except KeyError:
                    logger.exception(
                        f"Fixture not found for {file_path}: {fixture_name}"
                    )
                    raise
            else:
                content_formatted = content
                # Apply template substitution to non-fixture content too
                if template_vars and "{" in content:
                    try:
                        content_formatted = content.format(**template_vars)
                    except KeyError as e:
                        msg = f"Template variable missing for {file_path}: {e}"
                        raise ValueError(msg) from e
                expanded_files[file_path] = content_formatted

        return expanded_files

    @staticmethod
    def process_config_references(
        config: dict[str, Any] | None,  # pyright: ignore[reportExplicitAny]
    ) -> dict[str, Any] | None:  # pyright: ignore[reportExplicitAny]
        """Process configuration dictionary to expand any fixture references.

        Args:
            config: Configuration dictionary that may contain fixture references

        Returns:
            dict[str, Any] | None: Processed configuration dictionary
        """
        if not config:
            return None

        # For now, we don't expect fixture references in config dictionaries
        # This method is here for future extensibility
        return config

    def validate_test_params(self, params: ConfigTestParams) -> None:
        """Validate test parameters and check fixture references.

        Args:
            params: Test parameters to validate

        Raises:
            ValueError: If validation fails
        """
        # Check that referenced fixtures exist
        if params.files:
            for file_path, content in params.files.items():
                if content.startswith("fixture:"):
                    fixture_name = content[8:]
                    if fixture_name not in self.fixture_loader.list_fixtures():
                        msg = (
                            f"Referenced fixture not found: {fixture_name} "
                            f"for file {file_path}"
                        )
                        raise ValueError(msg)

        # Validate CLI arguments format
        if params.cli_arguments and not params.cli_arguments.strip().startswith(
            "emsipi"
        ):
            msg = (
                "CLI arguments must start with 'emsipi': "
                f"{params.cli_arguments}"
            )
            raise ValueError(msg)

    def load_test_case(self, params: ConfigTestParams) -> ConfigTestParams:
        """Load and process a single test case.

        This method validates the test parameters and expands any fixture
        references.

        Args:
            params: Raw test parameters

        Returns:
            ConfigTestParams: Processed test parameters with expanded references
        """
        # Validate parameters
        self.validate_test_params(params)

        # Create a new instance with expanded file references
        expanded_files = self.expand_file_references(
            params.files, params.template_vars
        )
        processed_public_config = self.process_config_references(
            params.public_config
        )
        processed_private_config = self.process_config_references(
            params.private_config
        )

        return ConfigTestParams(
            test_id=params.test_id,
            description=params.description,
            public_config=processed_public_config,
            private_config=processed_private_config,
            files=expanded_files,
            cli_arguments=params.cli_arguments,
            non_interactive_arguments=params.non_interactive_arguments,
            environment_variables=params.environment_variables,
            wizard_behavior=params.wizard_behavior,
            expected_configuration=params.expected_configuration,
            expected_files=params.expected_files,
            template_vars=params.template_vars,
            expected_validation_errors=params.expected_validation_errors,
            expected_error_message=params.expected_error_message,
        )

    def load_test_cases(
        self, test_params_list: list[ConfigTestParams]
    ) -> list[ConfigTestParams]:
        """Load and process multiple test cases.

        Args:
            test_params_list: List of raw test parameters

        Returns:
            list[ConfigTestParams]: List of processed test parameters
        """
        processed_cases: list[ConfigTestParams] = []
        for params in test_params_list:
            try:
                processed_case = self.load_test_case(params)
                processed_cases.append(processed_case)
                logger.debug(f"Loaded test case: {params.test_id}")
            except Exception:
                logger.exception(f"Failed to load test case {params.test_id}")
                raise

        return processed_cases
