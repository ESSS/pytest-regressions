# encoding: UTF-8
from functools import partial

import six

from .common import perform_regression_check, check_text_files


class FileRegressionFixture(object):
    """
    Implementation of `file_regression` fixture.
    """

    def __init__(self, datadir, original_datadir, request):
        """
        :type datadir: Path
        :type original_datadir: Path
        :type request: FixtureRequest
        """
        self.request = request
        self.datadir = datadir
        self.original_datadir = original_datadir
        self.force_regen = False

    def check(
        self,
        contents,
        encoding=None,
        extension=".txt",
        newline=None,
        basename=None,
        fullpath=None,
        binary=False,
        obtained_filename=None,
        check_fn=None,
    ):
        """
        Checks the contents against a previously recorded version, or generate a new file.

        :param six.text_type contents: contents to write to the file
        :param six.text_type|None encoding: Encoding used to write file, if any.
        :param six.text_type extension: Extension of file.
        :param six.text_type|None newline: See `io.open` docs.
        :param bool binary: If the file is binary or text.
        :param obtained_filename: ..see:: FileRegressionCheck
        :param check_fn: a function with signature (obtained_filename, expected_filename) that should raise
            AssertionError if both files differ.
            If not given, use internal TODO.

        ..see: `data_regression.Check` for `basename` and `fullpath` arguments.
        """
        __tracebackhide__ = 0

        if binary and encoding:
            raise ValueError(
                "Only binary ({!r}) or encoding ({!r}) parameters must be passed at the same time.".format(
                    binary, encoding
                )
            )

        if binary:
            assert isinstance(
                contents, six.binary_type
            ), "Expected bytes contents but received type {}".format(
                type(contents).__name__
            )
        else:
            assert isinstance(
                contents, six.text_type
            ), "Expected text/unicode contents but received type {}".format(
                type(contents).__name__
            )

        import io

        if check_fn is None:

            if binary:

                def check_fn(obtained_filename, expected_filename):
                    if obtained_filename.read_bytes() != expected_filename.read_bytes():
                        raise AssertionError(
                            "Binary files {} and {} differ.".format(
                                obtained_filename, expected_filename
                            )
                        )

            else:
                check_fn = partial(check_text_files, encoding=encoding)

        def dump_fn(filename):
            mode = "wb" if binary else "w"
            with io.open(
                six.text_type(filename), mode, encoding=encoding, newline=newline
            ) as f:
                f.write(contents)

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
            obtained_filename=obtained_filename,
        )

    # non-PEP 8 alias used internally at ESSS
    Check = check
