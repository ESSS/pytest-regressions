import sys
from textwrap import dedent

import pytest
import yaml

from pytest_regressions.testing import check_regression_fixture_workflow


def test_example(data_regression):
    """Basic example"""
    contents = {"contents": "Foo", "value": 11}
    data_regression.check(contents)


def test_basename(data_regression):
    """Basic example using basename parameter"""
    contents = {"contents": "Foo", "value": 11}
    data_regression.check(contents, basename="case.normal")


def test_integer_keys(data_regression):
    """Test that integer keys are supported in data dictionaries."""
    contents = {
        1: "first",
        2: "second",
        10: "tenth",
        100: "hundredth",
    }
    data_regression.check(contents)


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


def test_round_digits(data_regression):
    """Example including float numbers and check rounding capabilities."""
    contents = {
        "content": {"value1": "toto", "value": 1.123456789},
        "values": [1.12345, 2.34567],
        "value": 1.23456789,
    }
    data_regression.check(contents, round_digits=2)

    with pytest.raises(AssertionError):
        contents = {
            "content": {"value1": "toto", "value": 1.2345678},
            "values": [1.13456, 2.45678],
            "value": 1.23456789,
        }
        data_regression.check(contents, round_digits=2)


def test_usage_workflow(pytester, monkeypatch):
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
        yaml_filename = pytester.path / "test_file" / "test_1.yml"
        assert yaml_filename.is_file()
        with yaml_filename.open() as f:
            return yaml.safe_load(f)

    check_regression_fixture_workflow(
        pytester,
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


def test_data_regression_full_path(pytester, tmp_path):
    """
    Test data_regression with ``fullpath`` parameter.
    """
    fullpath = tmp_path.joinpath("full/path/to/contents.yaml")
    fullpath.parent.mkdir(parents=True)
    assert not fullpath.is_file()

    source = """
        def test(data_regression):
            contents = {'data': [1, 2]}
            data_regression.check(contents, fullpath=%s)
    """ % (
        repr(str(fullpath))
    )
    pytester.makepyfile(test_foo=source)
    # First run fails because there's no yml file yet
    result = pytester.inline_run()
    result.assertoutcome(failed=1)

    # ensure now that the file was generated and the test passes
    assert fullpath.is_file()
    result = pytester.inline_run()
    result.assertoutcome(passed=1)


def test_data_regression_no_aliases(pytester):
    """
    YAML standard supports aliases as can be seen here:
    http://pyyaml.org/wiki/PyYAMLDocumentation#Aliases.

    Even though this is a resourceful feature, data regression intends to be as human readable as
    possible and it was deemed that YAML aliases make it harder for developers to understand
    contents.

    This test makes sure data regression never uses aliases when dumping expected file to YAML.
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
    pytester.makepyfile(test_file=source)

    result = pytester.inline_run()
    result.assertoutcome(failed=1)

    yaml_file_contents = pytester.path.joinpath("test_file/test.yml").read_text()
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
    result = pytester.inline_run()
    result.assertoutcome(passed=1)


def test_not_create_file_on_error(pytester):
    """Basic example where we serializing the object should throw an error and should not create the file"""

    source = """
        def test(data_regression):
            class Scalar:
                def __init__(self, value, unit):
                    self.value = value
                    self.unit = unit

            contents = {"scalar": Scalar(10, "m")}
            data_regression.Check(contents)
    """
    pytester.makepyfile(test_file=source)

    result = pytester.inline_run()
    result.assertoutcome(failed=1)

    yaml_file = pytester.path.joinpath("test_file/test.yml")
    assert not yaml_file.is_file()


def test_regen_all(pytester, tmp_path):
    source = """
        def test_1(data_regression):
            contents = {"contents": "Foo", "value": 11}
            data_regression.check(contents, basename="test_1_a")

            contents = {"contents": "Bar", "value": 12}
            data_regression.check(contents, basename="test_1_b")

        def test_2(data_regression):
            contents = {"contents": "Baz", "value": 33}
            data_regression.check(contents, basename="test_2_a")

            contents = {"contents": "BazFoo", "value": 34}
            data_regression.check(contents, basename="test_2_b")
    """
    pytester.makepyfile(source)
    result = pytester.runpytest("--regen-all")

    result.stdout.fnmatch_lines("* 2 passed *")
    data_dir = pytester.path.joinpath("test_regen_all")
    assert {x.name for x in data_dir.iterdir()} == {
        "test_1_a.yml",
        "test_1_b.yml",
        "test_2_a.yml",
        "test_2_b.yml",
    }

    result = pytester.runpytest("--regen-all")
    result.stdout.fnmatch_lines("* 2 passed *")
    data_dir = pytester.path.joinpath("test_regen_all")
    assert {x.name for x in data_dir.iterdir()} == {
        "test_1_a.yml",
        "test_1_b.yml",
        "test_2_a.yml",
        "test_2_b.yml",
    }

    result = pytester.runpytest()
    result.stdout.fnmatch_lines("* 2 passed *")
    data_dir = pytester.path.joinpath("test_regen_all")
    assert {x.name for x in data_dir.iterdir()} == {
        "test_1_a.yml",
        "test_1_b.yml",
        "test_2_a.yml",
        "test_2_b.yml",
    }
