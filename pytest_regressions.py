# -*- coding: utf-8 -*-
import difflib
from pathlib import Path

import pytest
import yaml


def pytest_addoption(parser):
    group = parser.getgroup('regressions')
    group.addoption(
        '--force-regen',
        action='store_true',
        default=False,
        help='Re-generate all data_regression fixture data files.',
    )


@pytest.fixture
def data_regression(datadir, original_datadir, request):
    """
    Fixture used to test arbitrary data against known versions previously
    recorded by this same fixture. Useful to test 3rd party APIs or where testing directly
    generated data from other sources.

    Create a dict in your test containing a arbitrary data you want to test, and
    call the `Check` function. The first time it will fail but will generate a file in your
    data directory.

    Subsequent runs against the same data will now compare against the generated file and pass
    if the dicts are equal, or fail showing a diff otherwise. To regenerate the data,
    either set `force_regen` attribute to True or pass the `--force-regen` flag to pytest
    which will regenerate the data files for all tests. Make sure to diff the files to ensure
    the new changes are expected and not regressions.

    The dict may be anything serializable by the `yaml` library.

    :type datadir: Path
    :type request: FixtureRequest
    :rtype: DataRegressionFixture
    :return: Data regression fixture.
    """
    return DataRegressionFixture(datadir, original_datadir, request)


class DataRegressionFixture(object):
    """
    Implementation of `data_regression` fixture.
    """

    def __init__(self, datadir, original_datadir, request):
        """
        :type datadir: Path
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

            with filename.open('wb') as f:
                yaml.dump_all(
                    [data_dict],
                    f,
                    Dumper=RegressionYamlDumper,
                    default_flow_style=False,
                    allow_unicode=True,
                    indent=2,
                    encoding='utf-8',
                )

        _regression_check(
            datadir=self.datadir,
            original_datadir=self.original_datadir,
            request=self.request,
            check_fn=check_text_files,
            dump_fn=dump,
            extension='.yml',
            basename=basename,
            fullpath=fullpath,
            force_regen=self.force_regen,
        )

    # non-PEP 8 alias used internally at ESSS
    Check = check


def _regression_check(
        datadir,
        original_datadir,
        request,
        check_fn,
        dump_fn,
        extension,
        basename=None,
        fullpath=None,
        force_regen=False,
        obtained_filename=None,
        dump_aux_fn=lambda filename: [],
):
    """
    First run of this check will generate a expected file. Following attempts will always try to
    match obtained files with that expected file.

    If expected file needs to be updated, just enable `force_regen` argument.

    :param Path datadir: Fixture embed_data.
    :param Path original_datadir: Fixture embed_data.
    :param SubRequest request: Pytest request object.
    :param callable check_fn: A function that receives as arguments, respectively, absolute path to
        obtained file and absolute path to expected file. It must assert if contents of file match.
        Function can safely assume that obtained file is already dumped and only care about
        comparison.
    :param callable dump_fn: A function that receive an absolute file path as argument. Implementor
        must dump file in this path.
    :param callable dump_aux_fn: A function that receives the same file path as ``dump_fn``, but may
        dump additional files to help diagnose this regression later (for example dumping image of
        3d views and plots to compare later). Must return the list of file names written (used to display).
    :param six.text_type extension: Extension of files compared by this check.
    :param bool force_regen: if true it will regenerate expected file.
    :param six.text_type obtained_filename: complete path to use to write the obtained file. By
        default will prepend `.obtained` before the file extension.
    ..see: `data_regression.Check` for `basename` and `fullpath` arguments.
    """
    import re

    assert not (basename and fullpath), "pass either basename or fullpath, but not both"

    __tracebackhide__ = False

    if basename is None:
        basename = re.sub("[\W]", "_", request.node.name)

    if fullpath:
        filename = source_filename = Path(fullpath)
    else:
        dump_ext = extension
        filename = (datadir / basename).with_suffix(dump_ext)
        source_filename = (original_datadir / basename).with_suffix(dump_ext)

    def make_location_message(banner, filename, aux_files):
        msg = [
            banner,
            '- {}'.format(filename),
        ]
        if aux_files:
            msg.append('Auxiliary:')
            msg += ['- {}'.format(x) for x in aux_files]
        return '\n'.join(msg)

    force_regen = force_regen or request.config.getoption('force_regen')
    if not filename.is_file():
        source_filename.parent.mkdir(parents=True, exist_ok=True)
        dump_fn(source_filename)
        aux_created = dump_aux_fn(source_filename)

        msg = make_location_message('File not found in data directory, created:', source_filename, aux_created)
        pytest.fail(msg)
    else:
        if obtained_filename is None:
            if fullpath:
                obtained_filename = (datadir / basename).with_suffix('.obtained' + extension)
            else:
                obtained_filename = filename.with_suffix('.obtained' + extension)

        dump_fn(obtained_filename)

        try:
            check_fn(obtained_filename, filename)
        except AssertionError:
            if force_regen:
                dump_fn(source_filename)
                aux_created = dump_aux_fn(source_filename)
                msg = make_location_message(
                    'Files differ and --force-regen set, regenerating file at:',
                    source_filename,
                    aux_created,
                )
                pytest.fail(msg)
            else:
                dump_aux_fn(obtained_filename)
                raise


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
        :param callable representer_fn: Function that receives object of `data_type` type as
            argument and must must return a YAML-convertible representation.
        """
        # Use multi-representer instead of simple-representer because it supports polymorphism.
        yaml.add_multi_representer(
            data_type,
            multi_representer=representer_fn,
            Dumper=cls)


def check_text_files(obtained_fn, expected_fn, fix_callback=lambda x: x, encoding=None):
    """
    Compare two files contents. If the files differ, show the diff and write a nice HTML
    diff file into the data directory.

    :param Path obtained_fn: path to obtained file during current testing.

    :param Path expected_fn: path to the expected file, obtained from previous testing.

    :param str encoding: encoding used to open the files.

    :param callable fix_callback:
        A callback to "fix" the contents of the obtained (first) file.
        This callback receives a list of strings (lines) and must also return a list of lines,
        changed as needed.
        The resulting lines will be used to compare with the contents of expected_fn.
    """
    __tracebackhide__ = False

    obtained_fn = Path(obtained_fn)
    expected_fn = Path(expected_fn)
    obtained_lines = fix_callback(obtained_fn.read_text(encoding=encoding).splitlines())
    expected_lines = expected_fn.read_text(encoding=encoding).splitlines()

    if obtained_lines != expected_lines:
        diff_lines = list(difflib.unified_diff(expected_lines, obtained_lines))
        if len(diff_lines) <= 500:
            html_fn = obtained_fn.with_suffix('.diff.html')
            try:
                differ = difflib.HtmlDiff()
                html_diff = differ.make_file(
                    fromlines=expected_lines,
                    fromdesc=expected_fn,
                    tolines=obtained_lines,
                    todesc=obtained_fn,
                )
            except Exception as e:
                html_fn = '(failed to generate html diff: %s)' % e
            else:
                html_fn.write_text(html_diff, encoding='UTF-8')

            diff = ['FILES DIFFER:', str(expected_fn), str(obtained_fn)]
            diff += ['HTML DIFF: %s' % html_fn]
            diff += diff_lines
            raise AssertionError('\n'.join(diff))
        else:
            # difflib has exponential scaling and for thousands of lines it starts to take minutes to render
            # the HTML diff.
            msg = [
                "Files are different, but diff is too big ({} lines)".format(len(diff_lines)),
                "- obtained: {}".format(obtained_fn),
                "- expected: {}".format(expected_fn),
            ]
            raise AssertionError('\n'.join(msg))
