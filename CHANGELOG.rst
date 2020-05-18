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
