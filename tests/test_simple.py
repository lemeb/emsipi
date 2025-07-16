from emsipi import emsipi


def test_assert_true() -> None:
    assert True


def test_main() -> None:
    assert emsipi.main() is True
