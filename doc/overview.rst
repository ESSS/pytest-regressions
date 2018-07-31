Overview
========

``pytest-regressions`` provides some fixtures that make it easy to maintain tests that
generate lots of data or specific data files like images.

This plugin uses a *data directory* (courtesy of `pytest-datadir <https://github.com/gabrielcnr/pytest-datadir>`_) to
store expected data files, which are stored and used as baseline for future test runs.

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
* **Maintenance burden**: if the data changes in the future (and it will) it will be a major head-ache to update the values,
  specially if there are a lot of similar tests like this one.


Using data_regression
---------------------

The ``data_regression`` fixture provides a method to check general dictionary data like the one in the previous example.

Just declare the ``data_regression`` fixture and call the ``check`` method:

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

This file should be committed to version control.

The next time you run this test, it will compare the results of ``summary_grids()`` with the contents of the YAML file.
If they match, the test passes. If they don't match the test will fail, showing a nice diff of the text differences.

If the test fails because the new data is correct (the implementation might be returning more information about the
grids for example), then you can use the ``--force-regen`` flag to update the expected file::

    $ pytest --force-regen


and commit the updated file.

This workflow makes it very simple to keep the files up to date and to check all the information we need.
