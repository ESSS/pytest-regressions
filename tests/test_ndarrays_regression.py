import re

import numpy as np
import pytest

from pytest_regressions.testing import check_regression_fixture_workflow


@pytest.fixture
def no_regen(ndarrays_regression, request):
    if ndarrays_regression._force_regen or request.config.getoption("force_regen"):
        pytest.fail("--force-regen should not be used on this test.")


def test_usage_workflow(testdir, monkeypatch):
    """
    :type testdir: _pytest.pytester.TmpTestdir

    :type monkeypatch: _pytest.monkeypatch.monkeypatch
    """

    import sys

    monkeypatch.setattr(
        sys, "testing_get_data", lambda: {"data": 1.1 * np.ones(50)}, raising=False
    )
    source = """
        import sys
        def test_1(ndarrays_regression):
            contents = sys.testing_get_data()
            ndarrays_regression.check(contents)
    """

    def get_npz_contents():
        filename = testdir.tmpdir / "test_file" / "test_1.npz"
        return dict(np.load(str(filename)))

    def compare_arrays(obtained, expected):
        assert (obtained["data"] == expected["data"]).all()

    check_regression_fixture_workflow(
        testdir,
        source=source,
        data_getter=get_npz_contents,
        data_modifier=lambda: monkeypatch.setattr(
            sys, "testing_get_data", lambda: {"data": 1.2 * np.ones(50)}, raising=False
        ),
        expected_data_1={"data": 1.1 * np.ones(50)},
        expected_data_2={"data": 1.2 * np.ones(50)},
        compare_fn=compare_arrays,
    )


def test_common_case(ndarrays_regression, no_regen):
    # Most common case: Data is valid, is present and should pass
    data1 = 1.1 * np.ones(5000)
    data2 = 2.2 * np.ones(5000)
    ndarrays_regression.check({"data1": data1, "data2": data2})

    # Assertion error case 1: Data has one invalid place
    data1 = 1.1 * np.ones(5000)
    data2 = 2.2 * np.ones(5000)
    data1[500] += 0.1
    with pytest.raises(AssertionError) as excinfo:
        ndarrays_regression.check({"data1": data1, "data2": data2})
    obtained_error_msg = str(excinfo.value)
    expected = "\n".join(
        [
            "Values are not sufficiently close.",
            "To update values, use --force-regen option.",
        ]
    )
    assert expected in obtained_error_msg
    expected = "\n".join(
        [
            "data1:",
            "     Index              Obtained              Expected            Difference",
            "       500    1.2000000000000002                   1.1   0.10000000000000009",
        ]
    )
    assert expected in obtained_error_msg

    # Assertion error case 2: More than one invalid data
    data1 = 1.1 * np.ones(5000)
    data2 = 2.2 * np.ones(5000)
    data1[500] += 0.1
    data1[600] += 0.2
    data2[700] += 0.3
    with pytest.raises(AssertionError) as excinfo:
        ndarrays_regression.check({"data1": data1, "data2": data2})
    obtained_error_msg = str(excinfo.value)
    expected = "\n".join(
        [
            "Values are not sufficiently close.",
            "To update values, use --force-regen option.",
        ]
    )
    assert expected in obtained_error_msg
    expected = "\n".join(
        [
            "data1:",
            "     Index              Obtained              Expected            Difference",
            "       500    1.2000000000000002                   1.1   0.10000000000000009",
            "       600                   1.3                   1.1   0.19999999999999996",
        ]
    )
    assert expected in obtained_error_msg
    expected = "\n".join(
        [
            "data2:",
            "     Index              Obtained              Expected            Difference",
            "       700                   2.5                   2.2    0.2999999999999998",
        ]
    )
    assert expected in obtained_error_msg


def test_common_case_nd(ndarrays_regression, no_regen):
    # Most common case: Data is valid, is present and should pass
    data1 = 1.1 * np.ones((50, 20))
    data2 = 2.2 * np.ones((3, 4, 5))
    ndarrays_regression.check({"data1": data1, "data2": data2})

    # Assertion error case 1: Data has one invalid place
    data1 = 1.1 * np.ones((50, 20))
    data2 = 2.2 * np.ones((3, 4, 5))
    data1[30, 2] += 0.1
    with pytest.raises(AssertionError) as excinfo:
        ndarrays_regression.check({"data1": data1, "data2": data2})
    obtained_error_msg = str(excinfo.value)
    expected = "\n".join(
        [
            "Values are not sufficiently close.",
            "To update values, use --force-regen option.",
        ]
    )
    assert expected in obtained_error_msg
    expected = "\n".join(
        [
            "data1:",
            "     Index              Obtained              Expected            Difference",
            "      30,2    1.2000000000000002                   1.1   0.10000000000000009",
        ]
    )
    assert expected in obtained_error_msg

    # Assertion error case 2: More than one invalid data
    data1 = 1.1 * np.ones((50, 20))
    data2 = 2.2 * np.ones((3, 4, 5))
    data1[20, 15] += 0.1
    data1[0, 9] = 1.43248324e35
    data2[2, 3, 4] += 0.3
    with pytest.raises(AssertionError) as excinfo:
        ndarrays_regression.check({"data1": data1, "data2": data2})
    obtained_error_msg = str(excinfo.value)
    expected = "\n".join(
        [
            "Values are not sufficiently close.",
            "To update values, use --force-regen option.",
        ]
    )
    assert expected in obtained_error_msg
    expected = "\n".join(
        [
            "data1:",
            "     Index              Obtained              Expected            Difference",
            "       0,9        1.43248324e+35                   1.1        1.43248324e+35",
            "     20,15    1.2000000000000002                   1.1   0.10000000000000009",
        ]
    )
    assert expected in obtained_error_msg
    expected = "\n".join(
        [
            "data2:",
            "     Index              Obtained              Expected            Difference",
            "     2,3,4                   2.5                   2.2    0.2999999999999998",
        ]
    )
    assert expected in obtained_error_msg


def test_different_data_types(ndarrays_regression, no_regen):
    # Original NPZ file contains integer data
    data1 = np.array([True] * 10)
    with pytest.raises(
        AssertionError,
        match="Data types are not the same.\nkey: data1\nObtained: bool\nExpected: int64\n",
    ):
        ndarrays_regression.check({"data1": data1})


class Foo:
    def __init__(self, bar):
        self.bar = bar


def test_object_dtype(ndarrays_regression, no_regen):
    data1 = {"data1": np.array([Foo(i) for i in range(4)], dtype=object)}
    with pytest.raises(
        AssertionError,
        match="Only numeric data is supported on ndarrays_regression fixture.\n"
        " *Array 'data1' with type '%s' was given." % (str(data1["data1"].dtype),),
    ):
        ndarrays_regression.check(data1)


def test_integer_values_smoke_test(ndarrays_regression, no_regen):
    data1 = np.ones(11, dtype=int)
    ndarrays_regression.check({"data1": data1})


def test_number_formats(ndarrays_regression):
    data1 = np.array([1.2345678e50, 1.2345678e-50, 0.0])
    ndarrays_regression.check({"data1": data1})


def test_bool_array(ndarrays_regression, no_regen):
    data1 = np.array([True, True, True], dtype=bool)
    with pytest.raises(AssertionError) as excinfo:
        ndarrays_regression.check({"data1": data1})
    obtained_error_msg = str(excinfo.value)
    expected = "\n".join(
        [
            "Values are not sufficiently close.",
            "To update values, use --force-regen option.",
        ]
    )
    assert expected in obtained_error_msg
    expected = "\n".join(
        [
            "data1:",
            "     Index              Obtained              Expected            Difference",
            "         0                  True                 False                      ",
            "         1                  True                 False                      ",
            "         2                  True                 False                      ",
        ]
    )
    assert expected in obtained_error_msg


def test_arrays_of_same_size_1d(ndarrays_regression):
    same_size_int_arrays = {
        "hello": np.zeros((1,), dtype=int),
        "world": np.zeros((1,), dtype=int),
    }
    ndarrays_regression.check(same_size_int_arrays)


def test_arrays_with_different_sizes_1d(ndarrays_regression, no_regen):
    # Original NPY file contains 11 elements.
    data1 = np.ones(10, dtype=np.float64)
    expected = re.escape(
        "Shapes are not the same.\nKey: data1\nObtained: (10,)\nExpected: (11,)\n"
    )
    with pytest.raises(AssertionError, match=expected):
        ndarrays_regression.check({"data1": data1})


def test_arrays_of_same_shape(ndarrays_regression):
    same_size_int_arrays = {
        "2d": np.zeros((3, 4), dtype=int),
        "3d": np.ones((7, 8, 9), dtype=float),
        "4d": np.full((2, 1, 1, 4), 3, dtype=int),
    }
    ndarrays_regression.check(same_size_int_arrays)


def test_arrays_with_different_shapes(ndarrays_regression):
    same_size_int_arrays = {
        # Originally with shape (3, 4)
        "2d": np.zeros((3, 2), dtype=int),
    }
    with pytest.raises(AssertionError) as excinfo:
        ndarrays_regression.check(same_size_int_arrays)
    obtained_error_msg = str(excinfo.value)
    print(obtained_error_msg)
    expected = "\n".join(
        [
            "Shapes are not the same.",
            "Key: 2d",
            "Obtained: (3, 2)",
            "Expected: (3, 4)",
        ]
    )
    assert expected in obtained_error_msg


def test_string_array(ndarrays_regression):
    data1 = {"potato": ["delicious", "nutritive", "yummy"]}
    ndarrays_regression.check(data1)


def test_non_dict(ndarrays_regression):
    data = np.ones(shape=(10, 10))
    with pytest.raises(
        AssertionError,
        match="Only dictionaries with NumPy arrays or array-like objects are supported "
        "on ndarray_regression fixture.\n *Object with type '%s' was given."
        % (str(type(data)),),
    ):
        ndarrays_regression.check(data)
