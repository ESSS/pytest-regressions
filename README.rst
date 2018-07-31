==================
pytest-regressions
==================

.. image:: https://img.shields.io/pypi/v/pytest-regressions.svg
    :target: https://pypi.org/project/pytest-regressions
    :alt: PyPI version

.. image:: https://img.shields.io/conda/vn/conda-forge/pytest-regressions.svg
    :target: https://anaconda.org/conda-forge/pytest-regressions

.. image:: https://img.shields.io/pypi/pyversions/pytest-regressions.svg
    :target: https://pypi.org/project/pytest-regressions
    :alt: Python versions

.. image:: https://travis-ci.com/ESSS/pytest-regressions.svg?branch=master
    :target: https://travis-ci.com/ESSS/pytest-regressions
    :alt: See Build Status on Travis CI

.. image:: https://ci.appveyor.com/api/projects/status/oq3udklexcx38sc0/branch/master
    :target: https://ci.appveyor.com/project/ESSS/pytest-regressions/branch/master
    :alt: See Build Status on AppVeyor

.. image:: https://img.shields.io/readthedocs/pytest-regressions.svg
  :target: https://pytest-regressions.readthedocs.io/en/latest

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
  :target: https://github.com/ambv/black

Fixtures to write regression tests.

Features
--------

This plugin makes it simple to test general data, images, files, and numeric tables by saving *expected*
data in a *data directory* (courtesy of `pytest-datadir <https://github.com/gabrielcnr/pytest-datadir>`_) that
can be used to verify that future runs produce the same data.

See `the docs <https://pytest-regressions.readthedocs.io/en/latest>`_ for examples and API usage.


Requirements
------------

* ``pytest>=3.5``
* Python 2.7 and Python 3.5+.


Installation
------------

You can install "pytest-regressions" via `pip`_ from `PyPI`_::

    $ pip install pytest-regressions


Contributing
------------
Contributions are very welcome. Tests can be run with `tox`_, please ensure
the coverage at least stays the same before you submit a pull request.

License
-------

Distributed under the terms of the `MIT`_ license, "pytest-regressions" is free and open source software


Issues
------

If you encounter any problems, please `file an issue`_ along with a detailed description.

----

This `pytest`_ plugin was generated with `Cookiecutter`_ along with `@hackebrot`_'s `cookiecutter-pytest-plugin`_ template.


.. _`Cookiecutter`: https://github.com/audreyr/cookiecutter
.. _`@hackebrot`: https://github.com/hackebrot
.. _`MIT`: http://opensource.org/licenses/MIT
.. _`BSD-3`: http://opensource.org/licenses/BSD-3-Clause
.. _`GNU GPL v3.0`: http://www.gnu.org/licenses/gpl-3.0.txt
.. _`Apache Software License 2.0`: http://www.apache.org/licenses/LICENSE-2.0
.. _`cookiecutter-pytest-plugin`: https://github.com/pytest-dev/cookiecutter-pytest-plugin
.. _`file an issue`: https://github.com/nicoddemus/pytest-regressions/issues
.. _`pytest`: https://github.com/pytest-dev/pytest
.. _`tox`: https://tox.readthedocs.io/en/latest/
.. _`pip`: https://pypi.org/project/pip/
.. _`PyPI`: https://pypi.org/project
