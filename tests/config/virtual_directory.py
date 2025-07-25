"""Virtual directory management for configuration testing.

This module provides utilities for creating and managing isolated test
environments according to specs/test_config.md.
"""

import logging
import shutil
from pathlib import Path
from typing import final

import rich
import yaml

from emsipi.printshop import WARNING_RICH_PREPEND

from .params import ConfigTestParams, SuiteConfig

logger = logging.getLogger(__name__)


@final
class VirtualDirectory:
    """Manages a virtual directory for test execution.

    This class creates an isolated temporary directory, populates it with test
    files, and provides cleanup capabilities.
    """

    def __init__(self, base_path: Path, test_id: str) -> None:
        """Initialize the virtual directory.

        Args:
            base_path: Base path for the virtual directory (usually tests/tmp)
            test_id: Unique identifier for the test case
        """
        self.base_path = base_path
        self.test_id = test_id
        self.virtual_path = base_path / test_id
        self._is_created = False

    def create(self) -> None:
        """Create the virtual directory structure."""
        if self._is_created:
            rich.print(
                WARNING_RICH_PREPEND
                + f"Virtual directory already created: {self.virtual_path}"
            )
            return

        # Ensure parent directory exists
        self.base_path.mkdir(parents=True, exist_ok=True)

        # Remove existing test directory if it exists
        if self.virtual_path.exists():
            shutil.rmtree(self.virtual_path)

        # Create the test directory
        self.virtual_path.mkdir(parents=True)
        self._is_created = True
        logger.debug(f"Created virtual directory: {self.virtual_path}")

    def populate(self, test_params: ConfigTestParams) -> None:
        """Populate the virtual directory with test files.

        Args:
            test_params: Test parameters containing file content
        """
        if not self._is_created:
            self.create()

        # Write emsipi.yaml if provided
        if test_params.public_config is not None:
            public_config_path = self.virtual_path / "emsipi.yaml"
            with public_config_path.open("w", encoding="utf-8") as f:
                yaml.dump(
                    test_params.public_config, f, default_flow_style=False
                )
            msg = (
                f"Created emsipi.yaml with {len(test_params.public_config)} "
                f"keys"
            )
            logger.debug(msg)

        # Write emsipi.private.yaml if provided
        if test_params.private_config is not None:
            private_config_path = self.virtual_path / "emsipi.private.yaml"
            with private_config_path.open("w", encoding="utf-8") as f:
                yaml.dump(
                    test_params.private_config, f, default_flow_style=False
                )
            msg = (
                f"Created emsipi.private.yaml with "
                f"{len(test_params.private_config)} keys"
            )
            logger.debug(msg)

        # Write additional files if provided
        if test_params.files:
            for file_path, content in test_params.files.items():
                full_path = self.virtual_path / file_path

                # Create parent directories if needed
                full_path.parent.mkdir(parents=True, exist_ok=True)

                # Write file content
                with full_path.open("w", encoding="utf-8") as f:
                    _ = f.write(content)
                logger.debug(f"Created file: {file_path}")

    def cleanup(self) -> None:
        """Remove the virtual directory and all its contents."""
        if self.virtual_path.exists():
            shutil.rmtree(self.virtual_path)
            logger.debug(f"Cleaned up virtual directory: {self.virtual_path}")
        self._is_created = False

    def get_path(self) -> Path:
        """Get the path to the virtual directory.

        Returns:
            Path: Path to the virtual directory
        """
        return self.virtual_path

    def file_exists(self, file_path: str) -> bool:
        """Check if a file exists in the virtual directory.

        Args:
            file_path: Relative path to the file

        Returns:
            bool: True if the file exists
        """
        return (self.virtual_path / file_path).exists()

    def read_file(self, file_path: str) -> str:
        """Read a file from the virtual directory.

        Args:
            file_path: Relative path to the file

        Returns:
            str: Content of the file

        Raises:
            FileNotFoundError: If the file doesn't exist
        """
        full_path = self.virtual_path / file_path
        if not full_path.exists():
            msg = f"File not found in virtual directory: {file_path}"
            raise FileNotFoundError(msg)

        with full_path.open(encoding="utf-8") as f:
            return f.read()

    def list_files(self) -> list[Path]:
        """List all files in the virtual directory recursively.

        Returns:
            list[Path]: List of file paths relative to the virtual directory
        """
        if not self.virtual_path.exists():
            return []

        files: list[Path] = []
        for path in self.virtual_path.rglob("*"):
            if path.is_file():
                relative_path = path.relative_to(self.virtual_path)
                files.append(relative_path)

        return sorted(files)


@final
class VirtualDirectoryManager:
    """Manages multiple virtual directories for test execution."""

    def __init__(self, suite_config: SuiteConfig) -> None:
        """Initialize the manager.

        Args:
            suite_config: Configuration for the test suite
        """
        self.suite_config = suite_config
        self.tests_dir = Path(__file__).parent.parent
        self.base_tmp_dir = self.tests_dir / suite_config.tmp_dir_name
        self._active_directories: dict[str, VirtualDirectory] = {}

    def create_virtual_directory(self, test_id: str) -> VirtualDirectory:
        """Create a new virtual directory for a test case.

        Args:
            test_id: Unique identifier for the test case

        Returns:
            VirtualDirectory: The created virtual directory
        """
        if test_id in self._active_directories:
            rich.print(
                WARNING_RICH_PREPEND
                + f"Virtual directory already exists for test: {test_id}"
            )
            return self._active_directories[test_id]

        virtual_dir = VirtualDirectory(self.base_tmp_dir, test_id)
        virtual_dir.create()
        self._active_directories[test_id] = virtual_dir

        return virtual_dir

    def cleanup_all(self) -> None:
        """Clean up all active virtual directories."""
        for test_id, virtual_dir in self._active_directories.items():
            virtual_dir.cleanup()
            logger.debug(f"Cleaned up virtual directory for test: {test_id}")

        self._active_directories.clear()

        # Remove the base tmp directory and any leftover files
        if self.base_tmp_dir.exists():
            # First try to clean up any remaining subdirectories
            for item in self.base_tmp_dir.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
                    logger.debug(f"Removed leftover directory: {item}")
                else:
                    item.unlink()
                    logger.debug(f"Removed leftover file: {item}")

            # Now remove the base directory
            if self.base_tmp_dir.exists():
                self.base_tmp_dir.rmdir()
                logger.debug(f"Removed tmp directory: {self.base_tmp_dir}")

    def cleanup_test(self, test_id: str) -> None:
        """Clean up a specific test virtual directory.

        Args:
            test_id: Identifier of the test to clean up
        """
        if test_id in self._active_directories:
            self._active_directories[test_id].cleanup()
            del self._active_directories[test_id]
            logger.debug(f"Cleaned up virtual directory for test: {test_id}")

    def get_virtual_directory(self, test_id: str) -> VirtualDirectory | None:
        """Get an existing virtual directory.

        Args:
            test_id: Identifier of the test

        Returns:
            VirtualDirectory | None: The virtual directory if it exists
        """
        return self._active_directories.get(test_id)

    def setup_test_environment(
        self, test_params: ConfigTestParams
    ) -> VirtualDirectory:
        """Set up a complete test environment for a test case.

        This method creates a virtual directory and populates it with all
        necessary files and configurations.

        Args:
            test_params: Test parameters containing the test configuration

        Returns:
            VirtualDirectory: The set up virtual directory
        """
        virtual_dir = self.create_virtual_directory(test_params.test_id)

        # Replace {virtual_dir} in configurations
        public_cfg, private_cfg = (
            test_params.public_config,
            test_params.private_config,
        )
        for cfg in (public_cfg, private_cfg):
            if cfg is not None:
                for key, value in cfg.items():
                    if isinstance(value, str) and "{virtual_dir}" in value:
                        cfg[key] = value.replace(
                            "{virtual_dir}", str(virtual_dir.get_path())
                        )

        virtual_dir.populate(test_params)

        logger.info(f"Set up test environment for: {test_params.test_id}")

        # We ensure that the directory is set to the virtual directory
        # for non-interactive arguments
        if test_params.non_interactive_arguments:
            test_params.non_interactive_arguments.directory = (
                virtual_dir.get_path()
            )

        return virtual_dir
