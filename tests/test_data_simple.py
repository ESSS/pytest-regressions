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
