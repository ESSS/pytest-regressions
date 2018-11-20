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
