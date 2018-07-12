from __future__ import unicode_literals


def test_usage_workflow(testdir, monkeypatch):
    """
    :type testdir: _pytest.pytester.TmpTestdir

    :type monkeypatch: _pytest.monkeypatch.monkeypatch
    """
    import sys
    import yaml

    monkeypatch.setattr(
        sys, "testing_get_data", lambda: {"contents": "Foo", "value": 10}, raising=False
    )
    source = """
        import sys
        def test_1(data_regression):
            contents = sys.testing_get_data()
            data_regression.check(contents)
    """

    def get_yaml_contents():
        yaml_filename = testdir.tmpdir / "test_file" / "test_1.yml"
        assert yaml_filename.check(file=1)
        with yaml_filename.open() as f:
            return yaml.load(f)

    check_regression_fixture(
        testdir,
        source=source,
        data_getter=get_yaml_contents,
        data_modifier=lambda: monkeypatch.setattr(
            sys,
            "testing_get_data",
            lambda: {"contents": "Bar", "value": 20},
            raising=False,
        ),
        expected_data_1={"contents": "Foo", "value": 10},
        expected_data_2={"contents": "Bar", "value": 20},
    )


def check_regression_fixture(
    testdir, source, data_getter, data_modifier, expected_data_1, expected_data_2
):
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

    check_regression_fixture(
        testdir,
        source,
        data_getter=get_data,
        data_modifier=lambda: monkeypatch.setattr(sys, 'get_data', lambda: 'bar', raising=False),
        expected_data_1='foo',
        expected_data_2='bar',
    )
    ```

    :param Testdir testdir: `testdir` fixture. Requires pytest's `pytester` to be installed.
    :param str source: Source code using regression fixture.
    :param callable data_getter: Function without arguments that returns contents of file
        created by regression test when it fails first time (i.e. the expected file for future
        runs).
    :param callable data_modifier: Function without arguments that must change data compared by
        regression fixture so it fails in next comparison.
    :param object expected_data_1: Expected data in expected file for first state of data.
    :param object expected_data_1: Expected data in expected file for second state of data.
    """
    testdir.makepyfile(test_file=source)

    # First run fails because there's no expected file yet
    result = testdir.inline_run()
    result.assertoutcome(failed=1)

    # ensure now that the file was generated and the test passes
    assert data_getter() == expected_data_1
    result = testdir.inline_run()
    result.assertoutcome(passed=1)

    # changing the regression data makes the test fail (file remains unchanged)
    data_modifier()
    result = testdir.inline_run()
    result.assertoutcome(failed=1)
    assert data_getter() == expected_data_1

    # force regeneration (test fails again)
    result = testdir.inline_run("--force-regen")
    result.assertoutcome(failed=1)
    assert data_getter() == expected_data_2

    # test should pass again
    result = testdir.inline_run()
    result.assertoutcome(passed=1)