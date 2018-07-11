import pytest


def pytest_addoption(parser):
    group = parser.getgroup("regressions")
    group.addoption(
        "--force-regen",
        action="store_true",
        default=False,
        help="Re-generate all data_regression fixture data files.",
    )


@pytest.fixture
def data_regression(datadir, original_datadir, request):
    """
    Fixture used to test arbitrary data against known versions previously
    recorded by this same fixture. Useful to test 3rd party APIs or where testing directly
    generated data from other sources.

    Create a dict in your test containing a arbitrary data you want to test, and
    call the `Check` function. The first time it will fail but will generate a file in your
    data directory.

    Subsequent runs against the same data will now compare against the generated file and pass
    if the dicts are equal, or fail showing a diff otherwise. To regenerate the data,
    either set `force_regen` attribute to True or pass the `--force-regen` flag to pytest
    which will regenerate the data files for all tests. Make sure to diff the files to ensure
    the new changes are expected and not regressions.

    The dict may be anything serializable by the `yaml` library.

    :type datadir: Path
    :type request: FixtureRequest
    :rtype: DataRegressionFixture
    :return: Data regression fixture.
    """
    from .data_regression import DataRegressionFixture

    return DataRegressionFixture(datadir, original_datadir, request)
