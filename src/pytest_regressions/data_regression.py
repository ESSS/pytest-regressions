import os
from functools import partial
from pathlib import Path
from typing import Any
from typing import Callable
from typing import Dict
from typing import Optional

import pytest
import yaml

from .common import check_text_files
from .common import perform_regression_check


class DataRegressionFixture:
    """
    Implementation of `data_regression` fixture.
    """

    def __init__(
        self, datadir: Path, original_datadir: Path, request: pytest.FixtureRequest
    ) -> None:
        self.request = request
        self.datadir = datadir
        self.original_datadir = original_datadir
        self.force_regen = False
        self.with_test_class_names = False

    def check(
        self,
        data_dict: Dict[str, Any],
        basename: Optional[str] = None,
        fullpath: Optional["os.PathLike[str]"] = None,
    ) -> None:
        """
        Checks the given dict against a previously recorded version, or generate a new file.

        :param data_dict: any yaml serializable dict.

        :param basename: basename of the file to test/record. If not given the name
            of the test is used.
            Use either `basename` or `fullpath`.

        :param fullpath: complete path to use as a reference file. This option
            will ignore ``datadir`` fixture when reading *expected* files but will still use it to
            write *obtained* files. Useful if a reference file is located in the session data dir for example.

        ``basename`` and ``fullpath`` are exclusive.
        """
        __tracebackhide__ = True

        def dump(filename: Path) -> None:
            """Dump dict contents to the given filename"""
            import yaml

            dumped_str = yaml.dump_all(
                [data_dict],
                Dumper=RegressionYamlDumper,
                default_flow_style=False,
                allow_unicode=True,
                indent=2,
                encoding="utf-8",
            )
            with filename.open("wb") as f:
                f.write(dumped_str)

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
            with_test_class_names=self.with_test_class_names,
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

    def ignore_aliases(self, data: object) -> bool:
        return True

    @classmethod
    def add_custom_yaml_representer(
        cls, data_type: type, representer_fn: Callable[[object, Any], None]
    ) -> None:
        """
        Add custom representer to regression YAML dumper. It is polymorphic, so it works also for
        subclasses of `data_type`.

        :param data_type: Type of objects.
        :param representer_fn: Function that receives ``(dumper, data)`` type as
            argument and must must return a YAML-convertible representation.
        """
        # Use multi-representer instead of simple-representer because it supports polymorphism.
        yaml.add_multi_representer(
            data_type, multi_representer=representer_fn, Dumper=cls
        )
