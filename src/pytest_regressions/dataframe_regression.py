from pytest_regressions.common import import_error_message
from pytest_regressions.common import perform_regression_check


class DataFrameRegressionFixture:
    """
    Pandas DataFrame Regression fixture implementation used on dataframe_regression fixture.
    """

    DISPLAY_PRECISION = 17  # Decimal places
    DISPLAY_WIDTH = 1000  # Max. Chars on outputs
    DISPLAY_MAX_COLUMNS = 1000  # Max. Number of columns (see #3)

    def __init__(self, datadir, original_datadir, request):
        """
        :type datadir: Path
        :type original_datadir: Path
        :type request: FixtureRequest
        """
        self._tolerances_dict = {}
        self._default_tolerance = {}

        self.request = request
        self.datadir = datadir
        self.original_datadir = original_datadir
        self._force_regen = False
        self._with_test_class_names = False

        self._pandas_display_options = (
            "display.precision",
            DataFrameRegressionFixture.DISPLAY_PRECISION,
            "display.width",
            DataFrameRegressionFixture.DISPLAY_WIDTH,
            "display.max_columns",
            DataFrameRegressionFixture.DISPLAY_MAX_COLUMNS,
        )

    def _check_data_types(self, key, obtained_column, expected_column):
        """
        Check if data type of obtained and expected columns are the same. Fail if not.
        Helper method used in _check_fn method.
        """
        try:
            import numpy as np
        except ModuleNotFoundError:
            raise ModuleNotFoundError(import_error_message("NumPy"))

        __tracebackhide__ = True
        obtained_data_type = obtained_column.values.dtype
        expected_data_type = expected_column.values.dtype
        if obtained_data_type != expected_data_type:
            # Check if both data types are comparable as numbers (float, int, short, bytes, etc...)
            if np.issubdtype(obtained_data_type, np.number) and np.issubdtype(
                expected_data_type, np.number
            ):
                return

            # In case they are not, assume they are not comparable
            error_msg = (
                "Data type for data %s of obtained and expected are not the same.\n"
                "Obtained: %s\n"
                "Expected: %s\n" % (key, obtained_data_type, expected_data_type)
            )
            raise AssertionError(error_msg)

    def _check_data_shapes(self, obtained_column, expected_column):
        """
        Check if obtained and expected columns have the same size.
        Helper method used in _check_fn method.
        """
        __tracebackhide__ = True

        obtained_data_shape = obtained_column.values.shape
        expected_data_shape = expected_column.values.shape
        if obtained_data_shape != expected_data_shape:
            error_msg = (
                "Obtained and expected data shape are not the same.\n"
                "Obtained: %s\n"
                "Expected: %s\n" % (obtained_data_shape, expected_data_shape)
            )
            raise AssertionError(error_msg)

    def _check_fn(self, obtained_filename, expected_filename):
        """
        Check if dict contents dumped to a file match the contents in expected file.

        :param str obtained_filename:
        :param str expected_filename:
        """
        try:
            import numpy as np
        except ModuleNotFoundError:
            raise ModuleNotFoundError(import_error_message("NumPy"))
        try:
            import pandas as pd
        except ModuleNotFoundError:
            raise ModuleNotFoundError(import_error_message("Pandas"))

        __tracebackhide__ = True

        obtained_data = pd.read_csv(str(obtained_filename))
        expected_data = pd.read_csv(str(expected_filename))

        comparison_tables_dict = {}
        for k in obtained_data.keys():
            obtained_column = obtained_data[k]
            expected_column = expected_data.get(k)

            if expected_column is None:
                error_msg = f"Could not find key '{k}' in the expected results.\n"
                error_msg += "Keys in the obtained data table: ["
                for k in obtained_data.keys():
                    error_msg += f"'{k}', "
                error_msg += "]\n"
                error_msg += "Keys in the expected data table: ["
                for k in expected_data.keys():
                    error_msg += f"'{k}', "
                error_msg += "]\n"
                error_msg += "To update values, use --force-regen option.\n\n"
                raise AssertionError(error_msg)

            tolerance_args = self._tolerances_dict.get(k, self._default_tolerance)

            self._check_data_types(k, obtained_column, expected_column)
            self._check_data_shapes(obtained_column, expected_column)

            if np.issubdtype(obtained_column.values.dtype, np.inexact):
                not_close_mask = ~np.isclose(
                    obtained_column.values,
                    expected_column.values,
                    equal_nan=True,
                    **tolerance_args,
                )
            else:
                not_close_mask = obtained_column.values != expected_column.values
                # If Empty/NaN data is expected, then the values are equal:
                not_close_mask[
                    np.logical_and(
                        pd.isna(obtained_column.values), pd.isna(expected_column.values)
                    )
                ] = False

            if np.any(not_close_mask):
                diff_ids = np.where(not_close_mask)[0]
                diff_obtained_data = obtained_column[diff_ids]
                diff_expected_data = expected_column[diff_ids]
                if obtained_column.values.dtype == bool:
                    diffs = np.logical_xor(obtained_column, expected_column)[diff_ids]
                elif obtained_column.values.dtype == object:
                    diffs = diff_obtained_data.copy()
                    diffs[:] = "?"
                else:
                    diffs = np.abs(obtained_column - expected_column)[diff_ids]

                comparison_table = pd.concat(
                    [diff_obtained_data, diff_expected_data, diffs], axis=1
                )
                comparison_table.columns = [f"obtained_{k}", f"expected_{k}", "diff"]
                comparison_tables_dict[k] = comparison_table

        if len(comparison_tables_dict) > 0:
            error_msg = "Values are not sufficiently close.\n"
            error_msg += "To update values, use --force-regen option.\n\n"
            for k, comparison_table in comparison_tables_dict.items():
                error_msg += f"{k}:\n{comparison_table}\n\n"
            if obtained_column.values.dtype == object:
                error_msg += (
                    "WARNING: diffs for this kind of data type cannot be computed."
                )
            raise AssertionError(error_msg)

    def _dump_fn(self, data_object, filename):
        """
        Dump dict contents to the given filename

        :param pd.DataFrame data_object:
        :param str filename:
        """
        data_object.to_csv(
            str(filename),
            float_format=f"%.{DataFrameRegressionFixture.DISPLAY_PRECISION}g",
        )

    def check(
        self,
        data_frame,
        basename=None,
        fullpath=None,
        tolerances=None,
        default_tolerance=None,
    ):
        """
        Checks a pandas dataframe, containing only numeric data, against a previously recorded version, or generate a new file.

        Example::

            data_frame = pandas.DataFrame.from_dict({
                'U_gas': U[0][positions],
                'U_liquid': U[1][positions],
                'gas_vol_frac [-]': vol_frac[0][positions],
                'liquid_vol_frac [-]': vol_frac[1][positions],
                'P': Pa_to_bar(P)[positions],
            })
            dataframe_regression.check(data_frame)

        :param pandas.DataFrame data_frame: pandas DataFrame containing data for regression check.

        :param str basename: basename of the file to test/record. If not given the name
            of the test is used.

        :param str fullpath: complete path to use as a reference file. This option
            will ignore embed_data completely, being useful if a reference file is located
            in the session data dir for example.

        :param dict tolerances: dict mapping keys from the data_frame to tolerance settings for the
            given data. Example::

                tolerances={'U': Tolerance(atol=1e-2)}

        :param dict default_tolerance: dict mapping the default tolerance for the current check
            call. Example::

                default_tolerance=dict(atol=1e-7, rtol=1e-18).

            If not provided, will use defaults from numpy's ``isclose`` function.

        ``basename`` and ``fullpath`` are exclusive.
        """
        try:
            import pandas as pd
        except ModuleNotFoundError:
            raise ModuleNotFoundError(import_error_message("Pandas"))

        import functools

        __tracebackhide__ = True

        assert type(data_frame) is pd.DataFrame, (
            "Only pandas DataFrames are supported on dataframe_regression fixture.\n"
            "Object with type '%s' was given." % (str(type(data_frame)),)
        )

        for column in data_frame.columns:
            array = data_frame[column]
            # Skip assertion if an array of strings
            if (array.dtype == "O") and (type(array[0]) is str):
                continue
            # Rejected: timedelta, datetime, objects, zero-terminated bytes, unicode strings and raw data
            assert array.dtype not in ["m", "M", "O", "S", "a", "U", "V"], (
                "Only numeric data is supported on dataframe_regression fixture.\n"
                "Array with type '%s' was given." % (str(array.dtype),)
            )

        if tolerances is None:
            tolerances = {}
        self._tolerances_dict = tolerances

        if default_tolerance is None:
            default_tolerance = {}
        self._default_tolerance = default_tolerance

        dump_fn = functools.partial(self._dump_fn, data_frame)

        with pd.option_context(*self._pandas_display_options):
            perform_regression_check(
                datadir=self.datadir,
                original_datadir=self.original_datadir,
                request=self.request,
                check_fn=self._check_fn,
                dump_fn=dump_fn,
                extension=".csv",
                basename=basename,
                fullpath=fullpath,
                force_regen=self._force_regen,
                with_test_class_names=self._with_test_class_names,
            )
