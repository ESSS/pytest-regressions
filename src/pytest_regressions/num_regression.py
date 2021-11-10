from pytest_regressions.common import import_error_message
from pytest_regressions.common import perform_regression_check
from pytest_regressions.dataframe_regression import DataFrameRegressionFixture


class NumericRegressionFixture(DataFrameRegressionFixture):
    """
    Numeric Data Regression fixture implementation used on num_regression fixture.
    """

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
        The dict must map from user-defined keys to 1d numpy arrays or array-like values.

        Example::

            num_regression.check({
                'U_gas': U[0][positions],
                'U_liquid': U[1][positions],
                'gas_vol_frac [-]': vol_frac[0][positions],
                'liquid_vol_frac [-]': vol_frac[1][positions],
                'P': Pa_to_bar(P)[positions],
            })

        :param dict data_dict: dict mapping keys to numpy arrays, or objects that can be
            coerced to 1d numpy arrays with a numeric dtype (e.g. list, tuple, etc).

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

        try:
            import numpy as np
        except ModuleNotFoundError:
            raise ModuleNotFoundError(import_error_message("Numpy"))
        try:
            import pandas as pd
        except ModuleNotFoundError:
            raise ModuleNotFoundError(import_error_message("Pandas"))

        __tracebackhide__ = True

        for k, obj in data_dict.items():
            if not isinstance(obj, np.ndarray):
                arr = np.atleast_1d(np.asarray(obj))
                if np.issubdtype(arr.dtype, np.number):
                    data_dict[k] = arr

        data_shapes = []
        for obj in data_dict.values():
            assert type(obj) in [
                np.ndarray
            ], "Only objects that can be coerced to numpy arrays are valid for numeric_data_regression fixture.\n"
            shape = obj.shape

            assert len(shape) == 1, (
                "Only 1D arrays are supported on num_data_regression fixture.\n"
                "Array with shape %s was given.\n" % (shape,)
            )
            data_shapes.append(shape[0])

        data_shapes = np.array(data_shapes)
        if not np.all(data_shapes == data_shapes[0]):
            if not fill_different_shape_with_nan:
                assert (
                    False
                ), "Data dict with different array lengths will not be accepted. Try setting fill_different_shape_with_nan=True."
            elif len(data_dict) > 1 and not all(
                np.issubdtype(a.dtype, np.floating) for a in data_dict.values()
            ):
                raise TypeError(
                    "Checking multiple arrays with different shapes are not supported for non-float arrays"
                )
            else:
                max_size = max(data_shapes)
                for k, obj in data_dict.items():
                    new_data = np.empty(shape=(max_size,), dtype=obj.dtype)
                    new_data[: len(obj)] = obj
                    new_data[len(obj) :] = np.nan
                    data_dict[k] = new_data

        data_frame = pd.DataFrame(data_dict, index=data_index)

        DataFrameRegressionFixture.check(
            self, data_frame, basename, fullpath, tolerances, default_tolerance
        )
