from pathlib import Path

import pytest


def test_foo(datadir, num_regression):
    """
    Dumb test, just to generate a expected csv file that must be different from the one gathered
    from `TestClass::test_foo`.
    """
    data = {"ones": [1, 1, 1, 1], "zeros": [0, 0, 0, 0]}
    num_regression.check(data)

    expected_filename = f"{test_foo.__name__}.csv"
    obtained_filename = f"{test_foo.__name__}.obtained.csv"
    assert (datadir / expected_filename).exists()
    assert (datadir / obtained_filename).exists()


class TestClass:
    def test_foo(self, datadir, num_regression):
        """
        Since 2.2.1, pytest-regressions use the test class name to compose the name of the datafiles, by default.
        This tests asserts this behavior.
        """
        data = {"twos": [2, 2, 2, 2], "threes": [3, 3, 3, 3]}

        # equivalent to use "--with-test-class-names" parameter
        num_regression._with_test_class_names = True
        num_regression.check(data)

        expected_filename = f"{TestClass.__name__}_{TestClass.test_foo.__name__}.csv"
        obtained_filename = (
            f"{TestClass.__name__}_{TestClass.test_foo.__name__}.obtained.csv"
        )
        assert (datadir / expected_filename).exists()
        assert (datadir / obtained_filename).exists()


class TestClassWithIgnoredName:
    def test_foo(self, datadir, num_regression):
        """
        Specifies to not use the class name to compose the expected data filename. The filename coincides with the
        expected data filename used by `test_foo` function. The regression test then fails because the expected
        data is different.
        """
        data = {"fours": [4, 4, 4, 4], "fives": [5, 5, 5, 5]}

        # Trying to compare this data with `test_foo` expected data.
        with pytest.raises(AssertionError):
            num_regression.check(data)

        # Assert that we have the expected names, without class name
        expected_filename = f"{TestClassWithIgnoredName.test_foo.__name__}.csv"
        obtained_filename = f"{TestClassWithIgnoredName.test_foo.__name__}.obtained.csv"
        assert (datadir / expected_filename).exists()
        assert (datadir / obtained_filename).exists()

        # Assert that don't have files with class name
        expected_with_class_name = f"{TestClassWithIgnoredName.__name__}_{TestClassWithIgnoredName.test_foo.__name__}.csv"
        obtained_with_class_name = f"{TestClassWithIgnoredName.__name__}_{TestClassWithIgnoredName.test_foo.__name__}.obtained.csv"
        assert not (datadir / expected_with_class_name).exists()
        assert not (datadir / obtained_with_class_name).exists()
