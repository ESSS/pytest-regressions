from typing import Any
from typing import Callable
from typing import Optional

import pytest


def check_regression_fixture_workflow(
    pytester: pytest.Pytester,
    source: str,
    data_getter: Callable[[], Any],
    data_modifier: Callable[[], Any],
    expected_data_1: Any,
    expected_data_2: Any,
    compare_fn: Optional[Callable[[object, object], None]] = None,
) -> None:
    """
    Helper method to test regression fixtures like `data_regression`. Offers a basic template/script
    able to validate main behaviors expected by regression fixtures.

    Usage
    -----

    ```
    import sys

    monkeypatch.setattr(sys, 'get_data', lambda: 'foo', raising=False)
    source = '''
        import sys
        def test_1(fake_regression):
            data = sys.get_data()
            fake_regression.Check(data)
    '''

    def get_data():
        fake_filename = os.path.join(str(testdir.tmpdir), 'test_file', 'test_1.fake')
        assert os.path.isfile(fake_filename)
        with open(fake_filename) as f:
            return f.read()

    check_regression_fixture_workflow(
        pytester,
        source,
        data_getter=get_data,
        data_modifier=lambda: monkeypatch.setattr(sys, 'get_data', lambda: 'bar', raising=False),
        expected_data_1='foo',
        expected_data_2='bar',
    )
    ```

    :param pytester: pytester fixture.
    :param source: Source code using regression fixture.
    :param data_getter: Function without arguments that returns contents of file
        created by regression test when it fails first time (i.e. the expected file for future
        runs).
    :param data_modifier: Function without arguments that must change data compared by
        regression fixture so it fails in next comparison.
    :param expected_data_1: Expected data in expected file for first state of data.
    :param expected_data_2: Expected data in expected file for second state of data.
    :param compare_fn: function with signature (obtained, expected) used to ensure
        both data are equal. Should raise an assertion error if both objects are not equal.
    """
    if compare_fn is None:

        def compare_fn(x: object, y: object) -> None:
            assert x == y

    assert compare_fn is not None
    pytester.makepyfile(test_file=source)

    # First run fails because there's no expected file yet
    result = pytester.inline_run()
    result.assertoutcome(failed=1)

    # ensure now that the file was generated and the test passes
    xx = data_getter()
    compare_fn(xx, expected_data_1)
    result = pytester.inline_run()
    result.assertoutcome(passed=1)

    # changing the regression data makes the test fail (file remains unchanged)
    data_modifier()
    result = pytester.inline_run()
    result.assertoutcome(failed=1)
    compare_fn(data_getter(), expected_data_1)

    # force regeneration (test fails again)
    result = pytester.inline_run("--force-regen")
    result.assertoutcome(failed=1)
    compare_fn(data_getter(), expected_data_2)

    # test should pass again
    result = pytester.inline_run()
    result.assertoutcome(passed=1)
