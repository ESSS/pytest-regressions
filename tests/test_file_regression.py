# encoding: UTF-8
import os
import textwrap

import pytest
import six

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


def test_file_regression_fixture(testdir, monkeypatch):
    """
    :type testdir: _pytest.pytester.TmpTestdir
    :type monkeypatch: _pytest.monkeypatch.monkeypatch
    """
    import sys

    monkeypatch.setattr(sys, "GetData", lambda: "foo", raising=False)
    source = """
        import sys
        def test_1(file_regression):
            contents = sys.GetData()
            file_regression.Check(contents, extension='.test')
    """

    def GetFileContents():
        txt_filename = os.path.join(
            six.text_type(testdir.tmpdir), "test_file", "test_1.test"
        )
        assert os.path.isfile(txt_filename)
        with open(txt_filename) as f:
            return f.read()

    check_regression_fixture_workflow(
        testdir,
        source,
        data_getter=GetFileContents,
        data_modifier=lambda: monkeypatch.setattr(
            sys, "GetData", lambda: "foobar", raising=False
        ),
        expected_data_1="foo",
        expected_data_2="foobar",
    )
