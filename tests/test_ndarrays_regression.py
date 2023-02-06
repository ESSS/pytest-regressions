import sys

import numpy as np
import pytest

from pytest_regressions.testing import check_regression_fixture_workflow


@pytest.fixture
def no_regen(ndarrays_regression, request):
    if ndarrays_regression._force_regen or request.config.getoption("force_regen"):
        pytest.fail("--force-regen should not be used on this test.")


def test_usage_workflow(pytester, monkeypatch):
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
        filename = pytester.path / "test_file" / "test_1.npz"
        return dict(np.load(str(filename)))

    def compare_arrays(obtained, expected):
        assert (obtained["data"] == expected["data"]).all()

    check_regression_fixture_workflow(
        pytester,
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
    data1 = np.full(5000, 1.1, dtype=float)
    data2 = np.arange(5000, dtype=int)
    ndarrays_regression.check({"data1": data1, "data2": data2})

    # Assertion error case 1: Data has one invalid place
    data1 = np.full(5000, 1.1, dtype=float)
    data2 = np.arange(5000, dtype=int)
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
            "  Shape: (5000,)",
            "  Number of differences: 1 / 5000 (0.0%)",
            "  Individual errors:",
            "          Index              Obtained              Expected            Difference",
            "            500    1.2000000000000002                   1.1   0.10000000000000009",
        ]
    )
    assert expected in obtained_error_msg

    # Assertion error case 2: More than one invalid data
    data1 = np.full(5000, 1.1, dtype=float)
    data2 = np.arange(5000, dtype=int)
    data1[500] += 0.1
    data1[600] += 0.2
    data2[0] += 5
    data2[700:900] += 5
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
            "  Shape: (5000,)",
            "  Number of differences: 2 / 5000 (0.0%)",
            "  Statistics are computed for differing elements only.",
            "  Stats for abs(obtained - expected):",
            "    Max:     0.19999999999999996",
            "    Mean:    0.15000000000000002",
            "    Median:  0.15000000000000002",
            "  Stats for abs(obtained - expected) / abs(expected):",
            "    Max:     0.18181818181818177",
            "    Mean:    0.13636363636363638",
            "    Median:  0.13636363636363638",
            "  Individual errors:",
            "          Index              Obtained              Expected            Difference",
            "            500    1.2000000000000002                   1.1   0.10000000000000009",
            "            600                   1.3                   1.1   0.19999999999999996",
        ]
    )
    assert expected in obtained_error_msg
    expected = "\n".join(
        [
            "data2:",
            "  Shape: (5000,)",
            "  Number of differences: 201 / 5000 (4.0%)",
            "  Statistics are computed for differing elements only.",
            "  Stats for abs(obtained - expected):",
            "    Max:     5",
            "    Mean:    5.0",
            "    Median:  5.0",
            "  Stats for abs(obtained - expected) / abs(expected):",
            "    Number of (differing) non-zero expected results: 200 / 201 (99.5%)",
            "    Relative errors are computed for the non-zero expected results.",
            "    Max:     0.007142857142857143",
            "    Mean:    0.006286830640674575",
            "    Median:  0.006253911138923655",
            "  Individual errors:",
            "    Only showing first 100 mismatches.",
            "          Index              Obtained              Expected            Difference",
            "              0                     5                     0                     5",
            "            700                   705                   700                     5",
            "            701                   706                   701                     5",
        ]
    )
    assert expected in obtained_error_msg


def test_common_case_nd(ndarrays_regression, no_regen):
    # Most common case: Data is valid, is present and should pass
    data1 = np.full((50, 20), 1.1, dtype=float)
    data2 = np.arange(60, dtype=int).reshape((3, 4, 5))
    ndarrays_regression.check({"data1": data1, "data2": data2})

    # Assertion error case 1: Data has one invalid place
    data1 = np.full((50, 20), 1.1, dtype=float)
    data2 = np.arange(60, dtype=int).reshape((3, 4, 5))
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
            "  Shape: (50, 20)",
            "  Number of differences: 1 / 1000 (0.1%)",
            "  Individual errors:",
            "          Index              Obtained              Expected            Difference",
            "        (30, 2)    1.2000000000000002                   1.1   0.10000000000000009",
        ]
    )
    assert expected in obtained_error_msg

    # Assertion error case 2: More than one invalid data
    data1 = np.full((50, 20), 1.1, dtype=float)
    data2 = np.arange(60, dtype=int).reshape((3, 4, 5))
    data1[20, 15] += 0.1
    data1[0, 9] = 1.43248324e35
    data2[:2, 0, [0, 2, 4]] += 71
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
            "  Shape: (50, 20)",
            "  Number of differences: 2 / 1000 (0.2%)",
            "  Statistics are computed for differing elements only.",
            "  Stats for abs(obtained - expected):",
            "    Max:     1.43248324e+35",
            "    Mean:    7.1624162e+34",
            "    Median:  7.1624162e+34",
            "  Stats for abs(obtained - expected) / abs(expected):",
            "    Max:     1.3022574909090907e+35",
            "    Mean:    6.511287454545454e+34",
            "    Median:  6.511287454545454e+34",
            "  Individual errors:",
            "          Index              Obtained              Expected            Difference",
            "         (0, 9)        1.43248324e+35                   1.1        1.43248324e+35",
            "       (20, 15)    1.2000000000000002                   1.1   0.10000000000000009",
        ]
    )
    assert expected in obtained_error_msg
    expected = "\n".join(
        [
            "data2:",
            "  Shape: (3, 4, 5)",
            "  Number of differences: 6 / 60 (10.0%)",
            "  Statistics are computed for differing elements only.",
            "  Stats for abs(obtained - expected):",
            "    Max:     71",
            "    Mean:    71.0",
            "    Median:  71.0",
            "  Stats for abs(obtained - expected) / abs(expected):",
            "    Number of (differing) non-zero expected results: 5 / 6 (83.3%)",
            "    Relative errors are computed for the non-zero expected results.",
            "    Max:     35.5",
            "    Mean:    12.597121212121213",
            "    Median:  3.55",
            "  Individual errors:",
            "          Index              Obtained              Expected            Difference",
            "      (0, 0, 0)                    71                     0                    71",
            "      (0, 0, 2)                    73                     2                    71",
            "      (0, 0, 4)                    75                     4                    71",
            "      (1, 0, 0)                    91                    20                    71",
            "      (1, 0, 2)                    93                    22                    71",
            "      (1, 0, 4)                    95                    24                    71",
        ]
    )
    assert expected in obtained_error_msg


def test_common_case_zero_expected(ndarrays_regression, no_regen):
    # Most common case: Data is valid, is present and should pass
    data = {"data1": np.array([0, 0, 2, 3, 0, 5, 0, 7])}
    ndarrays_regression.check(data)

    # Assertion error case: Only some zeros are not reproduced.
    data = {"data1": np.array([1, 5, 2, 3, 0, 5, 3, 7])}
    with pytest.raises(AssertionError) as excinfo:
        ndarrays_regression.check(data)
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
            "  Shape: (8,)",
            "  Number of differences: 3 / 8 (37.5%)",
            "  Statistics are computed for differing elements only.",
            "  Stats for abs(obtained - expected):",
            "    Max:     5",
            "    Mean:    3.0",
            "    Median:  3.0",
            "  Relative errors are not reported because all expected values are zero.",
            "  Individual errors:",
            "          Index              Obtained              Expected            Difference",
            "              0                     1                     0                     1",
            "              1                     5                     0                     5",
            "              6                     3                     0                     3",
        ]
    )
    assert expected in obtained_error_msg


def test_different_data_types(ndarrays_regression, no_regen):
    # Generate data with integer array.
    data = {"data1": np.array([1] * 10)}
    ndarrays_regression.check(data)

    # Run check with incompatible type.
    data = {"data1": np.array([True] * 10)}
    with pytest.raises(AssertionError) as excinfo:
        ndarrays_regression.check(data)
    obtained_error_msg = str(excinfo.value)
    expected = "\n".join(
        [
            "Data types are not the same.",
            "  key: data1",
            "  Obtained: bool",
            "  Expected: int64",
        ]
    )
    assert expected in obtained_error_msg


class Foo:
    def __init__(self, bar):
        self.bar = bar


def test_object_dtype(ndarrays_regression, no_regen):
    data1 = {"data1": np.array([Foo(i) for i in range(4)], dtype=object)}
    with pytest.raises(TypeError) as excinfo:
        ndarrays_regression.check(data1)
    obtained_error_msg = str(excinfo.value)
    expected = "\n".join(
        [
            "Only numeric or unicode data is supported on ndarrays_regression fixture.",
            "Array 'data1' with type 'object' was given.",
        ]
    )
    assert expected in obtained_error_msg


def test_integer_values_smoke_test(ndarrays_regression, no_regen):
    data1 = np.ones(11, dtype=int)
    ndarrays_regression.check({"data1": data1})


def test_float_values_smoke_test(ndarrays_regression):
    data1 = np.array([1.2345678e50, 1.2345678e-50, 0.0])
    ndarrays_regression.check({"data1": data1})


def test_bool_array(ndarrays_regression, no_regen):
    # Correct data
    data1 = np.array([False, False, False], dtype=bool)
    ndarrays_regression.check({"data1": data1})

    # Data with errors
    data1 = np.array([True, True, False], dtype=bool)
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
            "  Shape: (3,)",
            "  Number of differences: 2 / 3 (66.7%)",
            "  Individual errors:",
            "          Index              Obtained              Expected            Difference",
            "              0                  True                 False                      ",
            "              1                  True                 False                      ",
        ]
    )
    assert expected in obtained_error_msg


def test_complex_array(ndarrays_regression, no_regen):
    # Correct data
    data1 = np.array([3.0 + 2.5j, -0.5, -1.879j])
    ndarrays_regression.check({"data1": data1})

    # Data with errors
    data1 = np.array([3.0 + 2.5j, 0.5, -1.879])
    with pytest.raises(AssertionError) as excinfo:
        ndarrays_regression.check({"data1": data1})
    str(excinfo.value)
    expected = "\n".join(
        [
            "data1:",
            "  Shape: (3,)",
            "  Number of differences: 2 / 3 (66.7%)",
            "  Statistics are computed for differing elements only.",
            "  Stats for abs(obtained - expected):",
            "    Max:     2.6573072836990455",
            "    Mean:    1.8286536418495227",
            "    Median:  1.8286536418495227",
            "  Stats for abs(obtained - expected) / abs(expected):",
            "    Max:     2.0",
            "    Mean:    1.7071067811865475",
            "    Median:  1.7071067811865475",
            "  Individual errors:",
            "          Index              Obtained              Expected            Difference",
            "              1              (0.5+0j)             (-0.5+0j)                (1+0j)",
            "              2           (-1.879+0j)           (-0-1.879j)       (-1.879+1.879j)",
        ]
    )


def test_arrays_of_same_size_1d(ndarrays_regression):
    data = {
        "hello": np.zeros((1,), dtype=int),
        "world": np.zeros((1,), dtype=int),
    }
    ndarrays_regression.check(data)


def test_arrays_with_different_sizes_1d(ndarrays_regression, no_regen):
    data = {"data1": np.ones(11, dtype=np.float64)}
    ndarrays_regression.check(data)

    # Original NPY file contains 11 elements.
    data = {"data1": np.ones(10, dtype=np.float64)}
    with pytest.raises(AssertionError) as excinfo:
        ndarrays_regression.check(data)
    obtained_error_msg = str(excinfo.value)
    expected = "\n".join(
        [
            "Shapes are not the same.",
            "  Key: data1",
            "  Obtained: (10,)",
            "  Expected: (11,)",
        ]
    )
    assert expected in obtained_error_msg


def test_arrays_of_same_shape(ndarrays_regression):
    data = {
        "2d": np.zeros((3, 4), dtype=int),
        "3d": np.ones((7, 8, 9), dtype=float),
        "4d": np.full((2, 1, 1, 4), 3, dtype=int),
    }
    ndarrays_regression.check(data)


def test_arrays_with_different_shapes(ndarrays_regression):
    # Prepare data with one shape.
    data = {"2d": np.zeros((3, 4), dtype=int)}
    ndarrays_regression.check(data)

    # Check with other shape.
    data = {"2d": np.zeros((3, 2), dtype=int)}
    with pytest.raises(AssertionError) as excinfo:
        ndarrays_regression.check(data)
    obtained_error_msg = str(excinfo.value)
    expected = "\n".join(
        [
            "Shapes are not the same.",
            "  Key: 2d",
            "  Obtained: (3, 2)",
            "  Expected: (3, 4)",
        ]
    )
    assert expected in obtained_error_msg


def test_scalars(ndarrays_regression):
    # Initial data with scalars.
    data1 = {"data1": 4.0, "data2": 42}
    ndarrays_regression.check(data1)

    # Run check with non-scalar data.
    data2 = {"data1": np.array([4.0]), "data2": np.array([42, 21])}
    with pytest.raises(AssertionError) as excinfo:
        ndarrays_regression.check(data2)
    obtained_error_msg = str(excinfo.value)
    expected = "\n".join(
        [
            "Shapes are not the same.",
            "  Key: data1",
            "  Obtained: (1,)",
            "  Expected: ()",
        ]
    )
    assert expected in obtained_error_msg

    # Other test case.
    data3 = {"data1": 5.0, "data2": 21}
    with pytest.raises(AssertionError) as excinfo:
        ndarrays_regression.check(data3)
    obtained_error_msg = str(excinfo.value)
    expected = "\n".join(
        [
            "data1:",
            "  Shape: ()",
            "  Number of differences: 1 / 1 (100.0%)",
            "  Individual errors:",
            "          Index              Obtained              Expected            Difference",
            "             ()                   5.0                   4.0                   1.0",
        ]
    )
    assert expected in obtained_error_msg
    expected = "\n".join(
        [
            "data2:",
            "  Shape: ()",
            "  Number of differences: 1 / 1 (100.0%)",
            "  Individual errors:",
            "          Index              Obtained              Expected            Difference",
            "             ()                    21                    42                   -21",
        ]
    )
    assert expected in obtained_error_msg


def test_string_array(ndarrays_regression):
    # Initial data.
    data1 = {"potato": ["delicious", "nutritive", "yummy"]}
    ndarrays_regression.check(data1)

    # Run check with wrong data.
    data1 = {"potato": ["delicious", "nutritive", "yikes"]}
    with pytest.raises(AssertionError) as excinfo:
        ndarrays_regression.check(data1)
    obtained_error_msg = str(excinfo.value)
    expected = "\n".join(
        [
            "potato:",
            "  Shape: (3,)",
            "  Number of differences: 1 / 3 (33.3%)",
            "  Individual errors:",
            "          Index              Obtained              Expected            Difference",
            "              2                 yikes                 yummy                      ",
        ]
    )
    assert expected in obtained_error_msg

    # Try data with incompatible dtype
    data1 = {"potato": ["disgusting", "nutritive", "yikes"]}
    with pytest.raises(AssertionError) as excinfo:
        ndarrays_regression.check(data1)
    obtained_error_msg = str(excinfo.value)
    expected = "\n".join(
        [
            "potato:",
            "  Shape: (3,)",
            "  Number of differences: 2 / 3 (66.7%)",
            "  Individual errors:",
            "          Index              Obtained              Expected            Difference",
            "              0            disgusting             delicious                      ",
            "              2                 yikes                 yummy                      ",
        ]
    )
    assert expected in obtained_error_msg


def test_non_dict(ndarrays_regression):
    data = np.ones(shape=(10, 10))
    with pytest.raises(TypeError) as excinfo:
        ndarrays_regression.check(data)
    obtained_error_msg = str(excinfo.value)
    expected = "\n".join(
        [
            "Only dictionaries with NumPy arrays or array-like objects are supported "
            "on ndarray_regression fixture.",
            "Object with type '{}' was given.".format(
                str(type(data)),
            ),
        ]
    )
    assert expected in obtained_error_msg


def test_structured_array(ndarrays_regression):
    data = {
        "array": np.array(
            [("spam", 1, 3.0), ("egg", 0, 4.3)],
            dtype=[("item", "U5"), ("count", "i4"), ("price", "f8")],
        )
    }
    with pytest.raises(TypeError) as excinfo:
        ndarrays_regression.check(data)
    obtained_error_msg = str(excinfo.value)
    expected = "\n".join(
        [
            "Only numeric or unicode data is supported on ndarrays_regression fixture.",
            "Array 'array' with type '{}' was given.".format(data["array"].dtype),
        ]
    )
    assert expected in obtained_error_msg


def test_new_obtained(ndarrays_regression):
    # Prepare data with one array.
    data = {"ar1": np.array([2.3, 9.4])}
    ndarrays_regression.check(data)

    # Run check with two arrays.
    data = {"ar1": np.array([2.3, 9.4]), "ar2": np.array([3, 4, 9])}
    with pytest.raises(AssertionError) as excinfo:
        ndarrays_regression.check(data)
    obtained_error_msg = str(excinfo.value)
    expected = "\n".join(
        [
            "They keys in the obtained results differ from the expected results.",
            "  Matching keys: ['ar1']",
            "  New in obtained: ['ar2']",
            "  Missing from obtained: []",
        ]
    )
    assert expected in obtained_error_msg


def test_missing_obtained(ndarrays_regression):
    # Prepare data with two arrays.
    data = {"ar1": np.array([2.3, 9.4]), "ar2": np.array([3, 4, 9])}
    ndarrays_regression.check(data)

    # Run check with just one array.
    data = {"ar1": np.array([2.3, 9.4])}
    with pytest.raises(AssertionError) as excinfo:
        ndarrays_regression.check(data)
    obtained_error_msg = str(excinfo.value)
    expected = "\n".join(
        [
            "They keys in the obtained results differ from the expected results.",
            "  Matching keys: ['ar1']",
            "  New in obtained: []",
            "  Missing from obtained: ['ar2']",
        ]
    )
    assert expected in obtained_error_msg


@pytest.mark.parametrize("prefix", [True, False])
def test_corrupt_npz(ndarrays_regression, tmp_path, prefix):
    data = {"data1": np.array([4, 5])}
    fn_npz = tmp_path / "corrupt.npz"
    # Write random bytes to a file
    with open(fn_npz, "wb") as f:
        if prefix:
            f.write(b"PK\x03\x04")
        np.random.randint(0, 256, 1000, dtype=np.ubyte).tofile(f)
    with pytest.raises(IOError) as excinfo:
        ndarrays_regression.check(data, fullpath=fn_npz)
    obtained_error_msg = str(excinfo.value)
    expected = f"NPZ file {fn_npz} could not be loaded. Corrupt file?"
    assert expected in obtained_error_msg
