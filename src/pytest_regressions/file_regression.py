import os
from functools import partial
from pathlib import Path
from typing import Callable
from typing import Optional
from typing import Union

import pytest

from .common import check_text_files
from .common import perform_regression_check


class FileRegressionFixture:
    """
    Implementation of `file_regression` fixture.
    """

    def __init__(
        self, datadir: Path, original_datadir: Path, request: pytest.FixtureRequest
    ) -> None:
        self.request = request
        self.datadir = datadir
        self.original_datadir = original_datadir
        self.force_regen = False
        self.with_test_class_names = False

    def check(
        self,
        contents: Union[str, bytes],
        encoding: Optional[str] = None,
        extension: str = ".txt",
        newline: Optional[str] = None,
        basename: Optional[str] = None,
        fullpath: Optional["os.PathLike[str]"] = None,
        binary: bool = False,
        obtained_filename: Optional["os.PathLike[str]"] = None,
        check_fn: Optional[Callable[[Path, Path], None]] = None,
    ) -> None:
        """
        Checks the contents against a previously recorded version, or generate a new file.

        :param contents: content to be verified.
        :param encoding: Encoding used to write file, if any.
        :param extension: Extension of file.
        :param newline: See `io.open` docs.
        :param binary: If the file is binary or text.
        :param obtained_filename: ..see:: FileRegressionCheck
        :param check_fn: a function with signature ``(obtained_filename, expected_filename)`` that should raise
            AssertionError if both files differ.
            If not given, use internal function which compares text using :py:mod:`difflib`.
        """
        __tracebackhide__ = True

        if binary and encoding:
            raise ValueError(
                "Only binary ({!r}) or encoding ({!r}) parameters must be passed at the same time.".format(
                    binary, encoding
                )
            )

        if binary:
            assert isinstance(
                contents, bytes
            ), "Expected bytes contents but received type {}".format(
                type(contents).__name__
            )
        else:
            assert isinstance(
                contents, str
            ), "Expected text/unicode contents but received type {}".format(
                type(contents).__name__
            )

        if check_fn is None:

            if binary:

                def check_fn(obtained_filename: Path, expected_filename: Path) -> None:
                    if obtained_filename.read_bytes() != expected_filename.read_bytes():
                        raise AssertionError(
                            "Binary files {} and {} differ.".format(
                                obtained_filename, expected_filename
                            )
                        )

            else:
                check_fn = partial(check_text_files, encoding=encoding)

        def dump_fn(filename: Path) -> None:
            mode = "wb" if binary else "w"
            with open(str(filename), mode, encoding=encoding, newline=newline) as f:
                f.write(contents)

        assert check_fn is not None
        perform_regression_check(
            datadir=self.datadir,
            original_datadir=self.original_datadir,
            request=self.request,
            check_fn=check_fn,
            dump_fn=dump_fn,
            extension=extension,
            basename=basename,
            fullpath=fullpath,
            force_regen=self.force_regen,
            with_test_class_names=self.with_test_class_names,
            obtained_filename=obtained_filename,
        )

    # non-PEP 8 alias used internally at ESSS
    Check = check
