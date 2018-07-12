def test_example(data_regression):
    """Basic example"""
    contents = {"contents": "Foo", "value": 11}
    data_regression.check(contents)


def test_basename(data_regression):
    """Basic example using basename parameter"""
    contents = {"contents": "Foo", "value": 11}
    data_regression.check(contents, basename="case.normal")
