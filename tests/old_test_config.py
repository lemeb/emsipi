"""Test script for the new Pydantic-based configuration."""

import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest
import yaml
from pydantic import ValidationError

from emsipi.config.config_old import (
    EmsipiConfig,
    EmsipiConfigLoader,
    GoogleProviderConfig,
)

ConfigData = dict[str, Any]  # pyright: ignore[reportExplicitAny]


@pytest.fixture
def valid_config_data() -> ConfigData:
    """Provide valid configuration data for testing.

    Returns:
        dict[str, Any]: Valid configuration data
    """
    return {
        "server-name": "test-server",
        "server-file": "server.py",
        "providers": {
            "google": {
                "project": "test-project",
                "region": "us-central1",
            }
        },
    }


@pytest.fixture
def temp_config_file() -> Generator[Path, Any, None]:  # pyright: ignore[reportExplicitAny]
    """Create a temporary config file for testing.

    Yields:
        Path: Path to the temporary config file
    """
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as f:
        yaml.dump(
            {
                "server-name": "test-server",
                "server-file": "server.py",
                "providers": {
                    "google": {
                        "project": "test-project",
                        "region": "us-central1",
                    }
                },
            },
            f,
        )
        config_path = Path(f.name)

    yield config_path
    config_path.unlink(missing_ok=True)


def test_valid_config_creation(valid_config_data: ConfigData) -> None:
    """Test that valid configuration can be created."""
    config = EmsipiConfig(**valid_config_data)  # pyright: ignore[reportAny]

    assert config.server_name == "test-server"
    assert config.get_default_provider() == "google"
    assert config.get_provider_config("google").project == "test-project"
    assert config.get_provider_config("google").region == "us-central1"


def test_config_with_environment_variables() -> None:
    """Test configuration with environment variables."""
    config_data = {
        "server-name": "test-server",
        "server-file": "server.py",
        "providers": {
            "google": {
                "project": "test-project",
                "region": "us-central1",
            }
        },
        "environment-variables": {
            "API_KEY": "test-key",
            "DEBUG": "true",
        },
    }

    config = EmsipiConfig(**config_data)  # type: ignore[arg-type] # pyright: ignore[reportArgumentType]

    assert config.environment_variables is not None
    assert config.environment_variables["API_KEY"] == "test-key"
    assert config.environment_variables["DEBUG"] == "true"


@pytest.mark.parametrize(
    ("invalid_config", "expected_error"),
    [
        (
            {
                "server-name": "",  # Empty server name
                "providers": {
                    "google": {
                        "project": "test-project",
                        "region": "us-central1",
                    }
                },
            },
            ValueError,
        ),
        (
            {
                "server-name": "test-server",
                "providers": {},  # No providers
            },
            ValueError,
        ),
        (
            {
                "server-name": "test-server",
                "providers": {
                    "google": {
                        "project": "",  # Empty project
                        "region": "us-central1",
                    }
                },
            },
            ValueError,
        ),
        (
            {
                "server-name": "test-server",
                "providers": {
                    "google": {
                        "project": "test-project",
                        "region": "",  # Empty region
                    }
                },
            },
            ValueError,
        ),
    ],
)
def test_invalid_config_validation(
    invalid_config: ConfigData, expected_error: type[Exception]
) -> None:
    """Test that invalid configurations raise appropriate errors."""
    with pytest.raises(expected_error):
        _ = EmsipiConfig(**invalid_config)  # pyright: ignore[reportAny]


def test_get_provider_config_valid() -> None:
    """Test getting provider configuration for valid provider."""
    config_data = {
        "server-name": "test-server",
        "server-file": "server.py",
        "providers": {
            "google": {
                "project": "test-project",
                "region": "us-central1",
            },
            "aws": {
                "project": "aws-project",
                "region": "us-east-1",
            },
        },
    }

    config = EmsipiConfig(**config_data)  # type: ignore[arg-type] # pyright: ignore[reportArgumentType]

    google_config = config.get_provider_config("google")
    assert google_config.project == "test-project"
    assert google_config.region == "us-central1"

    aws_config = config.get_provider_config("aws")
    assert aws_config.project == "aws-project"
    assert aws_config.region == "us-east-1"


def test_get_provider_config_invalid() -> None:
    """Test getting provider configuration for invalid provider."""
    config_data = {
        "server-name": "test-server",
        "server-file": "server.py",
        "providers": {
            "google": {
                "project": "test-project",
                "region": "us-central1",
            }
        },
    }

    config = EmsipiConfig(**config_data)  # type: ignore[arg-type] # pyright: ignore[reportArgumentType]

    with pytest.raises(ValueError, match="Provider 'aws' not configured"):
        _ = config.get_provider_config("aws")


def test_get_default_provider() -> None:
    """Test getting the default provider."""
    config_data = {
        "server-name": "test-server",
        "server-file": "server.py",
        "providers": {
            "google": {
                "project": "test-project",
                "region": "us-central1",
            },
            "aws": {
                "project": "aws-project",
                "region": "us-east-1",
            },
        },
    }

    config = EmsipiConfig(**config_data)  # type: ignore[arg-type] # pyright: ignore[reportArgumentType]

    # Should return the first provider in the dict
    assert config.get_default_provider() == "google"


def test_get_default_provider_no_providers() -> None:
    """Test getting default provider when no providers are configured."""
    config_data = {  # pyright: ignore[reportUnknownVariableType]
        "server-name": "test-server",
        "providers": {},
    }

    with pytest.raises(
        ValidationError, match="At least one provider must be configured"
    ):
        _ = EmsipiConfig(**config_data)  # type: ignore[arg-type] # pyright: ignore[reportArgumentType]


def test_config_loader_load_valid_config(temp_config_file: Path) -> None:
    """Test configuration loader with valid config file."""
    loader = EmsipiConfigLoader(temp_config_file)
    config = loader.load_config()

    assert config.server_name == "test-server"
    assert config.get_provider_config("google").project == "test-project"


def test_config_loader_file_not_found() -> None:
    """Test configuration loader with non-existent file."""
    non_existent_path = Path("/non/existent/path/emsipi.yaml")
    loader = EmsipiConfigLoader(non_existent_path)

    with pytest.raises(FileNotFoundError):
        _ = loader.load_config()


def test_google_provider_config_validation() -> None:
    """Test Google provider configuration validation."""
    # Test valid config
    valid_config = {
        "project": "test-project",
        "region": "us-central1",
    }

    provider_config = GoogleProviderConfig(**valid_config)
    assert provider_config.project == "test-project"
    assert provider_config.region == "us-central1"
    assert provider_config.artifact_registry is None
    assert provider_config.service_name is None


@pytest.mark.parametrize(
    ("invalid_provider_config", "expected_error"),
    [
        (
            {
                "project": "",  # Empty project
                "region": "us-central1",
            },
            ValueError,
        ),
        (
            {
                "project": "test-project",
                "region": "",  # Empty region
            },
            ValueError,
        ),
    ],
)
def test_google_provider_config_invalid(
    invalid_provider_config: ConfigData, expected_error: type[Exception]
) -> None:
    """Test Google provider configuration validation with invalid data."""
    with pytest.raises(expected_error):
        _ = GoogleProviderConfig(**invalid_provider_config)  # pyright: ignore[reportAny]


def test_environment_variables_validation() -> None:
    """Test environment variables validation."""
    config_data = {
        "server-name": "test-server",
        "server-file": "server.py",
        "providers": {
            "google": {
                "project": "test-project",
                "region": "us-central1",
            }
        },
        "environment-variables": {
            "API_KEY": "test-key",
            "DEBUG": "true",
        },
    }

    config = EmsipiConfig(**config_data)  # type: ignore[arg-type] # pyright: ignore[reportArgumentType]
    assert config.environment_variables is not None
    assert len(config.environment_variables) == len(["API_KEY", "DEBUG"])


def test_environment_variables_invalid_types() -> None:
    """Test environment variables with invalid types."""
    config_data = {
        "server-name": "test-server",
        "providers": {
            "google": {
                "project": "test-project",
                "region": "us-central1",
            }
        },
        "environment-variables": {
            "API_KEY": 123,  # Invalid: should be string
            "DEBUG": "true",
        },
    }

    with pytest.raises(
        ValidationError, match=r"Input should be a valid string"
    ):
        _ = EmsipiConfig(**config_data)  # type: ignore[arg-type] # pyright: ignore[reportArgumentType]
