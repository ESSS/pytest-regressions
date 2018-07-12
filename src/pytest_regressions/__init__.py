def add_custom_yaml_representer(data_type, representer_fn):
    """
    Add custom representer to regression YAML dumper. It is polymorphic, so it works also for
    subclasses of `data_type`.

    :param type data_type: Type of objects.
    :param callable representer_fn: Function that receives object of `data_type` type as
        argument and must must return a YAML-convertible representation.
    """
    from .data_regression import RegressionYamlDumper

    return RegressionYamlDumper.add_custom_yaml_representer(data_type, representer_fn)
