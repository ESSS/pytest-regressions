import io
import os
from functools import partial
from pathlib import Path
from typing import Any
from typing import Optional

import pytest

from .common import import_error_message
from .common import perform_regression_check


class ImageRegressionFixture:
    """
    Regression test for image objects, accounting for small differences.
    """

    def __init__(
        self, datadir: Path, original_datadir: Path, request: pytest.FixtureRequest
    ) -> None:
        self.request = request
        self.datadir = datadir
        self.original_datadir = original_datadir
        self.force_regen = False
        self.with_test_class_names = False

    def _load_image(self, filename: "os.PathLike[str]") -> Any:
        """
        Reads the image from the given file and convert it to RGB if necessary.
        This is necessary to be used with the ImageChops module operations.
        At this time, in this module, channel operations are only implemented
        for 8-bit images (e.g. "L" and "RGB").
        """
        try:
            from PIL import Image
        except ModuleNotFoundError:
            raise ModuleNotFoundError(import_error_message("Pillow"))

        img = Image.open(str(filename), "r")
        if img.mode not in ("L" or "RGB"):
            return img.convert("RGB")
        else:
            return img

    def _compute_manhattan_distance(self, diff_image: Any) -> float:
        """
        Computes a percentage of similarity of the difference image given.

        :param diff_image:
            An image in RGB mode computed from ImageChops.difference
        """
        try:
            import numpy
        except ModuleNotFoundError:
            raise ModuleNotFoundError(import_error_message("Numpy"))

        number_of_pixels = diff_image.size[0] * diff_image.size[1]
        return float(
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
        self,
        obtained_file: Path,
        expected_file: Path,
        expect_equal: bool,
        diff_threshold: float,
    ) -> None:
        """
        Compare two image by computing the differences spatially, pixel by pixel.

        The Manhattan Distance is used to compute how much two images differ.

        :param obtained_file:
            The image with the obtained image

        :param expected_file:
            The image with the expected image

        :param expect_equal:
            If True, the images are expected to be equal, otherwise, they're expected to be
            different.

        :param diff_threshold:
            The maximum percentage of difference accepted.
            A value between 0.0 and 100.0

        :raises AssertionError:
            raised if they are actually different and expect_equal is False or
            if they are equal and expect_equal is True.
        """
        try:
            from PIL import ImageChops
        except ModuleNotFoundError:
            raise ModuleNotFoundError(import_error_message("Pillow"))

        __tracebackhide__ = True

        obtained_img = self._load_image(obtained_file)
        expected_img = self._load_image(expected_file)

        def check_result(equal: bool, manhattan_distance: Optional[float]) -> None:
            if equal != expect_equal:
                if expect_equal:
                    assert (
                        False
                    ), f"Difference between images too high: {manhattan_distance} %\n{expected_file}\n{obtained_file}"
                else:
                    assert (
                        False
                    ), f"Difference between images too small: {manhattan_distance} %\n{expected_file}\n{obtained_file}"

        # 1st check: identical
        diff_img = ImageChops.difference(obtained_img, expected_img)

        if diff_img.getbbox() is None:  # Equal
            check_result(True, None)

        manhattan_distance = self._compute_manhattan_distance(diff_img)
        equal = manhattan_distance <= diff_threshold
        check_result(equal, manhattan_distance)

    def check(
        self,
        image_data: bytes,
        diff_threshold: float = 0.1,
        expect_equal: bool = True,
        basename: Optional[str] = None,
    ) -> None:
        """
        Checks that the given image contents are comparable with the ones stored in the data directory.

        :param image_data: image data
        :param basename: basename to store the information in the data directory. If none, use the name
            of the test function.
        :param expect_equal: if the image should considered equal below of the given threshold. If False, the
            image should be considered different at least above the threshold.
        :param diff_threshold:
            Tolerance as a percentage (1 to 100) on how the images are allowed to differ.
        """
        __tracebackhide__ = True

        try:
            from PIL import Image
        except ModuleNotFoundError:
            raise ModuleNotFoundError(import_error_message("Pillow"))

        def dump_fn(target: Path) -> None:
            image = Image.open(io.BytesIO(image_data))
            image.save(str(target), "PNG")

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
            with_test_class_names=self.with_test_class_names,
        )
