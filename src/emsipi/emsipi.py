"""Main module.

Copyright (c) 2025 Leopold Mebazaa.
"""
# We allow 'print' here, but you should not use them in production code.
# ruff: noqa: T201


def main() -> bool:
    """Placeholder main function.

    Returns:
        bool: True if successful, False otherwise.
    """
    print("Hello from emsipi")
    return True


if __name__ == "__main__":
    success = main()
    print("Success!" if success else "Failure!")
