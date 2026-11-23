import json

import pytest


def test_exports_failed_comparisons(pytester):
    pytester.makepyfile("""
        from pathlib import Path
        import pytest

        @pytest.mark.parametrize("value", [b"changed", b"other", b"expected"])
        def test_binary(file_regression, monkeypatch, tmp_path, value):
            monkeypatch.chdir(tmp_path)
            golden = Path("golden.bin")
            golden.write_bytes(b"expected")
            file_regression.check(value, binary=True, fullpath=golden, extension=".bin",
                                  obtained_filename=Path("actual.bin"))
        """)
    result = pytester.runpytest("--regression-artifacts=artifacts")
    result.assert_outcomes(passed=1, failed=2)
    artifacts = pytester.path / "artifacts"
    failures = sorted(artifacts.iterdir())
    assert len(failures) == 2
    for folder in failures:
        info = json.loads((folder / "metadata.json").read_text(encoding="utf-8"))
        obtained = (folder / info["obtained"]).read_bytes()
        assert obtained in (b"changed", b"other")
        assert info["nodeid"].endswith("::test_binary[%s]" % obtained.decode())
        assert (folder / info["expected"]).read_bytes() == b"expected"
        assert sorted(p.name for p in folder.rglob("*.bin")) == [
            "actual.bin",
            "golden.bin",
        ]


@pytest.mark.parametrize("regen", ["--force-regen", "--regen-all"])
def test_regeneration_does_not_export_artifacts(pytester, regen):
    pytester.makepyfile("""
        from pathlib import Path
        def test_data(file_regression):
            golden = Path("reference.txt")
            golden.write_text("old")
            file_regression.check("new", fullpath=golden)
        """)
    result = pytester.runpytest("--regression-artifacts=artifacts", regen)
    if regen == "--force-regen":
        result.assert_outcomes(failed=1)
    else:
        result.assert_outcomes(passed=1)
    assert (pytester.path / "reference.txt").read_text() == "new"
    assert not (pytester.path / "artifacts").exists()


def test_failed_export_preserves_original_comparison(pytester):
    pytester.makepyfile("""
        from pathlib import Path

        def test_comparison(file_regression):
            golden = Path("shared.txt")
            golden.write_text("expected")

            def check(obtained, expected):
                obtained.unlink()
                raise AssertionError("custom mismatch")

            file_regression.check("obtained", fullpath=golden, check_fn=check)
        """)
    result = pytester.runpytest("--regression-artifacts=artifacts")
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(
        ["*AssertionError: custom mismatch*", "*regression artifacts*"]
    )
    assert not (pytester.path / "artifacts").exists()


def test_only_exports_from_failed_tests(pytester):
    pytester.makepyfile("""
        from pathlib import Path
        import pytest

        def compare(file_regression, value):
            golden = Path("same.txt")
            golden.write_text("expected " + value)
            file_regression.check("obtained " + value, fullpath=golden,
                                  obtained_filename=Path("actual.txt"))

        def test_caught(file_regression):
            with pytest.raises(AssertionError):
                compare(file_regression, "caught")

        @pytest.mark.xfail(reason="known difference")
        def test_expected_failure(file_regression):
            compare(file_regression, "xfail")

        def test_skipped(file_regression):
            with pytest.raises(AssertionError):
                compare(file_regression, "skipped")
            pytest.skip()

        def test_failed(file_regression):
            with pytest.raises(AssertionError):
                compare(file_regression, "first")
            compare(file_regression, "second")
        """)
    result = pytester.runpytest("--regression-artifacts=artifacts")
    result.assert_outcomes(passed=1, failed=1, skipped=1, xfailed=1)
    files = []
    for directory in (pytester.path / "artifacts").iterdir():
        meta = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
        assert meta["nodeid"].endswith("::test_failed")
        files.append(
            (
                (directory / meta["expected"]).read_text(),
                (directory / meta["obtained"]).read_text(),
            )
        )
    assert sorted(files) == [
        ("expected first", "obtained first"),
        ("expected second", "obtained second"),
    ]


def test_unwritable_export_reports_both_errors(pytester):
    (pytester.path / "artifacts").write_text("keep this file")
    pytester.makepyfile("""
        from pathlib import Path
        def test_mismatch(file_regression):
            golden = Path("golden.txt")
            golden.write_text("expected")
            file_regression.check("obtained", fullpath=golden)
        """)
    result = pytester.runpytest("--regression-artifacts=artifacts")
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(
        ["*FILES DIFFER*", "*regression artifacts*", "*artifacts*"]
    )
    assert (pytester.path / "artifacts").read_text() == "keep this file"
