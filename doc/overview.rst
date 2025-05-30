Overview
========

``pytest-regressions`` provides some fixtures that make it easy to maintain tests that
generate lots of data or specific data files like images.

This plugin uses a *data directory* (courtesy of `pytest-datadir <https://github.com/gabrielcnr/pytest-datadir>`_) to
store expected data files, which are stored and used as baseline for future test runs.  You can also
define your own *data directory* directly as described below.

Example
-------

Let's use ``data_regression`` as an example, but the workflow is the same for the other ``*_regression`` fixtures.

Suppose we have a ``summary_grids`` function which outputs a dictionary containing information about discrete grids
for simulation. Of course your function would actually return some computed/read value, but here it is using an inline
result for this example:

.. code-block:: python

    def summary_grids():
        return {
            "Main Grid": {
                "id": 0,
                "cell_count": 1000,
                "active_cells": 300,
                "properties": [
                    {"name": "Temperature", "min": 75, "max": 85},
                    {"name": "Porosity", "min": 0.3, "max": 0.4},
                ],
            },
            "Refin1": {
                "id": 1,
                "cell_count": 48,
                "active_cells": 44,
                "properties": [
                    {"name": "Temperature", "min": 78, "max": 81},
                    {"name": "Porosity", "min": 0.36, "max": 0.39},
                ],
            },
        }


We could test the results of this function like this:


.. code-block:: python

    def test_grids():
        data = summary_grids()
        assert data["Main Grid"]["id"] == 0
        assert data["Main Grid"]["cell_count"] == 1000
        assert data["Main Grid"]["active_cells"] == 300
        assert data["Main Grid"]["properties"] == [
            {"name": "Temperature", "min": 75, "max": 85},
            {"name": "Porosity", "min": 0.3, "max": 0.4},
        ]
        ...


But this presents a number of problems:

* Gets old quickly.
* Error-prone.
* If a check fails, we don't know what else might be wrong with the obtained data.
* Does not scale for large data.
* **Maintenance burden**: if the data changes in the future (and it will) it will be a major headache to update the values,
  specially if there are a lot of similar tests like this one.


Using data_regression
---------------------

The ``data_regression`` fixture provides a method to check general dictionary data like the one in the previous example.

There is no need to import anything, just declare the ``data_regression`` fixture in your test's
arguments and call the ``check`` method in the test:

.. code-block:: python

    def test_grids2(data_regression):
        data = summary_grids()
        data_regression.check(data)


The first time your run this test, it will *fail* with a message like this::


    >           pytest.fail(msg)
    E           Failed: File not found in data directory, created:
    E           - C:\Users\bruno\pytest-regressions\tests\test_grids\test_grids2.yml

The fixture will generate a ``test_grids2.yml`` file (same name as the test) in the *data directory* with the contents of the dictionary:

.. code-block:: yaml

    Main Grid:
      active_cells: 300
      cell_count: 1000
      id: 0
      properties:
      - max: 85
        min: 75
        name: Temperature
      - max: 0.4
        min: 0.3
        name: Porosity
    Refin1:
      active_cells: 44
      cell_count: 48
      id: 1
      properties:
      - max: 81
        min: 78
        name: Temperature
      - max: 0.39
        min: 0.36
        name: Porosity

.. important::

    This file should be committed to version control.

The next time you run this test, it will compare the results of ``summary_grids()`` with the contents of the YAML file.
If they match, the test passes. If they don't match the test will fail, showing a nice diff of the text differences.

``--force-regen``
~~~~~~~~~~~~~~~~~

If the test fails because the new data is correct (the implementation might be returning more information about the
grids for example), then you can use the ``--force-regen`` flag to update the expected file::

    $ pytest --force-regen


This will fail the same test but with a different message saying that the file has been updated. Commit the new file.

This workflow makes it very simple to keep the files up to date and to check all the information we need.

``--regen-all``
~~~~~~~~~~~~~~~~~

If a single change will fail several regression tests, you can also use the ``--regen-all`` command-line flag::

    $ pytest --regen-all


With this flag, the regression fixtures will regenerate all files but will not fail the tests themselves. This make it very
easy to update all regression files in a single pytest run when individual tests contain multiple regressions.


Parametrized tests
------------------

When using parametrized tests, pytest will give each parametrization of your test a unique name.
This means that ``pytest-regressions`` will create a new file for each parametrization too.

Suppose we have an additional function ``summary_grids_2`` that generates longer data, we can
re-use the same test with the ``@pytest.mark.parametrize`` decorator:

.. code-block:: python

    @pytest.mark.parametrize('data', [summary_grids(), summary_grids_2()])
    def test_grids3(data_regression, data):
        data_regression.check(data)

Pytest will automatically name these as ``test_grids3[data0]`` and ``test_grids3[data1]``, so files
``test_grids3_data0.yml`` and ``test_grids3_data1.yml`` will be created.

The names of these files can be controlled using the ``ids`` `keyword for parametrize
<https://docs.pytest.org/en/stable/example/parametrize.html#different-options-for-test-ids>`_, so
instead of ``data0``, you can define more useful names such as ``short`` and ``long``:

.. code-block:: python

    @pytest.mark.parametrize('data', [summary_grids(), summary_grids_2()], ids=['short', 'long'])
    def test_grids3(data_regression, data):
        data_regression.check(data)

which creates ``test_grids3_short.yml`` and ``test_grids3_long.yml`` respectively.

Data directory path
-------------------

Optionally you can configure your own *data directory* paths by overriding
the fixtures provided by `pytest-datadir <https://github.com/gabrielcnr/pytest-datadir>`__.

The trick is to use the standard fixture override mechanism provided by pytest, to change the `original_datadir` and `lazy_datadir` to return
other paths customized to your test suite.

For example, you can hard-code the paths like this:

.. code-block:: python

    import pytest
    from pathlib import Path
    from myapp.config import PATH


    @pytest.fixture(scope="session")
    def lazy_datadir() -> Path:
        return PATH.repo / "test-data-regression"


    @pytest.fixture(scope="session")
    def original_datadir() -> Path:
        return PATH.repo / "test-data-regression"

An alternative would be to configure this using the configuration file:

.. code-block:: ini

    [pytest]
    lazy_datadir = mydatadir
    original_datadir = my_originaldatadir

Next, register the path parameter options in `conftest.py`:

.. code-block:: python

    def pytest_addoption(parser):
        parser.addini("lazy_datadir", "my own datadir for pytest-regressions")
        parser.addini("original_datadir", "my own original_datadir for pytest-regressions")

Finally, override the fixtures to use the new options.

.. code-block:: python

  import pytest
  import pathlib

  @pytest.fixture(scope="session")
  def original_datadir(request) -> pathlib.Path:
      config = request.config
      return config.rootpath / config.getini('original_datadir')


  @pytest.fixture(scope="session")
  def lazy_datadir(request) -> pathlib.Path:
      config = request.config
      return config.rootpath / config.getini('lazy_datadir')

Generated Filenames
-------------------

Optionally you can configure the generated filenames by using the ``basename`` parameter of the fixture. The name can be changed to anything as long as it does not conflict with other tests.
In the following example, the filename will be "my_custom_name.yml":

.. code-block:: python

    def test_grids3(data_regression, data):
        data_regression.check(data, basename="my_custom_name")

.. note::

    If one wants to continue using the test name as the filename and only add prefix or suffixes,
    It is possible to rely on the `request` fixture to get the test name and use it to generate the filename.

    .. code-block:: python

        def test_grids3(data_regression, data1, data2, request):
            data_regression.check(data1, basename=f"{request.node.name}_data1")
            data_regression.check(data2, basename=f"{request.node.name}_data2")
