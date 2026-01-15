"""Deployment package for emsipi."""

from .base import DeploymentFactory, DeploymentProvider
from .gcp_provider import GCPProvider

# Register providers
_ = DeploymentFactory.register_provider("gcp", GCPProvider)  # pyright: ignore[reportUnknownMemberType]
_ = DeploymentFactory.register_provider("google", GCPProvider)  # pyright: ignore[reportUnknownMemberType]

__all__ = [
    "DeploymentFactory",
    "DeploymentProvider",
    "GCPProvider",
]
