"""Version parser."""

from functools import lru_cache

from packaging.specifiers import SpecifierSet
from packaging.version import Version

CANDIDATE_VERSIONS: list[str] = []


@lru_cache
def _get_max_micro_version(major: int, minor: int) -> int:
    max_micro = {
        (2, 7): 18,
        (3, 0): 1,
        (3, 1): 5,
        (3, 2): 6,
        (3, 3): 7,
        (3, 4): 10,
        (3, 5): 10,
        (3, 6): 15,
        (3, 7): 17,
        (3, 8): 20,
        (3, 9): 23,
        (3, 10): 18,
        (3, 11): 13,
        (3, 12): 11,
        (3, 13): 20,  # Hasn't reached EOL yet
        (3, 14): 20,  # Hasn't reached EOL yet
        (3, 15): 20,  # Hasn't reached EOL yet
    }
    return max_micro.get((major, minor), 0)


for major in range(2, 4):
    max_minor = 7 if major == 2 else 15  # noqa: PLR2004
    CANDIDATE_VERSIONS.extend(
        f"{major}.{minor}.{micro}"
        for minor in range(max_minor + 1)
        for micro in range(_get_max_micro_version(major, minor) + 1)
    )


def get_first_ok_version(
    specifier_string: str,
    candidate_versions: list[str] | None = None,
) -> tuple[int, int, int] | None:
    """
    Get the first acceptable version from a specifier.

    Args:
        specifier_string: A version specifier like ">=3.8,<4.0"
        candidate_versions: Optional list of versions to test against

    Returns:
        Tuple of (major, minor, micro) or None if no match or pre-release
    """
    spec = SpecifierSet(specifier_string)

    candidate_versions = candidate_versions or CANDIDATE_VERSIONS

    # Find first acceptable version
    for version_str in candidate_versions:
        version = Version(version_str)
        if version in spec:
            # Return None for pre-release versions (alpha/beta)
            if version.is_prerelease:
                continue
            return (version.major, version.minor, version.micro)

    return None


def get_first_ok_version_as_string(
    specifier_string: str,
    candidate_versions: list[str] | None = None,
) -> str | None:
    """Get the first acceptable version from a specifier as a string.

    Args:
        specifier_string: A version specifier like ">=3.8,<4.0"
        candidate_versions: Optional list of versions to test against

    Returns:
        String of the first acceptable version or None if no match or
            pre-release
    """
    version = get_first_ok_version(specifier_string, candidate_versions)
    return f"{version[0]}.{version[1]}.{version[2]}" if version else None
