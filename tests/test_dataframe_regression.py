import numpy as np
import pandas as pd
import pytest

from pytest_regressions.testing import check_regression_fixture_workflow


@pytest.fixture
def no_regen(dataframe_regression, request):
    if dataframe_regression._force_regen or request.config.getoption("force_regen"):
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
        import pandas as pd
        def test_1(dataframe_regression):
            contents = sys.testing_get_data()
            dataframe_regression.check(pd.DataFrame.from_dict(contents))
    """

    def get_csv_contents():
        filename = testdir.tmpdir / "test_file" / "test_1.csv"
        frame = pd.read_csv(str(filename))
        return {"data": frame["data"].values}

    def compare_arrays(obtained, expected):
        assert (obtained["data"] == expected["data"]).all()

    check_regression_fixture_workflow(
        testdir,
        source=source,
        data_getter=get_csv_contents,
        data_modifier=lambda: monkeypatch.setattr(
            sys, "testing_get_data", lambda: {"data": 1.2 * np.ones(50)}, raising=False
        ),
        expected_data_1={"data": 1.1 * np.ones(50)},
        expected_data_2={"data": 1.2 * np.ones(50)},
        compare_fn=compare_arrays,
    )


def test_common_cases(dataframe_regression, no_regen):
    # Most common case: Data is valid, is present and should pass
    data1 = 1.1 * np.ones(5000)
    data2 = 2.2 * np.ones(5000)
    dataframe_regression.check(pd.DataFrame.from_dict({"data1": data1, "data2": data2}))

    # Assertion error case 1: Data has one invalid place
    data1 = 1.1 * np.ones(5000)
    data2 = 2.2 * np.ones(5000)
    data1[500] += 0.1
    with pytest.raises(AssertionError) as excinfo:
        dataframe_regression.check(
            pd.DataFrame.from_dict({"data1": data1, "data2": data2})
        )
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
            "          obtained_data1       expected_data1                 diff",
            "500  1.20000000000000018  1.10000000000000009  0.10000000000000009",
        ]
    )
    # prints used to debug #3
    print()
    print(expected)
    print("-" * 200)
    print(obtained_error_msg)
    assert expected in obtained_error_msg

    # Assertion error case 2: More than one invalid data
    data1 = 1.1 * np.ones(5000)
    data2 = 2.2 * np.ones(5000)
    data1[500] += 0.1
    data1[600] += 0.2
    data2[700] += 0.3
    with pytest.raises(AssertionError) as excinfo:
        dataframe_regression.check(
            pd.DataFrame.from_dict({"data1": data1, "data2": data2})
        )
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
            "          obtained_data1       expected_data1                 diff",
            "500  1.20000000000000018  1.10000000000000009  0.10000000000000009",
            "600  1.30000000000000004  1.10000000000000009  0.19999999999999996",
        ]
    )
    assert expected in obtained_error_msg
    expected = "\n".join(
        [
            "data2:",
            "     obtained_data2       expected_data2                 diff",
            "700             2.5  2.20000000000000018  0.29999999999999982",
        ]
    )
    assert expected in obtained_error_msg

    # Assertion error case 3: More than one invalid data
    data1 = 1.1 * np.ones(5000)
    data2 = 2.2 * np.ones(5000)
    data1[500] += 0.01
    data2[500] += 0.01
    with pytest.raises(AssertionError) as excinfo:
        dataframe_regression.check(
            pd.DataFrame.from_dict({"data1": data1, "data2": data2}),
            tolerances={
                "data1": dict(atol=1e-1, rtol=1e-17),
                "data2": dict(atol=1e-17, rtol=1e-17),
            },
        )
    obtained_error_msg = str(excinfo.value)
    assert "  data1:" not in obtained_error_msg
    assert (
        "\n".join(
            [
                "Values are not sufficiently close.",
                "To update values, use --force-regen option.",
            ]
        )
        in obtained_error_msg
    )
    assert (
        "\n".join(
            [
                "data2:",
                "          obtained_data2       expected_data2                 diff",
                "500  2.20999999999999996  2.20000000000000018  0.00999999999999979",
            ]
        )
        in obtained_error_msg
    )


def test_different_data_types(dataframe_regression, no_regen):
    data1 = np.ones(10)
    # Smoke test: Should not raise any exception
    dataframe_regression.check(pd.DataFrame.from_dict({"data1": data1}))

    data2 = np.array([True] * 10)
    with pytest.raises(
        AssertionError,
        match="Data type for data data1 of obtained and expected are not the same.",
    ):
        dataframe_regression.check(pd.DataFrame.from_dict({"data1": data2}))


def test_n_dimensions(dataframe_regression, no_regen):
    A = np.array([1, 1, 2, 2, 3, 3])
    B = np.array([0, 1] * 3)
    C = [np.random.randint(10, 99, 6)] * 6
    # C contains an array of integer arrays, it have non-numeric dtype is ('object')
    data1 = pd.DataFrame(zip(A, B, C), columns=["A", "B", "C"])
    data1.set_index(["A", "B"], inplace=True)

    with pytest.raises(
        AssertionError,
        match="Only numeric data is supported on dataframe_regression fixture.",
    ):
        dataframe_regression.check(data1)


def test_arrays_with_different_sizes(dataframe_regression, no_regen):
    data1 = np.ones(10, dtype=np.float64)
    with pytest.raises(
        AssertionError, match="Obtained and expected data shape are not the same."
    ):
        dataframe_regression.check(pd.DataFrame.from_dict({"data1": data1}))


def test_integer_values_smoke_test(dataframe_regression, no_regen):
    data1 = np.ones(11, dtype=np.int)
    dataframe_regression.check(pd.DataFrame.from_dict({"data1": data1}))


def test_number_formats(dataframe_regression, no_regen):
    data1 = np.array([1.2345678e50, 1.2345678e-50, 0.0])
    dataframe_regression.check(pd.DataFrame.from_dict({"data1": data1}))


def test_bool_array(dataframe_regression, no_regen):
    data1 = np.array([True, True, True], dtype=np.bool)
    with pytest.raises(AssertionError) as excinfo:
        dataframe_regression.check(pd.DataFrame.from_dict({"data1": data1}))
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
            "   obtained_data1  expected_data1  diff",
            "0            True           False  True",
            "1            True           False  True",
            "2            True           False  True",
        ]
    )
    assert expected in obtained_error_msg


def test_arrays_of_same_size(dataframe_regression):
    same_size_int_arrays = {
        "hello": np.zeros((1,), dtype=np.int),
        "world": np.zeros((1,), dtype=np.int),
    }
    dataframe_regression.check(pd.DataFrame.from_dict(same_size_int_arrays))


def test_string_array(dataframe_regression):
    with pytest.raises(
        AssertionError,
        match="Only numeric data is supported on dataframe_regression fixture.",
    ):
        dataframe_regression.check(
            pd.DataFrame.from_dict(
                {"potato": np.array(["delicious", "nutritive", "nice"])}
            )
        )


def test_non_pandas_dataframe(dataframe_regression):
    data = np.ones(shape=(10, 10))
    with pytest.raises(
        AssertionError,
        match="Only pandas DataFrames are supported on on dataframe_regression fixture.",
    ):
        dataframe_regression.check(data)
