from pytest_regressions.common import import_error_message
from pytest_regressions.common import perform_regression_check


class NDArraysRegressionFixture:
    """
    NumPy NPZ regression fixture implementation used on ndarrays_regression fixture.
    """

    THRESHOLD = 100
    ROWFORMAT = "{:>15s}  {:>20s}  {:>20s}  {:>20s}\n"

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

    def _check_data_types(self, key, obtained_array, expected_array):
        """
        Check if data type of obtained and expected arrays are the same. Fail if not.
        Helper method used in _check_fn method.
        """
        try:
            import numpy as np
        except ModuleNotFoundError:
            raise ModuleNotFoundError(import_error_message("NumPy"))

        __tracebackhide__ = True

        if obtained_array.dtype != expected_array.dtype:
            # Check if both data types are comparable as numbers (float, int, short, bytes, etc...)
            if np.issubdtype(obtained_array.dtype, np.number) and np.issubdtype(
                expected_array.dtype, np.number
            ):
                return
            # Check if both data types are comparable as strings
            if np.issubdtype(obtained_array.dtype, str) and np.issubdtype(
                expected_array.dtype, str
            ):
                return

            # In case they are not, assume they are not comparable
            error_msg = (
                "Data types are not the same.\n"
                f"key: {key}\n"
                f"Obtained: {obtained_array.dtype}\n"
                f"Expected: {expected_array.dtype}\n"
            )
            raise AssertionError(error_msg)

    def _check_data_shapes(self, key, obtained_array, expected_array):
        """
        Check if obtained and expected arrays have the same size.
        Helper method used in _check_fn method.
        """
        __tracebackhide__ = True

        if obtained_array.shape != expected_array.shape:
            error_msg = (
                "Shapes are not the same.\n"
                f"Key: {key}\n"
                f"Obtained: {obtained_array.shape}\n"
                f"Expected: {expected_array.shape}\n"
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

        __tracebackhide__ = True

        # Turn result of np.load into a dictionary, such that the files are closed immediately.
        obtained_data = dict(np.load(str(obtained_filename)))
        expected_data = dict(np.load(str(expected_filename)))

        # Check mismatches in the keys.
        if set(obtained_data) != set(expected_data):
            error_msg = (
                "They keys in the obtained results differ from the expected results.\n"
            )
            error_msg += "  Matching keys: "
            error_msg += str(list(set(obtained_data) & set(expected_data)))
            error_msg += "\n"
            error_msg += "  New in obtained: "
            error_msg += str(list(set(obtained_data) - set(expected_data)))
            error_msg += "\n"
            error_msg += "  Missing from obtained: "
            error_msg += str(list(set(expected_data) - set(obtained_data)))
            error_msg += "\n"
            error_msg += "To update values, use --force-regen option.\n\n"
            raise AssertionError(error_msg)

        # Compare the contents of the arrays.
        comparison_tables_dict = {}
        for k, obtained_array in obtained_data.items():
            expected_array = expected_data.get(k)
            tolerance_args = self._tolerances_dict.get(k, self._default_tolerance)

            self._check_data_types(k, obtained_array, expected_array)
            self._check_data_shapes(k, obtained_array, expected_array)

            if np.issubdtype(obtained_array.dtype, np.inexact):
                not_close_mask = ~np.isclose(
                    obtained_array,
                    expected_array,
                    equal_nan=True,
                    **tolerance_args,
                )
            else:
                not_close_mask = obtained_array != expected_array

            if np.any(not_close_mask):
                if not_close_mask.ndim == 0:
                    diff_ids = [()]
                else:
                    diff_ids = np.array(np.nonzero(not_close_mask)).T
                comparison_tables_dict[k] = (
                    expected_array.size,
                    expected_array.shape,
                    diff_ids,
                    obtained_array[not_close_mask],
                    expected_array[not_close_mask],
                )

        if len(comparison_tables_dict) > 0:
            error_msg = "Values are not sufficiently close.\n"
            error_msg += "To update values, use --force-regen option.\n\n"
            for k, (
                size,
                shape,
                diff_ids,
                obtained_array,
                expected_array,
            ) in comparison_tables_dict.items():
                # Summary
                error_msg += f"{k}:\n  Shape: {shape}\n"
                pct = 100 * len(diff_ids) / size
                error_msg += (
                    f"  Number of differences: {len(diff_ids)} / {size} ({pct:.1f}%)\n"
                )
                if np.issubdtype(obtained_array.dtype, np.number) and len(diff_ids) > 1:
                    error_msg += (
                        "  Statistics are computed for differing elements only.\n"
                    )

                    abs_errors = abs(obtained_array - expected_array)
                    error_msg += "  Stats for abs(obtained - expected):\n"
                    error_msg += f"    Max:     {abs_errors.max()}\n"
                    error_msg += f"    Mean:    {abs_errors.mean()}\n"
                    error_msg += f"    Median:  {np.median(abs_errors)}\n"

                    expected_nonzero = np.array(np.nonzero(expected_array)).T
                    rel_errors = abs(
                        (
                            obtained_array[expected_nonzero]
                            - expected_array[expected_nonzero]
                        )
                        / expected_array[expected_nonzero]
                    )
                    if len(rel_errors) == 0:
                        error_msg += "  Relative errors are not reported because all expected values are zero.\n"
                    else:
                        error_msg += (
                            f"  Stats for abs(obtained - expected) / abs(expected):\n"
                        )
                        if len(rel_errors) != len(abs_errors):
                            pct = 100 * len(rel_errors) / len(abs_errors)
                            error_msg += f"    Number of (differing) non-zero expected results: {len(rel_errors)} / {len(abs_errors)} ({pct:.1f}%)\n"
                            error_msg += f"    Relative errors are computed for the non-zero expected results.\n"
                        else:
                            rel_errors = abs(
                                (obtained_array - expected_array) / expected_array
                            )
                        error_msg += f"    Max:     {rel_errors.max()}\n"
                        error_msg += f"    Mean:    {rel_errors.mean()}\n"
                        error_msg += f"    Median:  {np.median(rel_errors)}\n"

                # Details results
                error_msg += "  Individual errors:\n"
                if len(diff_ids) > self.THRESHOLD:
                    error_msg += (
                        f"    Only showing first {self.THRESHOLD} mismatches.\n"
                    )
                    diff_ids = diff_ids[: self.THRESHOLD]
                    obtained_array = obtained_array[: self.THRESHOLD]
                    expected_array = expected_array[: self.THRESHOLD]
                error_msg += self.ROWFORMAT.format(
                    "Index",
                    "Obtained",
                    "Expected",
                    "Difference",
                )
                for diff_id, obtained, expected in zip(
                    diff_ids, obtained_array, expected_array
                ):
                    diff_id_str = ", ".join(str(i) for i in diff_id)
                    if len(diff_id) != 1:
                        diff_id_str = f"({diff_id_str})"
                    error_msg += self.ROWFORMAT.format(
                        diff_id_str,
                        str(obtained),
                        str(expected),
                        str(obtained - expected)
                        if isinstance(obtained, np.number)
                        else "",
                    )
                error_msg += "\n"
            raise AssertionError(error_msg)

    def _dump_fn(self, data_object, filename):
        """
        Dump dict contents to the given filename

        :param Dict[str, np.ndarray] data_object:
        :param str filename:
        """
        try:
            import numpy as np
        except ModuleNotFoundError:
            raise ModuleNotFoundError(import_error_message("NumPy"))
        np.savez_compressed(str(filename), **data_object)

    def check(
        self,
        data_dict,
        basename=None,
        fullpath=None,
        tolerances=None,
        default_tolerance=None,
    ):
        """
        Checks a dictionary of NumPy ndarrays, containing only numeric data, against a previously recorded version, or generate a new file.

        Example::

            def test_some_data(ndarrays_regression):
                points, values = some_function()
                ndarrays_regression.check(
                    {
                        'points': points,  # array with shape (100, 3)
                        'values': values,  # array with shape (100,)
                    },
                    default_tolerance=dict(atol=1e-8, rtol=1e-8)
                )

        :param Dict[str, numpy.ndarray] data_dict: dictionary of NumPy ndarrays containing
            data for regression check. The arrays can have any shape.

        :param str basename: basename of the file to test/record. If not given the name
            of the test is used.

        :param str fullpath: complete path to use as a reference file. This option
            will ignore embed_data completely, being useful if a reference file is located
            in the session data dir for example.

        :param dict tolerances: dict mapping keys from the data_dict to tolerance settings
            for the given data. Example::

                tolerances={'U': Tolerance(atol=1e-2)}

        :param dict default_tolerance: dict mapping the default tolerance for the current
            check call. Example::

                default_tolerance=dict(atol=1e-7, rtol=1e-18).

            If not provided, will use defaults from numpy's ``isclose`` function.

        ``basename`` and ``fullpath`` are exclusive.
        """
        try:
            import numpy as np
        except ModuleNotFoundError:
            raise ModuleNotFoundError(import_error_message("NumPy"))

        import functools

        __tracebackhide__ = True

        if not isinstance(data_dict, dict):
            raise TypeError(
                "Only dictionaries with NumPy arrays or array-like objects are "
                "supported on ndarray_regression fixture.\n"
                "Object with type '{}' was given.".format(str(type(data_dict)))
            )
        for key, array in data_dict.items():
            assert isinstance(
                key, str
            ), "The dictionary keys must be strings. " "Found key with type '%s'" % (
                str(type(key))
            )
            data_dict[key] = np.asarray(array)

        for key, array in data_dict.items():
            # Accepted:
            #  - b: boolean
            #  - i: signed integer
            #  - u: unsigned integer
            #  - f: floating-point number
            #  - c: complex floating-point number
            #  - U: unicode string
            # Rejected:
            #  - m: timedelta
            #  - M: datetime
            #  - O: objects
            #  - S: zero-terminated bytes
            #  - V: void (raw data, structured arrays)
            if array.dtype.kind not in ["b", "i", "u", "f", "c", "U"]:
                raise TypeError(
                    "Only numeric or unicode data is supported on ndarrays_regression "
                    f"fixture.\nArray '{key}' with type '{array.dtype}' was given."
                )

        if tolerances is None:
            tolerances = {}
        self._tolerances_dict = tolerances

        if default_tolerance is None:
            default_tolerance = {}
        self._default_tolerance = default_tolerance

        dump_fn = functools.partial(self._dump_fn, data_dict)

        perform_regression_check(
            datadir=self.datadir,
            original_datadir=self.original_datadir,
            request=self.request,
            check_fn=self._check_fn,
            dump_fn=dump_fn,
            extension=".npz",
            basename=basename,
            fullpath=fullpath,
            force_regen=self._force_regen,
            with_test_class_names=self._with_test_class_names,
        )
