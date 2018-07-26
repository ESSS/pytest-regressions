from __future__ import unicode_literals

from textwrap import dedent

import six

from pytest_regressions.testing import check_regression_fixture_workflow


def test_example(data_regression):
    """Basic example"""
    contents = {"contents": "Foo", "value": 11}
    data_regression.check(contents)


def test_basename(data_regression):
    """Basic example using basename parameter"""
    contents = {"contents": "Foo", "value": 11}
    data_regression.check(contents, basename="case.normal")


def test_custom_object(data_regression):
    """Basic example where we register a custom conversion to dump objects"""

    class Scalar:
        def __init__(self, value, unit):
            self.value = value
            self.unit = unit

    def dump_scalar(dumper, scalar):
        return dumper.represent_dict(dict(value=scalar.value, unit=scalar.unit))

    from pytest_regressions import add_custom_yaml_representer

    add_custom_yaml_representer(Scalar, dump_scalar)

    contents = {"scalar": Scalar(10, "m")}

    data_regression.check(contents)


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

    check_regression_fixture_workflow(
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


def test_data_regression_full_path(testdir, tmpdir):
    """
    Test data_regression with ``fullpath`` parameter.

    :type testdir: _pytest.pytester.TmpTestdir
    """
    fullpath = tmpdir.join("full/path/to").ensure(dir=1).join("contents.yaml")
    assert not fullpath.isfile()

    source = """
        def test(data_regression):
            contents = {'data': [1, 2]}
            data_regression.check(contents, fullpath=%s)
    """ % (
        repr(six.text_type(fullpath))
    )
    testdir.makepyfile(test_foo=source)
    # First run fails because there's no yml file yet
    result = testdir.inline_run()
    result.assertoutcome(failed=1)

    # ensure now that the file was generated and the test passes
    assert fullpath.isfile()
    result = testdir.inline_run()
    result.assertoutcome(passed=1)


def test_data_regression_no_aliases(testdir):
    """
    YAML standard supports aliases as can be seen here:
    http://pyyaml.org/wiki/PyYAMLDocumentation#Aliases.

    Even though this is a resourceful feature, data regression intends to be as human readable as
    possible and it was deemed that YAML aliases make it harder for developers to understand
    contents.

    This test makes sure data regression never uses aliases when dumping expected file to YAML.

    :type testdir: _pytest.pytester.TmpTestdir
    """
    source = """
        def test(data_regression):
            red = (255, 0, 0)
            green = (0, 255, 0)
            blue = (0, 0, 255)

            contents = {
                'color1': red,
                'color2': green,
                'color3': blue,
                'color4': red,
                'color5': green,
                'color6': blue,
            }
            data_regression.Check(contents)
    """
    testdir.makepyfile(test_file=source)

    result = testdir.inline_run()
    result.assertoutcome(failed=1)

    yaml_file_contents = testdir.tmpdir.join("test_file", "test.yml").read()
    assert yaml_file_contents == dedent(
        """\
        color1:
        - 255
        - 0
        - 0
        color2:
        - 0
        - 255
        - 0
        color3:
        - 0
        - 0
        - 255
        color4:
        - 255
        - 0
        - 0
        color5:
        - 0
        - 255
        - 0
        color6:
        - 0
        - 0
        - 255
        """
    )
    result = testdir.inline_run()
    result.assertoutcome(passed=1)
