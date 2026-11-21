import json
import shutil
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from tempfile import mkdtemp
from tempfile import TemporaryDirectory
from weakref import WeakKeyDictionary
from weakref import WeakSet

import pytest

# Item.stash is unavailable on pytest 6. Weak keys also isolate in-process pytest sessions.
_pending: WeakKeyDictionary[object, TemporaryDirectory[str]] = WeakKeyDictionary()
_failed: WeakSet[object] = WeakSet()


@contextmanager
def _comparison_directory(parent: Path) -> Iterator[Path]:
    # Both the staging and export directories can contain concurrent or repeated checks.
    folder = Path(mkdtemp(prefix="comparison-", dir=parent))
    try:
        yield folder
    except OSError:
        shutil.rmtree(folder, ignore_errors=True)
        raise


def record_comparison(
    request: pytest.FixtureRequest, expected: Path, obtained: Path
) -> None:
    """Keep a private copy before the next check can overwrite the compared files."""
    if request.config.getoption("regression_artifacts") is None:
        return
    try:
        staging = _pending.get(request.node)
        if staging is None:
            staging = TemporaryDirectory(prefix="pytest-regressions-")
            _pending[request.node] = staging
        with _comparison_directory(Path(staging.name)) as folder:
            metadata = {"nodeid": request.node.nodeid}
            for role, source in (("expected", expected), ("obtained", obtained)):
                (folder / role).mkdir()
                destination = folder / role / source.name
                shutil.copyfile(source, destination)
                metadata[role] = destination.relative_to(folder).as_posix()
            (folder / "metadata.json").write_text(
                json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
            )
    except OSError as exc:
        request.node.add_report_section("call", "regression artifacts", str(exc))


def process_report(item: pytest.Item, report: "pytest.TestReport") -> None:
    directory = item.config.getoption("regression_artifacts")
    if directory is None:
        return
    if report.failed:
        _failed.add(item)
    failed = item in _failed
    if not failed and report.when != "teardown":
        return
    if report.when == "teardown":
        _failed.discard(item)
    staging = _pending.pop(item, None)
    if staging is None:
        return
    with staging as path:
        if failed:
            root = item.config.invocation_params.dir / directory
            try:
                for comparison in Path(path).iterdir():
                    root.mkdir(parents=True, exist_ok=True)
                    with _comparison_directory(root) as destination:
                        for file in comparison.iterdir():
                            shutil.move(str(file), destination)
            except OSError as exc:
                report.sections.append(("regression artifacts", str(exc)))
