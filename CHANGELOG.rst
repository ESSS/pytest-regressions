2.4.0 (2022-09-16)
------------------

* New ``--regen-all`` flag, which regenerates all files without failing the tests. Useful to regenerate all files in
  the test suite with a single run.
* The public API is now fully type annotated.
* ``pytest>=6.2`` is now required.

2.3.1 (2022-01-18)
------------------

* `#84 <https://github.com/ESSS/pytest-regressions/pull/84>`__: (Bugfix) Properly handle empty and NaN values on num_regression and dataframe_regression.

2.3.0 (2022-01-04)
------------------

* `#54 <https://github.com/ESSS/pytest-regressions/pull/54>`__: New ``--with-test-class-names`` command-line flag to consider test class names when composing the expected and obtained data filenames. Needed when the same module contains different classes with the same method names.
* `#72 <https://github.com/ESSS/pytest-regressions/pull/72>`__: New ``ndarrays_regression``, for comparing NumPy arrays with arbitrary shape.
* `#74 <https://github.com/ESSS/pytest-regressions/pull/74>`__: Fix ``empty string bug`` on dataframe regression.

2.2.0 (2020-01-27)
------------------

* `#45 <https://github.com/ESSS/pytest-regressions/pull/45>`__: ``num_regression.check`` now accepts any object that can be coerced to a 1d ``numpy`` array with numeric ``dtype`` (e.g. list, tuple, etc).

2.1.1 (2020-12-7)
------------------

* `#35 <https://github.com/ESSS/pytest-regressions/pull/35>`__: New ``dataframe_regression`` fixture to check pandas DataFrames directly.

Note: `2.1.0` was not deployed due to a CI error.

2.0.2 (2020-10-07)
------------------

* `#34 <https://github.com/ESSS/pytest-regressions/pull/34>`__: Fix ``data_regression`` bug that creates empty file on serializing error.

2.0.1 (2020-05-18)
------------------

* `#28 <https://github.com/ESSS/pytest-regressions/pull/28>`__: Fix ``num_regression`` bug when comparing numpy shapes.

2.0.0 (2019-09-10)
------------------

* Drop support for Python 2.7 and 3.5.


1.0.6 (2019-09-10)
------------------

* `#18 <https://github.com/ESSS/pytest-regressions/pull/18>`__: When using ``fill_different_shape_with_nan=True``, a proper ``TypeError`` will be raised for non-float arrays instead of filling integer arrays with "garbage".

* `#22 <https://github.com/ESSS/pytest-regressions/issues/22>`__: Fix warning when comparing arrays of boolean values.

1.0.5 (2018-11-20)
------------------

* `#15 <https://github.com/ESSS/pytest-regressions/pull/15>`__: Remove some extra line separators from the diff output, which makes the representation more compact.

1.0.4 (2018-10-18)
------------------

* Fixed ``DeprecationWarning: invalid escape sequence \W``.

1.0.3 (2018-10-10)
------------------

* Set ``pandas`` ``display.max_columns`` option in ``num_regression`` to prevent
  ``pandas`` from truncating the output (`#3 <https://github.com/ESSS/pytest-regressions/issues/3>`_).


1.0.2 (2018-08-29)
------------------

* Hide traceback of internal functions when displaying failures.

1.0.1 (2018-07-27)
------------------

* Fixed some development dependencies being declared as runtime dependencies.

1.0.0 (2018-07-27)
------------------

* Introduce ``image_regression`` fixture.

0.1.0 (2018-07-26)
------------------

* Initial release.
