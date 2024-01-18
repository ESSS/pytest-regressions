import pathlib

import pytest


@pytest.fixture(scope="module")
def original_datadir(request) -> pathlib.Path:
    config = request.config
    return config.rootpath / config.getini("original_datadir")


@pytest.fixture(scope="module")
def datadir(request) -> pathlib.Path:
    config = request.config
    return config.rootpath / config.getini("datadir")


def test_user_specified_original_datadir(original_datadir):
    assert original_datadir.name == "my_originaldatadir"


def test_user_specified_datadir(datadir):
    assert datadir.name == "mydatadir"
