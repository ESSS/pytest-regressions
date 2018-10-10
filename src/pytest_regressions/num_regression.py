# encoding: UTF-8

import six

from pytest_regressions.common import perform_regression_check


class NumericRegressionFixture(object):
    """
    Numeric Data Regression fixture implementation used on num_regression fixture.
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

        self._pandas_display_options = (
            "display.precision",
            NumericRegressionFixture.DISPLAY_PRECISION,
            "display.width",
            NumericRegressionFixture.DISPLAY_WIDTH,
            "display.max_columns",
            NumericRegressionFixture.DISPLAY_MAX_COLUMNS,
        )

    def _check_data_types(self, key, obtained_column, expected_column):
        """
        Check if data type of obtained and expected columns are the same. Fail if not.
        Helper method used in _check_fn method.
        """
        import numpy as np

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

        :param six.text_type obtained_filename:
        :param six.text_type expected_filename:
        """
        import numpy as np
        import pandas as pd

        __tracebackhide__ = True

        obtained_data = pd.read_csv(six.text_type(obtained_filename))
        expected_data = pd.read_csv(six.text_type(expected_filename))

        comparison_tables_dict = {}
        for k in obtained_data.keys():
            obtained_column = obtained_data[k]
            expected_column = expected_data.get(k)

            if expected_column is None:
                error_msg = "Could not find key '%s' in the expected results.\n" % (k,)
                error_msg += "Keys in the obtained data table: ["
                for k in obtained_data.keys():
                    error_msg += "'%s', " % (k,)
                error_msg += "]\n"
                error_msg += "Keys in the expected data table: ["
                for k in expected_data.keys():
                    error_msg += "'%s', " % (k,)
                error_msg += "]\n"
                error_msg += "To update values, use --force-regen option.\n\n"
                raise AssertionError(error_msg)

            tolerance_args = self._tolerances_dict.get(k, self._default_tolerance)

            self._check_data_types(k, obtained_column, expected_column)
            self._check_data_shapes(obtained_column, expected_column)

            data_type = obtained_column.values.dtype
            if data_type in [float, np.float, np.float16, np.float32, np.float64]:
                not_close_mask = ~np.isclose(
                    obtained_column.values,
                    expected_column.values,
                    equal_nan=True,
                    **tolerance_args
                )
            else:
                not_close_mask = obtained_column.values != expected_column.values

            if np.any(not_close_mask):
                diff_ids = np.where(not_close_mask)[0]
                diff_obtained_data = obtained_column[diff_ids]
                diff_expected_data = expected_column[diff_ids]
                diffs = np.abs(obtained_column - expected_column)[diff_ids]

                comparison_table = pd.concat(
                    [diff_obtained_data, diff_expected_data, diffs], axis=1
                )
                comparison_table.columns = [
                    "obtained_%s" % (k,),
                    "expected_%s" % (k,),
                    "diff",
                ]
                comparison_tables_dict[k] = comparison_table

        if len(comparison_tables_dict) > 0:
            error_msg = "Values are not sufficiently close.\n"
            error_msg += "To update values, use --force-regen option.\n\n"
            for k, comparison_table in comparison_tables_dict.items():
                error_msg += "%s:\n%s\n\n" % (k, comparison_table)
            raise AssertionError(error_msg)

    def _dump_fn(self, data_object, filename):
        """
        Dump dict contents to the given filename

        :param pd.DataFrame data_object:
        :param six.text_type filename:
        """
        data_object.to_csv(
            six.text_type(filename),
            float_format="%%.%sg" % (NumericRegressionFixture.DISPLAY_PRECISION,),
        )

    def check(
        self,
        data_dict,
        basename=None,
        fullpath=None,
        tolerances=None,
        default_tolerance=None,
        data_index=None,
        fill_different_shape_with_nan=True,
    ):
        """
        Checks the given dict against a previously recorded version, or generate a new file.
        The dict must map from user-defined keys to 1d numpy arrays.

        Example::

            num_regression.check({
                'U_gas': U[0][positions],
                'U_liquid': U[1][positions],
                'gas_vol_frac [-]': vol_frac[0][positions],
                'liquid_vol_frac [-]': vol_frac[1][positions],
                'P': Pa_to_bar(P)[positions],
            })

        :param dict data_dict: dict mapping keys to numpy arrays.

        :param str basename: basename of the file to test/record. If not given the name
            of the test is used.

        :param str fullpath: complete path to use as a reference file. This option
            will ignore embed_data completely, being useful if a reference file is located
            in the session data dir for example.

        :param dict tolerances: dict mapping keys from the data_dict to tolerance settings for the
            given data. Example::

                tolerances={'U': Tolerance(atol=1e-2)}

        :param dict default_tolerance: dict mapping the default tolerance for the current check
            call. Example::

                default_tolerance=dict(atol=1e-7, rtol=1e-18).

            If not provided, will use defaults from numpy's ``isclose`` function.

        :param list data_index: If set, will override the indexes shown in the outputs. Default
            is panda's default, which is ``range(0, len(data))``.

        :param bool fill_different_shape_with_nan: If set, all the data provided in the data_dict
            that has size lower than the bigger size will be filled with ``np.NaN``, in order to save
            the data in a CSV file.

        ``basename`` and ``fullpath`` are exclusive.
        """
        import numpy as np
        import pandas as pd
        import functools

        __tracebackhide__ = True

        if tolerances is None:
            tolerances = {}
        self._tolerances_dict = tolerances

        if default_tolerance is None:
            default_tolerance = {}
        self._default_tolerance = default_tolerance

        data_shapes = []
        for obj in data_dict.values():
            assert type(obj) in [
                np.ndarray
            ], "Only numpy arrays are valid for numeric_data_regression fixture.\n"
            shape = obj.shape

            assert len(shape) == 1, (
                "Only 1D arrays are supported on num_data_regression fixture.\n"
                "Array with shape %s was given.\n" % (shape,)
            )
            data_shapes.append(shape[0])

        if not np.all(data_shapes == data_shapes[0]):
            if not fill_different_shape_with_nan:
                assert (
                    False
                ), "Data dict with different array lengths will not be accepted." "Try setting fill_different_shape_with_nan=True."
            else:
                max_size = max(data_shapes)
                for k, obj in data_dict.items():
                    new_data = np.empty(shape=(max_size,), dtype=obj.dtype)
                    new_data[: len(obj)] = obj
                    new_data[len(obj) :] = np.nan
                    data_dict[k] = new_data

        data_frame = pd.DataFrame(data_dict, index=data_index)
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
            )
