# encoding: UTF-8
import textwrap

import pytest


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
