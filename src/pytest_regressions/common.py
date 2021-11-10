import difflib
from pathlib import Path

import pytest


def import_error_message(libname):
    return f"'{libname}' library is an optional dependency and must be installed explicitly when the fixture 'check' is used"


def check_text_files(obtained_fn, expected_fn, fix_callback=lambda x: x, encoding=None):
    """
    Compare two files contents. If the files differ, show the diff and write a nice HTML
    diff file into the data directory.

    :param Path obtained_fn: path to obtained file during current testing.

    :param Path expected_fn: path to the expected file, obtained from previous testing.

    :param str encoding: encoding used to open the files.

    :param callable fix_callback:
        A callback to "fix" the contents of the obtained (first) file.
        This callback receives a list of strings (lines) and must also return a list of lines,
        changed as needed.
        The resulting lines will be used to compare with the contents of expected_fn.
    """
    __tracebackhide__ = True

    obtained_fn = Path(obtained_fn)
    expected_fn = Path(expected_fn)
    obtained_lines = fix_callback(obtained_fn.read_text(encoding=encoding).splitlines())
    expected_lines = expected_fn.read_text(encoding=encoding).splitlines()

    if obtained_lines != expected_lines:
        diff_lines = list(
            difflib.unified_diff(expected_lines, obtained_lines, lineterm="")
        )
        if len(diff_lines) <= 500:
            html_fn = obtained_fn.with_suffix(".diff.html")
            try:
                differ = difflib.HtmlDiff()
                html_diff = differ.make_file(
                    fromlines=expected_lines,
                    fromdesc=expected_fn,
                    tolines=obtained_lines,
                    todesc=obtained_fn,
                )
            except Exception as e:
                html_fn = "(failed to generate html diff: %s)" % e
            else:
                html_fn.write_text(html_diff, encoding="UTF-8")

            diff = ["FILES DIFFER:", str(expected_fn), str(obtained_fn)]
            diff += ["HTML DIFF: %s" % html_fn]
            diff += diff_lines
            raise AssertionError("\n".join(diff))
        else:
            # difflib has exponential scaling and for thousands of lines it starts to take minutes to render
            # the HTML diff.
            msg = [
                "Files are different, but diff is too big ({} lines)".format(
                    len(diff_lines)
                ),
                f"- obtained: {obtained_fn}",
                f"- expected: {expected_fn}",
            ]
            raise AssertionError("\n".join(msg))


def perform_regression_check(
    datadir,
    original_datadir,
    request,
    check_fn,
    dump_fn,
    extension,
    basename=None,
    fullpath=None,
    force_regen=False,
    with_test_class_names=False,
    obtained_filename=None,
    dump_aux_fn=lambda filename: [],
):
    """
    First run of this check will generate a expected file. Following attempts will always try to
    match obtained files with that expected file.

    If expected file needs to be updated, just enable `force_regen` argument.

    :param Path datadir: Fixture embed_data.
    :param Path original_datadir: Fixture embed_data.
    :param SubRequest request: Pytest request object.
    :param callable check_fn: A function that receives as arguments, respectively, absolute path to
        obtained file and absolute path to expected file. It must assert if contents of file match.
        Function can safely assume that obtained file is already dumped and only care about
        comparison.
    :param callable dump_fn: A function that receive an absolute file path as argument. Implementor
        must dump file in this path.
    :param callable dump_aux_fn: A function that receives the same file path as ``dump_fn``, but may
        dump additional files to help diagnose this regression later (for example dumping image of
        3d views and plots to compare later). Must return the list of file names written (used to display).
    :param str extension: Extension of files compared by this check.
    :param bool force_regen: if true it will regenerate expected file.
    :param bool with_test_class_names: if true it will use the test class name (if any) to compose
        the basename.
    :param str obtained_filename: complete path to use to write the obtained file. By
        default will prepend `.obtained` before the file extension.
    ..see: `data_regression.Check` for `basename` and `fullpath` arguments.
    """
    import re

    assert not (basename and fullpath), "pass either basename or fullpath, but not both"

    __tracebackhide__ = True

    with_test_class_names = with_test_class_names or request.config.getoption(
        "with_test_class_names"
    )
    if basename is None:
        if (request.node.cls is not None) and (with_test_class_names):
            basename = re.sub(r"[\W]", "_", request.node.cls.__name__) + "_"
        else:
            basename = ""
        basename += re.sub(r"[\W]", "_", request.node.name)

    if fullpath:
        filename = source_filename = Path(fullpath)
    else:
        filename = datadir / (basename + extension)
        source_filename = original_datadir / (basename + extension)

    def make_location_message(banner, filename, aux_files):
        msg = [banner, f"- {filename}"]
        if aux_files:
            msg.append("Auxiliary:")
            msg += [f"- {x}" for x in aux_files]
        return "\n".join(msg)

    force_regen = force_regen or request.config.getoption("force_regen")
    if not filename.is_file():
        source_filename.parent.mkdir(parents=True, exist_ok=True)
        dump_fn(source_filename)
        aux_created = dump_aux_fn(source_filename)

        msg = make_location_message(
            "File not found in data directory, created:", source_filename, aux_created
        )
        pytest.fail(msg)
    else:
        if obtained_filename is None:
            if fullpath:
                obtained_filename = (datadir / basename).with_suffix(
                    ".obtained" + extension
                )
            else:
                obtained_filename = filename.with_suffix(".obtained" + extension)

        dump_fn(obtained_filename)

        try:
            check_fn(obtained_filename, filename)
        except AssertionError:
            if force_regen:
                dump_fn(source_filename)
                aux_created = dump_aux_fn(source_filename)
                msg = make_location_message(
                    "Files differ and --force-regen set, regenerating file at:",
                    source_filename,
                    aux_created,
                )
                pytest.fail(msg)
            else:
                dump_aux_fn(obtained_filename)
                raise
