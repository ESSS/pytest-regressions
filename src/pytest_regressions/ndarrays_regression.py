from pytest_regressions.common import perform_regression_check, import_error_message


class NDArraysRegressionFixture:
    """
    NumPy NPZ regression fixture implementation used on ndarrays_regression fixture.
    """

    THRESHOLD = 100
    ROWFORMAT = "{:>10s}  {:>20s}  {:>20s}  {:>20s}\n"

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

        obtained_data_type = obtained_array.dtype
        expected_data_type = expected_array.dtype
        if obtained_data_type != expected_data_type:
            # Check if both data types are comparable as numbers (float, int, short, bytes, etc...)
            if np.issubdtype(obtained_data_type, np.number) and np.issubdtype(
                expected_data_type, np.number
            ):
                return

            # In case they are not, assume they are not comparable
            error_msg = (
                "Data types are not the same.\n"
                "key: %s\n"
                "Obtained: %s\n"
                "Expected: %s\n" % (key, obtained_data_type, expected_data_type)
            )
            raise AssertionError(error_msg)

    def _check_data_shapes(self, key, obtained_array, expected_array):
        """
        Check if obtained and expected arrays have the same size.
        Helper method used in _check_fn method.
        """
        __tracebackhide__ = True

        obtained_data_shape = obtained_array.shape
        expected_data_shape = expected_array.shape
        if obtained_data_shape != expected_data_shape:
            error_msg = (
                "Shapes are not the same.\n"
                "Key: %s\n"
                "Obtained: %s\n"
                "Expected: %s\n" % (key, obtained_data_shape, expected_data_shape)
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

        comparison_tables_dict = {}
        for k in obtained_data.keys():
            obtained_array = obtained_data[k]
            expected_array = expected_data.get(k)

            if expected_array is None:
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

            self._check_data_types(k, obtained_array, expected_array)
            self._check_data_shapes(k, obtained_array, expected_array)

            data_type = obtained_array.dtype
            if data_type in [float, np.float16, np.float32, np.float64]:
                not_close_mask = ~np.isclose(
                    obtained_array,
                    expected_array,
                    equal_nan=True,
                    **tolerance_args,
                )
            else:
                not_close_mask = obtained_array != expected_array

            if np.any(not_close_mask):
                diff_ids = np.nonzero(not_close_mask)
                comparison_tables_dict[k] = (
                    np.array(diff_ids).T,
                    obtained_array[diff_ids],
                    expected_array[diff_ids],
                )

        if len(comparison_tables_dict) > 0:
            error_msg = "Values are not sufficiently close.\n"
            error_msg += "To update values, use --force-regen option.\n\n"
            for k, (
                diff_ids,
                obtained_array,
                expected_array,
            ) in comparison_tables_dict.items():
                if len(diff_ids) > self.THRESHOLD:
                    error_msg += f"Only showing first {self.THRESHOLD} mismatches.\n"
                    diff_ids = diff_ids[: self.THRESHOLD]
                    obtained_array = obtained_array[: self.THRESHOLD]
                    expected_array = expected_array[: self.THRESHOLD]
                error_msg += f"{k}:\n"
                error_msg += self.ROWFORMAT.format(
                    "Index",
                    "Obtained",
                    "Expected",
                    "Difference",
                )
                for diff_id, obtained, expected in zip(
                    diff_ids, obtained_array, expected_array
                ):
                    error_msg += self.ROWFORMAT.format(
                        ",".join(str(i) for i in diff_id),
                        str(obtained),
                        str(expected),
                        str(obtained - expected)
                        if isinstance(obtained, np.number)
                        else "",
                    )
                error_msg += "\n\n"
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

        assert isinstance(data_dict, dict), (
            "Only dictionaries with NumPy arrays or array-like objects are "
            "supported on ndarray_regression fixture.\n"
            "Object with type '%s' was given. " % (str(type(data_dict)),)
        )
        for key, array in data_dict.items():
            assert isinstance(
                key, str
            ), "The dictionary keys must be strings. " "Found key with type '%s'" % (
                str(type(key))
            )
            data_dict[key] = np.asarray(array)

        for key, array in data_dict.items():
            # Skip assertion if an array of strings
            if (array.dtype == "O") and (type(array[0]) is str):
                continue
            # Rejected: timedelta, datetime, objects, zero-terminated bytes, unicode strings and raw data
            assert array.dtype not in [
                "m",
                "M",
                "O",
                "S",
                "a",
                "U",
                "V",
            ], "Only numeric data is supported on ndarrays_regression fixture.\n" "Array '%s' with type '%s' was given.\n" % (
                key,
                str(array.dtype),
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
