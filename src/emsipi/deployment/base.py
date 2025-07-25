"""Base classes for cloud-agnostic deployment."""

from abc import ABC, abstractmethod
from typing import Any, ClassVar

from emsipi.config.config import EmsipiConfig, ProvidersConfig


class DeploymentProvider[T: ProvidersConfig](ABC):
    """Abstract base class for deployment providers."""

    config: T

    @abstractmethod
    def __init__(
        self, general_config: EmsipiConfig, provider_config: T
    ) -> None:
        """Initialize the deployment provider.

        Args:
            general_config: Emsipi configuration
            provider_config: Provider configuration
        """

    @abstractmethod
    def synth(self) -> None:
        """Synthesize the application."""

    @staticmethod
    @abstractmethod
    def get_required_config_keys() -> list[str]:
        """Get the list of required configuration keys for this provider.

        Returns:
            List of required configuration keys
        """

    @staticmethod
    @abstractmethod
    def validate_config(config: dict[str, Any]) -> None:  # pyright: ignore[reportExplicitAny]
        """Validate the provider configuration.

        Args:
            config: Provider configuration dictionary

        Raises:
            ValueError: If configuration is invalid
            TypeError: If configuration types are invalid
        """


class DeploymentFactory[T: ProvidersConfig]:
    """Factory for creating deployment providers."""

    _providers: ClassVar[dict[str, type[DeploymentProvider[T]]]] = {}  # type: ignore[misc]  # pyright: ignore[reportGeneralTypeIssues]

    @classmethod
    def register_provider(
        cls, name: str, provider_class: type[DeploymentProvider[T]]
    ) -> None:
        """Register a deployment provider.

        Args:
            name: Name of the provider
            provider_class: Provider class
        """
        cls._providers[name] = provider_class

    @classmethod
    def create_provider(
        cls,
        name: str,
        general_config: EmsipiConfig,
        provider_config: T,
    ) -> DeploymentProvider[T]:
        """Create a deployment provider instance.

        Args:
            name: Name of the provider
            general_config: Emsipi configuration
            provider_config: Provider configuration

        Returns:
            Deployment provider instance

        Raises:
            ValueError: If provider is not registered
        """
        if name not in cls._providers:
            msg = f"Unknown provider: {name}"
            raise ValueError(msg)

        provider_class = cls._providers[name]
        return provider_class(general_config, provider_config)

    @classmethod
    def get_available_providers(cls) -> list[str]:
        """Get list of available providers.

        Returns:
            List of available provider names
        """
        return list(cls._providers.keys())
