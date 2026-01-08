2.9.0
-----

*2026-01-08*

* `#218 <https://github.com/ESSS/pytest-regressions/pull/218>`__: ``ImageRegression.check`` now supports receiving an ``PIL.Image`` object directly.
* `#220 <https://github.com/ESSS/pytest-regressions/pull/220>`__: Support for Python 3.14 has been added, while Python 3.9 (EOL) has been dropped.

2.8.3
-----

*2025-09-05*

* `#197 <https://github.com/ESSS/pytest-regressions/issues/197>`__: Fixed support for ``pandas.CategoricalDtype``, regressed in ``2.8.1``.

2.8.2
-----

*2025-08-13*

* `#200 <https://github.com/ESSS/pytest-regressions/issues/200>`__: Reintroduced support for ``datetime`` columns in ``dataframe_regression``.

2.8.1
-----

*2025-07-04*

* `#173 <https://github.com/ESSS/pytest-regressions/issues/173>`__: Removed check against numpy-2.0-deprecated ``a`` dtype alias.

2.8.0
-----

*2025-08-30*

* `#192 <https://github.com/ESSS/pytest-regressions/pull/192>`__: Replaced ``datadir`` with the ``lazy_datadir`` fixture for improved performance in test suites with large data directories.

  * **Breaking Change**: If your test suite modifies ``datadir``, you must now override ``lazy_datadir`` instead.


2.7.0
-----

*2025-01-10*

* Python 3.12 and 3.13 are now officially supported.
* Python 3.8 (EOL) is no longer supported.
* `#184 <https://github.com/ESSS/pytest-regressions/pull/184>`__: Added ``fullpath`` parameter to ``image_regression.check``.


2.6.0
-----

*2024-12-17*

* `#132 <https://github.com/ESSS/pytest-regressions/pull/132>`__: Added documentation for specifying custom data directories.
* `#177 <https://github.com/ESSS/pytest-regressions/pull/177>`__: Added new ``round_digits`` to ``data_regression.check``, which when given will round all float values to the given number of dicts (recursively) before saving the data to disk.

2.5.0 (2023-08-31)
------------------

* Dropped support for EOL Python 3.6 and Python 3.7.
* Added support for Python 3.11.

2.4.3 (2023-08-30)
------------------

* `#137 <https://github.com/ESSS/pytest-regressions/pull/137>`__: (Bugfix) Make ``dataframe_regression`` compatible with classes inheriting from ``pandas.DataFrame``.

2.4.2 (2023-01-12)
------------------

* `#119 <https://github.com/ESSS/pytest-regressions/pull/119>`__: (Bugfix) Properly handle missing index ``0``.

2.4.1 (2022-09-17)
------------------

* Compatibility fix for pytest 6.2.


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
