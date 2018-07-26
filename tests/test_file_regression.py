# encoding: UTF-8
from __future__ import unicode_literals
import textwrap
from pytest_regressions.common import Path

import pytest

from pytest_regressions.testing import check_regression_fixture_workflow


def test_simple_text_file(file_regression, datadir):
    contents = textwrap.dedent(
        """\
        # Title
        Another line: olá
    """
    )
    file_regression.check(contents, encoding="latin1", extension=".md")


def test_simple_bin_file(file_regression, datadir):
    contents = b"binary contents \xff\xff\xde"
    file_regression.check(contents, binary=True, extension=".bin")


def test_binary_and_text_error(file_regression):
    with pytest.raises(ValueError):
        file_regression.check("", encoding="UTF-8", binary=True)


def test_file_regression_workflow(testdir, monkeypatch):
    """
    :type testdir: _pytest.pytester.TmpTestdir
    :type monkeypatch: _pytest.monkeypatch.monkeypatch
    """
    import sys

    monkeypatch.setattr(sys, "get_data", lambda: "foo", raising=False)
    source = """
        import sys
        def test_1(file_regression):
            contents = sys.get_data()
            file_regression.check(contents, extension='.test')
    """

    def get_file_contents():
        fn = Path(str(testdir.tmpdir)) / "test_file" / "test_1.test"
        assert fn.is_file()
        return fn.read_text()

    check_regression_fixture_workflow(
        testdir,
        source,
        data_getter=get_file_contents,
        data_modifier=lambda: monkeypatch.setattr(
            sys, "get_data", lambda: "foobar", raising=False
        ),
        expected_data_1="foo",
        expected_data_2="foobar",
    )
