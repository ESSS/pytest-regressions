import io
from functools import partial

import pytest
from PIL import Image

from pytest_regressions.testing import check_regression_fixture_workflow


@pytest.mark.parametrize("image_type", ["pil", "bytes"])
def test_image_regression(image_regression, lazy_datadir, image_type):
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

    image_filename = lazy_datadir / "test.png"
    fig.savefig(str(image_filename))

    if image_type == "bytes":
        image_data = image_filename.read_bytes()
    else:
        image_data = Image.open(image_filename)
    image_regression.check(
        image_data, diff_threshold=1.0, basename="test_image_regression"
    )


@pytest.mark.parametrize("image_type", ["pil", "bytes"])
def test_image_regression_workflow(pytester, monkeypatch, image_type):
    import sys

    from PIL import Image

    def get_image(color):
        img = Image.new("RGB", (100, 100), color)
        if image_type == "pil":
            return img
        else:
            f = io.BytesIO()
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
        fn = pytester.path / "test_file" / "test_1.png"
        assert fn.is_file()
        if image_type == "pil":
            # Copy is necessary because Image.open returns a ImageFile class
            return Image.open(fn).copy()
        else:
            return fn.read_bytes()

    check_regression_fixture_workflow(
        pytester,
        source,
        data_getter=get_file_contents,
        data_modifier=lambda: monkeypatch.setattr(
            sys, "get_image", partial(get_image, "black"), raising=False
        ),
        expected_data_1=get_image("white"),
        expected_data_2=get_image("black"),
    )
