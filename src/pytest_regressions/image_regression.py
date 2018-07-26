# encoding: UTF-8
import io
from functools import partial

import six

from pytest_regressions.common import perform_regression_check


class ImageRegressionFixture(object):
    """
    Regression test for image objects, accounting for small differences.
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

    def _load_image(self, filename):
        """
        Reads the image from the given file and convert it to RGB if necessary.
        This is necessary to be used with the ImageChops module operations.
        At this time, in this module, channel operations are only implemented
        for 8-bit images (e.g. "L" and "RGB").

        :param Path filename:
            The name of the file
        """
        from PIL import Image

        img = Image.open(six.text_type(filename), "r")
        if img.mode not in ("L" or "RGB"):
            return img.convert("RGB")
        else:
            return img

    def _compute_manhattan_distance(self, diff_image):
        """
        Computes a percentage of similarity of the difference image given.

        :param PIL.Image diff_image:
            An image in RGB mode computed from ImageChops.difference
        """
        import numpy

        number_of_pixels = diff_image.size[0] * diff_image.size[1]
        return (
            # To obtain a number in 0.0 -> 100.0
            100.0
            * (
                # Compute the sum of differences
                numpy.sum(diff_image)
                /
                # Divide by the number of channel differences RGB * Pixels
                float(3 * number_of_pixels)
            )
            # Normalize between 0.0 -> 1.0
            / 255.0
        )

    def _check_images_manhattan_distance(
        self, obtained_file, expected_file, expect_equal, diff_threshold
    ):
        """
        Compare two image by computing the differences spatially, pixel by pixel.

        The Manhattan Distance is used to compute how much two images differ.

        :param six.text_type obtained_file:
            The image with the obtained image

        :param six.text_type expected_files:
            The image with the expected image

        :param bool expected_equal:
            If True, the images are expected to be equal, otherwise, they're expected to be
            different.

        :param float diff_threshold:
            The maximum percentage of difference accepted.
            A value between 0.0 and 100.0

        :raises AssertionError:
            raised if they are actually different and expect_equal is False or
            if they are equal and expect_equal is True.
        """
        from PIL import ImageChops

        obtained_img = self._load_image(obtained_file)
        expected_img = self._load_image(expected_file)

        def check_result(equal, manhattan_distance):
            if equal != expect_equal:
                params = manhattan_distance, expected_file, obtained_file
                if expect_equal:
                    assert 0, (
                        "Difference between images too high: %.2f %%\n%s\n%s" % params
                    )
                else:
                    assert 0, (
                        "Difference between images too small: %.2f %%\n%s\n%s" % params
                    )

        # 1st check: identical
        diff_img = ImageChops.difference(obtained_img, expected_img)

        if diff_img.getbbox() is None:  # Equal
            check_result(True, None)

        manhattan_distance = self._compute_manhattan_distance(diff_img)
        equal = manhattan_distance <= diff_threshold
        check_result(equal, manhattan_distance)

    def check(self, image_data, diff_threshold=0.1, expect_equal=True, basename=None):
        """
        Checks that the given image contents are comparable with the ones stored in the data directory.

        :param bytes image_data: image data
        :param str|None basename: basename to store the information in the data directory. If none, use the name
            of the test function.
        :param bool expect_equal: if the image should considered equal below of the given threshold. If False, the
            image should be considered different at least above the threshold.
        :param float diff_threshold:
            Tolerage as a percentage (1 to 100) on how the images are allowed to differ.

        """
        from PIL import Image

        def dump_fn(target):
            image = Image.open(io.BytesIO(image_data))
            image.save(six.text_type(target), "PNG")

        perform_regression_check(
            datadir=self.datadir,
            original_datadir=self.original_datadir,
            request=self.request,
            check_fn=partial(
                self._check_images_manhattan_distance,
                diff_threshold=diff_threshold,
                expect_equal=expect_equal,
            ),
            dump_fn=dump_fn,
            extension=".png",
            basename=basename,
            force_regen=self.force_regen,
        )
