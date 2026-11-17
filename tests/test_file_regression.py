import sys
import textwrap

import pytest

from pytest_regressions.file_regression import FileRegressionFixture
from pytest_regressions.testing import check_regression_fixture_workflow


def test_simple_text_file(file_regression: FileRegressionFixture):
    contents = textwrap.dedent("""\
        # Title
        Another line: olá
    """)
    file_regression.check(contents, encoding="latin1", extension=".md")


def test_simple_bin_file(file_regression: FileRegressionFixture):
    contents = b"binary contents \xff\xff\xde"
    file_regression.check(contents, binary=True, extension=".bin")


def test_binary_and_text_error(file_regression: FileRegressionFixture):
    with pytest.raises(ValueError):
        file_regression.check("", encoding="UTF-8", binary=True)


def test_skips_obtained_write_on_match(
    file_regression: FileRegressionFixture, tmp_path
):
    """When ``contents`` already matches the expected file, the
    ``.obtained`` sidecar is not written.
    """
    golden = tmp_path / "golden.txt"
    golden.write_text("hello\nworld\n", newline="")
    obtained = tmp_path / "golden.obtained.txt"

    file_regression.check(
        "hello\nworld\n",
        extension=".txt",
        newline="",
        fullpath=golden,
        obtained_filename=obtained,
    )

    assert not obtained.exists()


def test_skips_obtained_write_on_match_binary(
    file_regression: FileRegressionFixture, tmp_path
):
    """Same short-circuit for ``binary=True`` contents."""
    golden = tmp_path / "golden.bin"
    golden.write_bytes(b"\x00\x01\x02payload\xff")
    obtained = tmp_path / "golden.obtained.bin"

    file_regression.check(
        b"\x00\x01\x02payload\xff",
        binary=True,
        extension=".bin",
        fullpath=golden,
        obtained_filename=obtained,
    )

    assert not obtained.exists()


def test_writes_obtained_on_mismatch(file_regression: FileRegressionFixture, tmp_path):
    """A mismatch still goes through the standard path and the
    ``.obtained`` file is written.
    """
    golden = tmp_path / "golden.txt"
    golden.write_text("expected\n", newline="")
    obtained = tmp_path / "golden.obtained.txt"

    with pytest.raises(AssertionError, match="FILES DIFFER"):
        file_regression.check(
            "different\n",
            extension=".txt",
            newline="",
            fullpath=golden,
            obtained_filename=obtained,
        )

    assert obtained.exists()


@pytest.mark.parametrize("matches", [False, True])
def test_fullpath_and_basename_are_exclusive(file_regression, tmp_path, matches):
    golden = tmp_path / "golden.txt"
    golden.write_text("expected\n", encoding="utf-8")
    with pytest.raises(AssertionError, match="pass either basename or fullpath"):
        file_regression.check(
            "expected\n" if matches else "different\n",
            basename="explicit_name",
            fullpath=golden,
        )


@pytest.mark.parametrize("with_test_class_names", [False, True])
def test_fullpath_mismatch_uses_test_basename(
    pytester, tmp_path, with_test_class_names
):
    golden = tmp_path / "custom.txt"
    golden.write_text("expected\n", encoding="utf-8")
    obtained = tmp_path / "obtained"
    obtained.mkdir()
    pytester.makeconftest(f"""
        from pathlib import Path
        import pytest

        @pytest.fixture
        def lazy_datadir():
            return Path({str(obtained)!r})
        """)
    pytester.makepyfile(test_fullpath=f"""
        from pathlib import Path

        class TestSnapshots:
            def test_snapshot(self, file_regression):
                file_regression.check("different\\n", fullpath=Path({str(golden)!r}))
        """)
    args = ["--with-test-class-names"] if with_test_class_names else []
    result = pytester.runpytest_subprocess(*args)
    result.assert_outcomes(failed=1)
    basename = (
        "TestSnapshots_test_snapshot" if with_test_class_names else "test_snapshot"
    )
    assert (obtained / f"{basename}.obtained.txt").read_text(
        encoding="utf-8"
    ) == "different\n"
    assert (obtained / f"{basename}.obtained.diff.html").is_file()
    assert golden.read_text(encoding="utf-8") == "expected\n"


def test_custom_check_fn_disables_fast_path(
    file_regression: FileRegressionFixture, tmp_path
):
    """A user-supplied ``check_fn`` must always receive an obtained
    file, even when contents would match byte-exact.
    """
    golden = tmp_path / "golden.txt"
    golden.write_text("hello\n", newline="")
    obtained = tmp_path / "golden.obtained.txt"

    calls: list[tuple[str, str]] = []

    def my_check(obtained_fn, expected_fn):
        calls.append((str(obtained_fn), str(expected_fn)))

    file_regression.check(
        "hello\n",
        extension=".txt",
        newline="",
        fullpath=golden,
        obtained_filename=obtained,
        check_fn=my_check,
    )

    assert len(calls) == 1
    assert obtained.exists()


def test_file_regression_workflow(pytester, monkeypatch):
    monkeypatch.setattr(sys, "get_data", lambda: "foo", raising=False)
    source = """
        import sys
        def test_1(file_regression):
            contents = sys.get_data()
            file_regression.check(contents, extension='.test')
    """

    def get_file_contents():
        fn = pytester.path / "test_file" / "test_1.test"
        assert fn.is_file()
        return fn.read_text()

    check_regression_fixture_workflow(
        pytester,
        source,
        data_getter=get_file_contents,
        data_modifier=lambda: monkeypatch.setattr(
            sys, "get_data", lambda: "foobar", raising=False
        ),
        expected_data_1="foo",
        expected_data_2="foobar",
    )
