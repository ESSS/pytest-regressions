# encoding: UTF-8
from functools import partial

import yaml

from pytest_regressions.common import Path, check_text_files, perform_regression_check


class DataRegressionFixture(object):
    """
    Implementation of `data_regression` fixture.
    """

    def __init__(self, datadir, original_datadir, request):
        """
        :type datadir: Path
        :type original_datadir: Path
        :type request: FixtureRequest
        """
        self.request = request
        self.datadir = datadir
        self.original_datadir = original_datadir
        self.force_regen = False

    def check(self, data_dict, basename=None, fullpath=None):
        """
        Checks the given dict against a previously recorded version, or generate a new file.

        :param dict data_dict: any yaml serializable dict.

        :param six.text_type basename: basename of the file to test/record. If not given the name
            of the test is used.
            Use either `basename` or `fullpath`.

        :param six.text_type fullpath: complete path to use as a reference file. This option
            will ignore `datadir` fixture when reading _expected_ files but will still use it to
            write _obtained_ files.
            Useful if a reference file is located in the session data dir for example.
            Use either `basename` or `fullpath`.
        """
        __tracebackhide__ = False

        def dump(filename):
            """Dump dict contents to the given filename"""
            import yaml

            with filename.open("wb") as f:
                yaml.dump_all(
                    [data_dict],
                    f,
                    Dumper=RegressionYamlDumper,
                    default_flow_style=False,
                    allow_unicode=True,
                    indent=2,
                    encoding="utf-8",
                )

        perform_regression_check(
            datadir=self.datadir,
            original_datadir=self.original_datadir,
            request=self.request,
            check_fn=partial(check_text_files, encoding="UTF-8"),
            dump_fn=dump,
            extension=".yml",
            basename=basename,
            fullpath=fullpath,
            force_regen=self.force_regen,
        )

    # non-PEP 8 alias used internally at ESSS
    Check = check


class RegressionYamlDumper(yaml.SafeDumper):
    """
    Custom YAML dumper aimed for regression testing. Differences to usual YAML dumper:

    * Doesn't support aliases, as they produce confusing results on regression tests. The most
    definitive way to get rid of YAML aliases in the dump is to create an specialization that
    never allows aliases, as there isn't an argument that offers same guarantee
    (see http://pyyaml.org/ticket/91).
    """

    def ignore_aliases(self, data):
        return True

    @classmethod
    def add_custom_yaml_representer(cls, data_type, representer_fn):
        """
        Add custom representer to regression YAML dumper. It is polymorphic, so it works also for
        subclasses of `data_type`.

        :param type data_type: Type of objects.
        :param callable representer_fn: Function that receives ``(dumper, data)`` type as
            argument and must must return a YAML-convertible representation.
        """
        # Use multi-representer instead of simple-representer because it supports polymorphism.
        yaml.add_multi_representer(
            data_type, multi_representer=representer_fn, Dumper=cls
        )
