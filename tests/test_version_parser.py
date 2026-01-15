"""Test version parser."""

import pytest

from emsipi.config.version_parser import get_first_ok_version


class TestVersionParser:
    @pytest.mark.parametrize(
        ("specifier", "expected"),
        [
            # Basic constraints
            (">=3.8", (3, 8, 0)),
            (">3.8", (3, 8, 1)),
            (">=3.8.5", (3, 8, 5)),
            ("==3.9.2", (3, 9, 2)),
            # Range constraints
            (">=3.8,<3.10", (3, 8, 0)),
            (">=3.8.0,<3.9.0", (3, 8, 0)),
            (">=3.8.5,<3.8.10", (3, 8, 5)),
            (">3.8.0,<3.8.5", (3, 8, 1)),
            # Complex multi-constraint
            (">=3.7,!=3.8.0,<3.11", (3, 7, 0)),
            (">=3.8,!=3.8.0,!=3.8.1", (3, 8, 2)),
            (">=2.7,<3.0", (2, 7, 0)),
            (">=3.6,!=3.7.*,<4.0", (3, 6, 0)),
            # Exclusion patterns
            (">=3.8,!=3.8.*,<4.0", (3, 9, 0)),
            (">=3.8,!=3.8.0,!=3.9.0,<3.10", (3, 8, 1)),
            (">=3.0,<3.6", (3, 0, 0)),
            # Tilde requirements (compatible release)
            ("~=3.8.0", (3, 8, 0)),
            ("~=3.8.5", (3, 8, 5)),
            ("~=3.8", (3, 8, 0)),
            # Impossible constraints
            (">=4.0,<4.0", None),
            (">3.10,<3.8", None),
            ("==3.8,!=3.8", None),
            (">=5.0", None),  # No Python 5 in our candidates
            # Very specific constraints
            (">=3.8.0,<=3.8.0", (3, 8, 0)),
            (">=3.8.5,<3.8.6", (3, 8, 5)),
            (
                ">3.12.10,<3.13.0",
                (3, 12, 11),
            ),  # Assuming we have 2.7.19 in candidates
            # Edge cases with micro versions
            (">=3.8.0,!=3.8.0,!=3.8.1,!=3.8.2,<3.9", (3, 8, 3)),
            ("==2.7.14", (2, 7, 14)),
            # Multiple major versions
            (">=2.7,!=3.0.*,!=3.1.*,!=3.2.*,<3.6", (2, 7, 0)),
            # Complex real-world examples
            (">=3.7,!=3.8.0,!=3.8.1", (3, 7, 0)),
            (">=3.6,<3.8", (3, 6, 0)),
            (">=3.8,<3.11,!=3.9.7", (3, 8, 0)),
            # Wildcard exclusions
            (">=3.6,!=3.7.*,!=3.8.*", (3, 6, 0)),
            # Upper bound tests
            (">=3.8,<4", (3, 8, 0)),
            (">3.7,<3.8", (3, 7, 1)),
        ],
    )
    @staticmethod
    def test_complex_specifiers(
        specifier: str, expected: tuple[int, int, int] | None
    ) -> None:
        """Test complex version specifiers return correct version tuples."""
        result = get_first_ok_version(specifier)
        assert result == expected

    @pytest.mark.parametrize(
        ("specifier", "candidates", "expected"),
        [
            # Test with pre-release versions (should return None)
            (">=3.9", ["3.8.0", "3.9.0a1", "3.10.0"], (3, 10, 0)),
            (">=3.9.0a1", ["3.9.0a1", "3.9.0b1", "3.9.0"], (3, 9, 0)),
            (
                ">=3.9",
                ["3.9.0a1", "3.9.0b1"],
                None,
            ),  # Only pre-releases available
            # Custom candidate lists
            (">=3.8", ["3.6.0", "3.7.0"], None),
            (">=3.8", ["3.8.5", "3.9.0", "3.10.1"], (3, 8, 5)),
        ],
    )
    @staticmethod
    def test_with_custom_candidates(
        specifier: str,
        candidates: list[str],
        expected: tuple[int, int, int] | None,
    ) -> None:
        """Test with custom candidate version lists.

        Args:
            specifier: Version specifier.
            candidates: Candidate version list.
            expected: Expected version tuple.
        """
        result = get_first_ok_version(specifier, candidates)
        assert result == expected


if __name__ == "__main__":
    _ = pytest.main([__file__, "-v"])
