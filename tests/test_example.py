def test_example(data_regression):
    contents = {"contents": "Foo", "value": 11}
    data_regression.check(contents)
