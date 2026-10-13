import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import pytest

from pytest_regressions.dataframe_regression import DataFrameRegressionFixture
from pytest_regressions.testing import check_regression_fixture_workflow


@pytest.fixture
def no_regen(dataframe_regression: DataFrameRegressionFixture, request):
    if dataframe_regression._force_regen or request.config.getoption("force_regen"):
        pytest.fail("--force-regen should not be used on this test.")


def test_usage_workflow(pytester, monkeypatch):
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
        filename = pytester.path / "test_file" / "test_1.csv"
        frame = pd.read_csv(str(filename))
        return {"data": frame["data"].values}

    def compare_arrays(obtained, expected):
        assert (obtained["data"] == expected["data"]).all()

    check_regression_fixture_workflow(
        pytester,
        source=source,
        data_getter=get_csv_contents,
        data_modifier=lambda: monkeypatch.setattr(
            sys, "testing_get_data", lambda: {"data": 1.2 * np.ones(50)}, raising=False
        ),
        expected_data_1={"data": 1.1 * np.ones(50)},
        expected_data_2={"data": 1.2 * np.ones(50)},
        compare_fn=compare_arrays,
    )


@pytest.mark.parametrize("column_levels", [1, 2])
@pytest.mark.parametrize("rows", [0, 1])
def test_force_regen_after_column_header_growth(pytester, column_levels, rows):
    data = [[1, 2]] if rows else []
    columns = (
        'pd.Index(["x", "y"])'
        if column_levels == 1
        else 'pd.MultiIndex.from_tuples([("a", "x"), ("a", "y")])'
    )
    source = """
        import pandas as pd

        def test_frame(dataframe_regression):
            frame = pd.DataFrame({data}, columns={columns}, dtype="int64")
            dataframe_regression.check(frame)
    """
    pytester.makepyfile(test_dataframe=source.format(data=data, columns=columns))
    result = pytester.runpytest("--regen-all")
    result.assert_outcomes(passed=1)
    baseline = pytester.path / "test_dataframe" / "test_frame.csv"
    old_contents = baseline.read_text(encoding="utf-8")

    columns = 'pd.MultiIndex.from_tuples([("a", "x", "unit"), ("a", "y", "unit")])'
    pytester.makepyfile(test_dataframe=source.format(data=data, columns=columns))
    result = pytester.runpytest()
    result.assert_outcomes(failed=1)
    assert baseline.read_text(encoding="utf-8") == old_contents

    result = pytester.runpytest("--force-regen")
    result.assert_outcomes(failed=1)
    expected_contents = ",a,a\n,x,y\n,unit,unit\n"
    if rows:
        expected_contents += "0,1,2\n"
    assert (
        baseline.read_text(encoding="utf-8") == expected_contents
    ), result.stdout.str()
    result.stdout.fnmatch_lines(
        ["*Files differ and --force-regen set, regenerating file at:*"]
    )

    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_common_cases(dataframe_regression: DataFrameRegressionFixture, no_regen):
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


def test_different_data_types(
    dataframe_regression: DataFrameRegressionFixture, no_regen
):
    # Original CSV file contains integer data
    data1 = np.array([True] * 10)
    with pytest.raises(
        AssertionError,
        match="Data type for data data1 of obtained and expected are not the same.",
    ):
        dataframe_regression.check(pd.DataFrame.from_dict({"data1": data1}))


def test_multiindex_columns_tolerance(dataframe_regression, no_regen):
    df = pd.DataFrame(
        [[1.1, 2.2], [3.3, 4.4]],
        columns=pd.MultiIndex.from_tuples([("a", "x"), ("a", "y")]),
    )
    dataframe_regression.check(df)

    df.iloc[0, 0] += 0.01
    dataframe_regression.check(df, default_tolerance=dict(atol=0.1, rtol=1e-17))

    df.iloc[0, 0] += 0.2
    with pytest.raises(AssertionError, match="Values are not sufficiently close"):
        dataframe_regression.check(df, default_tolerance=dict(atol=0.1, rtol=1e-17))


@pytest.mark.parametrize("column_levels", [1, 2, 3])
@pytest.mark.parametrize("index_name", [None, "rows"])
@pytest.mark.parametrize("index_levels", [1, 2])
def test_column_header_tolerance(
    dataframe_regression, tmp_path, column_levels, index_name, index_levels
):
    if column_levels == 1:
        columns = pd.Index(["x", "y"])
    else:
        columns = pd.MultiIndex.from_tuples(
            [tuple(["a", value, "unit"][:column_levels]) for value in ("x", "y")]
        )
    if index_levels == 1:
        index = pd.Index(["first", "second"], name=index_name)
        changed_index = pd.Index(["changed", "second"], name=index_name)
    else:
        index_names = [None, None] if index_name is None else ["group", index_name]
        index = pd.MultiIndex.from_tuples(
            [("a", "first"), ("a", "second")], names=index_names
        )
        changed_index = pd.MultiIndex.from_tuples(
            [("a", "changed"), ("a", "second")], names=index_names
        )
    df = pd.DataFrame(
        [[1.1, 2.2], [3.3, 4.4]],
        columns=columns,
        index=index,
    )
    baseline = tmp_path / "baseline.csv"
    df.to_csv(baseline, float_format="%.17g")
    dataframe_regression.check(df, fullpath=baseline)

    df.iloc[0, 0] += 0.01
    dataframe_regression.check(
        df, fullpath=baseline, default_tolerance=dict(atol=0.1, rtol=1e-17)
    )

    df.index = changed_index
    with pytest.raises(AssertionError, match="Values are not sufficiently close"):
        dataframe_regression.check(
            df, fullpath=baseline, default_tolerance=dict(atol=0.1, rtol=1e-17)
        )


@pytest.mark.parametrize("column_levels", [1, 2, 3])
@pytest.mark.parametrize("index_name", [None, "rows"])
def test_multiindex_column_tolerances(
    dataframe_regression, tmp_path, column_levels, index_name
):
    df = pd.DataFrame(
        [[1.1, 2.2], [3.3, 4.4]],
        columns=pd.MultiIndex.from_tuples(
            [
                (
                    (value,)
                    if column_levels == 1
                    else tuple(["a", value, "unit"][:column_levels])
                )
                for value in ("x", "y")
            ]
        ),
        index=pd.Index(["first", "second"], name=index_name),
    )
    baseline = tmp_path / "baseline.csv"
    df.to_csv(baseline, float_format="%.17g")
    dataframe_regression.check(df, fullpath=baseline)
    df.iloc[0, 0] += 0.01
    dataframe_regression.check(
        df,
        fullpath=baseline,
        tolerances={df.columns[0]: dict(atol=0.1, rtol=1e-17)},
        default_tolerance=dict(atol=1e-17, rtol=1e-17),
    )
    df.iloc[0, 1] += 0.01
    with pytest.raises(AssertionError) as excinfo:
        dataframe_regression.check(
            df,
            fullpath=baseline,
            tolerances={df.columns[0]: dict(atol=0.1, rtol=1e-17)},
            default_tolerance=dict(atol=1e-17, rtol=1e-17),
        )
    assert f"{df.columns[0]}:\n" not in str(excinfo.value)
    assert f"{df.columns[1]}:\n" in str(excinfo.value)


@pytest.mark.parametrize(
    "columns",
    [
        pd.MultiIndex.from_tuples([("a", "renamed"), ("a", "y")]),
        pd.MultiIndex.from_tuples([("a", "x", "unit"), ("a", "y", "unit")]),
        pd.Index(["x", "y"]),
    ],
)
def test_multiindex_column_changes(dataframe_regression, tmp_path, columns):
    df = pd.DataFrame(
        [[1.1, 2.2], [3.3, 4.4]],
        columns=pd.MultiIndex.from_tuples([("a", "x"), ("a", "y")]),
    )
    baseline = tmp_path / "baseline.csv"
    df.to_csv(baseline, float_format="%.17g")
    df.columns = columns
    with pytest.raises(
        AssertionError, match="Could not find key|Obtained and expected data shape"
    ):
        dataframe_regression.check(df, fullpath=baseline)


@pytest.mark.parametrize("index_name", [None, "rows"])
@pytest.mark.parametrize("first_value", [1, 2**53])
@pytest.mark.parametrize("column_levels", [1, 2])
def test_multiindex_integer_tolerance(
    dataframe_regression, tmp_path, index_name, first_value, column_levels
):
    df = pd.DataFrame(
        [[first_value, 2], [first_value + 2, 4]],
        columns=(
            pd.MultiIndex.from_arrays([["x", "y"]])
            if column_levels == 1
            else pd.MultiIndex.from_tuples([("a", "x"), ("a", "y")])
        ),
        index=pd.Index(["first", "second"], name=index_name),
    )
    baseline = tmp_path / "baseline.csv"
    df.to_csv(baseline)
    df.iloc[0, 0] += 1
    with pytest.raises(AssertionError, match="Values are not sufficiently close"):
        dataframe_regression.check(
            df, fullpath=baseline, default_tolerance=dict(atol=10)
        )


@pytest.mark.parametrize("index_name", [None, "rows", 0, "", "row,\nlabel"])
@pytest.mark.parametrize("index_levels", [1, 2])
@pytest.mark.parametrize("column_levels", [1, 2])
def test_multiindex_index_names(
    dataframe_regression, tmp_path, index_name, index_levels, column_levels
):
    if index_levels == 1:
        index = pd.Index(["first", "second"], name=index_name)
    else:
        index = pd.MultiIndex.from_tuples(
            [("a", "first"), ("a", "second")], names=[None, index_name]
        )
    df = pd.DataFrame(
        [[1.1, 2.2], [3.3, 4.4]],
        columns=(
            pd.MultiIndex.from_arrays([["x", "y"]], names=["group,\nlabel"])
            if column_levels == 1
            else pd.MultiIndex.from_tuples(
                [("a", "x"), ("a", "y")], names=["group,\nlabel", "value"]
            )
        ),
        index=index,
    )
    baseline = tmp_path / "baseline.csv"
    df.to_csv(baseline, float_format="%.17g")
    dataframe_regression.check(df, fullpath=baseline)
    df.iloc[0, 0] += 0.01
    dataframe_regression.check(
        df, fullpath=baseline, default_tolerance=dict(atol=0.1, rtol=1e-17)
    )

    if index_levels == 1:
        df.index.name = "changed"
    else:
        df.index = df.index.set_names([None, "changed"])
    with pytest.raises(AssertionError):
        dataframe_regression.check(
            df, fullpath=baseline, default_tolerance=dict(atol=0.1, rtol=1e-17)
        )


def test_multiindex_column_level_names(dataframe_regression, tmp_path):
    df = pd.DataFrame(
        [[1.1, 2.2], [3.3, 4.4]],
        columns=pd.MultiIndex.from_tuples(
            [("a", "x"), ("a", "y")], names=["group", "value"]
        ),
    )
    baseline = tmp_path / "baseline.csv"
    df.to_csv(baseline, float_format="%.17g")
    df.columns.names = ["changed", "value"]
    with pytest.raises(AssertionError, match="Could not find key"):
        dataframe_regression.check(df, fullpath=baseline)


@pytest.mark.parametrize("index_name", [None, "rows"])
def test_multiindex_first_row_na(dataframe_regression, tmp_path, index_name):
    df = pd.DataFrame(
        [[np.nan, np.nan], [1.1, 2.2]],
        columns=pd.MultiIndex.from_tuples([("a", "x"), ("a", "y")]),
        index=pd.Index(["first", "second"], name=index_name),
    )
    baseline = tmp_path / "baseline.csv"
    df.to_csv(baseline, float_format="%.17g")
    dataframe_regression.check(df, fullpath=baseline)
    df.iloc[1, 0] += 0.01
    dataframe_regression.check(
        df, fullpath=baseline, default_tolerance=dict(atol=0.1, rtol=1e-17)
    )
    df.index = pd.Index(["changed", "second"], name=index_name)
    with pytest.raises(AssertionError, match="Values are not sufficiently close"):
        dataframe_regression.check(
            df, fullpath=baseline, default_tolerance=dict(atol=0.1, rtol=1e-17)
        )


@pytest.mark.parametrize("index_name", [None, "rows"])
def test_multiindex_empty_numeric_frame(dataframe_regression, tmp_path, index_name):
    df = pd.DataFrame(
        np.empty((0, 2)),
        columns=pd.MultiIndex.from_tuples([("a", "x"), ("a", "y")]),
        index=pd.Index([], name=index_name),
    )
    baseline = tmp_path / "baseline.csv"
    df.to_csv(baseline, float_format="%.17g")
    dataframe_regression.check(df, fullpath=baseline)
    df.loc["first"] = [1.1, 2.2]
    with pytest.raises(AssertionError):
        dataframe_regression.check(df, fullpath=baseline)


def test_multiindex_numeric_categorical(dataframe_regression, tmp_path):
    df = pd.DataFrame(
        {("a", "x"): pd.Categorical([1, 3], categories=[1, 2, 3])},
        index=pd.Index(["first", "second"], name="rows"),
    )
    baseline = tmp_path / "baseline.csv"
    df.to_csv(baseline)
    dataframe_regression.check(df, fullpath=baseline)
    df.iloc[0, 0] = 2
    with pytest.raises(AssertionError, match="Values are not sufficiently close"):
        dataframe_regression.check(
            df, fullpath=baseline, default_tolerance=dict(atol=10)
        )


class Foo:
    def __init__(self, bar):
        self.bar = bar


@pytest.mark.parametrize(
    "array", [[np.random.randint(10, 99, 6)] * 6, [Foo(i) for i in range(4)]]
)
def test_non_numeric_data(
    dataframe_regression: DataFrameRegressionFixture, array, no_regen
):
    data1 = pd.DataFrame()
    data1["data1"] = array
    with pytest.raises(
        AssertionError,
        match="Only numeric data/datatime objects are supported on dataframe_regression fixture.\n"
        " *Array with type '%s' was given." % (str(data1["data1"].dtype),),
    ):
        dataframe_regression.check(data1)


def test_arrays_with_different_sizes(
    dataframe_regression: DataFrameRegressionFixture, no_regen
):
    data1 = np.ones(10, dtype=np.float64)
    with pytest.raises(
        AssertionError, match="Obtained and expected data shape are not the same."
    ):
        dataframe_regression.check(pd.DataFrame.from_dict({"data1": data1}))


def test_nonrange_index(dataframe_regression: DataFrameRegressionFixture, no_regen):
    data1 = pd.DataFrame({"b": ["a", "b", "c"]}, index=pd.Index([90, 91, 92], name="a"))
    dataframe_regression.check(data1)


def test_integer_values_smoke_test(
    dataframe_regression: DataFrameRegressionFixture, no_regen
):
    data1 = np.ones(11, dtype=int)
    dataframe_regression.check(pd.DataFrame.from_dict({"data1": data1}))


def test_number_formats(dataframe_regression: DataFrameRegressionFixture, no_regen):
    data1 = np.array([1.2345678e50, 1.2345678e-50, 0.0])
    dataframe_regression.check(pd.DataFrame.from_dict({"data1": data1}))


def test_bool_array(dataframe_regression: DataFrameRegressionFixture, no_regen):
    data1 = np.array([True, True, True], dtype=bool)
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
        "hello": np.zeros((1,), dtype=int),
        "world": np.zeros((1,), dtype=int),
    }
    dataframe_regression.check(pd.DataFrame.from_dict(same_size_int_arrays))


def test_string_array(dataframe_regression):
    data1 = {"potato": ["delicious", "nutritive", "yummy"]}
    dataframe_regression.check(pd.DataFrame.from_dict(data1))

    data1 = {"potato": ["delicious", "nutritive", "yikes"]}
    with pytest.raises(AssertionError) as excinfo:
        dataframe_regression.check(pd.DataFrame.from_dict(data1))
    obtained_error_msg = str(excinfo.value)
    assert "Values are not sufficiently close." in obtained_error_msg
    assert "To update values, use --force-regen option." in obtained_error_msg
    assert "2           yikes           yummy    ?" in obtained_error_msg
    assert (
        "WARNING: diffs for this kind of data type cannot be computed"
        in obtained_error_msg
    )


def test_non_pandas_dataframe(dataframe_regression):
    data = np.ones(shape=(10, 10))
    with pytest.raises(
        AssertionError,
        match="Only pandas DataFrames are supported on dataframe_regression fixture.\n"
        " *Object with type '%s' was given." % (str(type(data)),),
    ):
        dataframe_regression.check(data)


def test_dataframe_with_empty_strings(dataframe_regression):
    df = pd.DataFrame.from_records(
        [
            {"a": "a", "b": "b"},
            {"a": "a1", "b": ""},
        ]
    )

    dataframe_regression.check(df)


def test_dataframe_with_datetime(dataframe_regression):
    df = pd.DataFrame(
        [
            {
                "naive": datetime(2020, 1, 1),
                "timezone": datetime(2020, 1, 1, tzinfo=ZoneInfo("America/Sao_Paulo")),
            },
        ]
    )

    dataframe_regression.check(df)


def test_categorical(dataframe_regression: DataFrameRegressionFixture) -> None:
    """Support for categorical data columns (#197)."""
    values = [3, 3, 1, 1, 2, 0, 0, 2]
    types = pd.Categorical.from_codes(
        np.array(values),
        categories=["a", "b", "c", "d"],
    )

    df = pd.DataFrame.from_dict({"types": types})
    dataframe_regression.check(df)


def test_string_dtype(dataframe_regression: DataFrameRegressionFixture) -> None:
    """Support for pandas StringDtype columns (#208)."""
    df = pd.DataFrame(
        {
            "name": pd.Series(["Alice", "Bob", "Charlie"], dtype="string"),
            "age": [25, 30, 35],
            "city": pd.Series(["New York", "London", "Paris"], dtype="string"),
        }
    )
    dataframe_regression.check(df)


def test_string_dtype_with_na(
    dataframe_regression: DataFrameRegressionFixture,
) -> None:
    """StringDtype columns whose first value is NA are still string columns (#208)."""
    df = pd.DataFrame(
        {
            "name": pd.Series([pd.NA, "Bob", "Charlie"], dtype="string"),
        }
    )
    dataframe_regression.check(df)
