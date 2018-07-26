import io
from functools import partial
from pytest_regressions.common import Path

from pytest_regressions.testing import check_regression_fixture_workflow


def test_image_regression(image_regression, datadir):
    import matplotlib

    # this ensures matplot lib does not use a GUI backend (such as Tk)
    matplotlib.use("Agg")

    import matplotlib.pyplot as plt
    import numpy as np

    t = np.arange(0.0, 2.0, 0.01)
    s = 1 + np.sin(2 * np.pi * t)

    fig, ax = plt.subplots()
    ax.plot(t, s)

    ax.set(
        xlabel="time (s)",
        ylabel="voltage (mV)",
        title="About as simple as it gets, folks",
    )
    ax.grid()

    image_filename = datadir / "test.png"
    fig.savefig(str(image_filename))

    image_regression.check(image_filename.read_bytes(), diff_threshold=1.0)


def test_image_regression_workflow(testdir, monkeypatch, datadir):
    """
    :type testdir: _pytest.pytester.TmpTestdir
    :type monkeypatch: _pytest.monkeypatch.monkeypatch
    """
    import sys
    from PIL import Image

    def get_image(color):
        f = io.BytesIO()
        img = Image.new("RGB", (100, 100), color)
        img.save(f, "PNG")
        return f.getvalue()

    monkeypatch.setattr(sys, "get_image", partial(get_image, "white"), raising=False)
    source = """
        import sys
        def test_1(image_regression):
            contents = sys.get_image()
            image_regression.check(contents)
    """

    def get_file_contents():
        fn = Path(str(testdir.tmpdir)) / "test_file" / "test_1.png"
        assert fn.is_file()
        return fn.read_bytes()

    check_regression_fixture_workflow(
        testdir,
        source,
        data_getter=get_file_contents,
        data_modifier=lambda: monkeypatch.setattr(
            sys, "get_image", partial(get_image, "black"), raising=False
        ),
        expected_data_1=partial(get_image, "white"),
        expected_data_2=partial(get_image, "black"),
    )
