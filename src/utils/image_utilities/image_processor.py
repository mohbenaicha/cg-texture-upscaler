from utils.image_utilities.interfaces import IImageProcessor
from utils.image_utilities import (
    determine_if_alpha_is_0,
    sRGB_to_linear,
    apply_gamma_correction,
    convert_datatype,
)
from utils.logger import write_log_to_file
from copy import deepcopy
import cv2
import numpy as np


class ImageProcessor(IImageProcessor):
    def __init__(self, container, gamma_adjustment):
        self.container = container  # orchestrator/container that has image and config
        self.export_config = self.container.config
        self.gamma_adjustment = gamma_adjustment

    def preprocess_image(self):
        self._handle_dimensions()
        self._check_all_values_equivalent()
        self._preprocess_noisy_image()
        self._split_image()
        self._handle_gamma()  # handle_gamma_correction
        self._convert_dtype(input=True)

        # convert_dtype()
        raise NotImplementedError

    def postprocess_image(self):
        # convert_dtpye()
        # handle_write_channel_model()
        # apply_dds_map_fix()
        # handle_noise()
        # handle_channel_order()
        raise NotImplementedError

    def process_image(self):
        # scale_image()
        # calls upscale or downscale based on parent config
        raise NotImplementedError

    def _upscale(self, method):
        # calls resrgan_upscale or linear_upscale based on parent config
        raise NotImplementedError

    def _downscale(self, method):
        # downscales image
        raise NotImplementedError

    def _resrgan_upscale():
        raise NotImplementedError

    def _linear_upscale():
        raise NotImplementedError

    def _handle_dimensions(self) -> None:
        """
        Reshapes an image by adding a single row and/or column of pixel to make
        a multiple of 2.
        """
        shape = list(self.container.image.shape)
        w_mod, h_mod = shape[0] % 2, shape[1] % 2
        if w_mod != 0 or h_mod != 0:
            write_log_to_file(
                "WARNING",
                f"Image {self.export_config.src_image_name} has dimensions {shape[0]}x{shape[1]}. Upscaling this image"
                "Will affect UV mapping.",
            )
            # check if the width and/or height is a multiple of 2
            shape[0] += 1 if w_mod != 0 else 0
            shape[1] += 1 if h_mod != 0 else 0
            write_log_to_file(
                "INFO",
                f"Reshaped image {self.export_config.src_image_name} to dimensions {shape[0]}x{shape[1]} to allow for processing.",
            )
            self.container.image = cv2.resize(
                src=self.container.image,
                dsize=shape[:2],
                interpolation=cv2.INTER_LANCZOS4,
            )

    def _check_all_values_equivalent(self):

        if self.container.image.max() == self.container.image.min():
            write_log_to_file(
                "WARNING",
                f"Using linear scaling to scale image {self.export_config.src_image_name}'s channels.",
            )
            determine_if_alpha_is_0()
            self.container.image = self.upscale_linear(
                self.container.image,
                self.export_config.upscale_factor,
                self.container.image.max(),
                self.export_config.upscale_precision,
            )
            self.export_config.linear_upscale_all_channels = True
            self.export_config.proceed_with_split = False
        else:
            self.export_config.linear_upscale_all_channels = False
            if (
                "A" in self.export_config.mode
            ):  # split channels to process by either the generator or through linear upscaling
                self.export_config.proceed_with_split = True
            else:  # if only rgb or grayscale channels exist, no split is required
                self.export_config.proceed_with_split = True

            # at this point, if noise is added, the noisy image is added before the channels to
            # be upscaled are processed further

    def _preprocess_noisy_image(self) -> None:
        if self.export_config.noise_factor > 0.0:
            self.container.noisy_copy = deepcopy(self.container.image)
            if self.export_config.mode == "RGBA":  # RGB + Alpha
                temp = np.copy(self.container.noisy_copy)[..., :3]
            elif self.export_config.mode == "LA":  # Greyscale + alpha
                temp = np.copy(self.container.noisy_copy)[..., :1]
            else:  # RGB or Greyscale
                temp = np.copy(self.container.noisy_copy)[..., :]

            # concatenate tranformed color channels with alpha channel TODO: is there a better way to avoid repeating the if/else statements
            if self.export_config.mode == "RGBA":
                self.container.noisy_copy = np.concatenate(
                    (temp, self.container.noisy_copy[..., 3:]), axis=2
                )
            elif self.export_config.mode == "LA":
                self.container.noisy_copy = np.concatenate(
                    (temp, self.container.noisy_copy[..., 1:]), axis=2
                )
            else:
                self.container.noisy_copy = temp
            del temp

            self.container.noisy_copy = self.export_config.output_dtype_mapping[
                f"{str(self.container.noisy_copy.dtype)}:{self.export_config.trg_image_dtype if self.export_config.export_format != 'exr' else 'float32'}"
            ](channels=self.container.noisy_copy)

            if "Linear In" in self.export_config.color_space:
                self.container.noisy_copy = self.export_config.output_dtype_mapping[
                    f"{self.container.noisy_copy.dtype}:float32"
                ](channels=self.container.noisy_copy)
                self.container.noisy_copy = np.vectorize(sRGB_to_linear)(
                    self.container.noisy_copy
                ).astype(self.container.noisy_copy.dtype)

            if self.export_config.mode == "L":
                self.container.noisy_copy = np.expand_dims(self.container.noisy_copy, 2)

    def _split_image(self):
        """
        Separates alpha from color channels creating two new members to represent the original image object.
        Also saves the images depth (data type) and removes the original image object from memory.
        """
        (
            self.export_config.upscale_color_with_generator,
            self.export_config.upscale_alpha_with_generator,
        ) = (
            (
                True
                if (
                    self.export_config.upscale_factor in [2, 4, 0.5]
                    and self.export_config.proceed_with_split
                )
                else False
            ),
            False,  # will handle separately
        )
        if self.export_config.proceed_with_split:
            # extract alpha information
            self.container.alpha = (
                self.container.image[:, :, self.export_config.length - 1 :]
                if (
                    "A" in self.export_config.mode
                    and "A" in self.export_config.export_mode
                )
                else None
            )
            self.export_config.upscale_alpha_with_generator = (
                True
                if (
                    type(self.container.alpha) == np.ndarray
                    and "A" in self.export_config.export_mode
                    and self.export_config.upscale_factor in [2, 4, 0.5]
                )
                else False
            )
            if self.export_config.upscale_alpha_with_generator:
                # ensure image channels and elements vary (masks in CG textures can exhibit such qualities)
                alpha_max, alpha_min = (
                    self.container.alpha.max(),
                    self.container.alpha.min(),
                )
                # if the entire alpha channel is a single value, conduct a linear upscale
                if alpha_max == alpha_min:
                    write_log_to_file(
                        "WARNING",
                        f"Using linear scaling to scale image {self.export_config.src_image_name}'s alpha channel.",
                    )
                    self.container.alpha = self.upscale_linear(  # todo
                        self.container.alpha,
                        self.export_config.upscale_factor,
                        alpha_max,
                        self.export_config.upscale_precision,
                    )
                    self.export_config.upscale_alpha_with_generator = False

                else:  # prepare alpha channel to be fed to the Generator
                    self.container.alpha = (
                        np.repeat(self.container.alpha, repeats=3, axis=2)
                        if not self.upscale_factor in [0.5, 1]
                        else self.container.alpha
                    )
            # exctract color information (rgb/grayscale)
            if self.export_config.mode == "RGBA":
                self.container.color_channels = self.container.image[
                    :, :, : self.export_config.length - 1
                ]  # rgb
            elif self.export_config.mode == "RGB":
                self.container.color_channels = self.container.image[:, :, :]  # rgb
            elif self.export_config.mode in ["LA"]:
                self.container.color_channels = self.container.image[
                    :, :, 0:1
                ]  # gray with 3 dimensions
            else:
                self.container.color_channels = np.expand_dims(
                    self.container.image[:, :], 2
                )  # grayscale with 2 dimensions expanded to 3

            # ensure channels image channels and elements vary (masks in CG textures can exhibit such qualities)
            color_max, color_min = (
                self.container.color_channels.max(),
                self.container.color_channels.min(),
            )
            if color_max == color_min:
                write_log_to_file(
                    "WARNING",
                    f"Using linear scaling to scale image {self.export_config.src_image_name}'s color channel(s).",
                )
                self.container.color_channels = self.upscale_linear(
                    self.container.color_channels,
                    self.export_config.upscale_factor,
                    color_max,
                    self.export_config.upscale_precision,
                )
                self.export_config.upscale_color_with_generator = False
            else:
                # the the color channels are to be fed to the generator, ensure the grayscale image
                # is expanded into 3 channels
                if (
                    self.export_config.mode == "L"
                ):  # i.e. either grayscale or grayscale+alpha
                    self.container.color_channels = np.repeat(
                        np.expand_dims(self.container.image, 2), repeats=3, axis=2
                    )
                elif (
                    self.export_config.mode == "LA"
                ):  # i.e. either grayscale or grayscale+alpha
                    self.container.color_channels = np.repeat(
                        self.container.image, repeats=3, axis=2
                    )
        else:
            if not "L" in self.export_config.mode:
                self.container.alpha = None
            self.container.color_channels = self.container.image
            # remove image from memory once channels are separated
        self.container.image = None

    def _handle_gamma(self):
        if self.export_config.upscale_color_with_generator:
            apply_gamma_correction(self.container.color_channels, self.gamma_adjustment)

    def _convert_dtype(self, input: bool = True):
        
        convert_datatype(
            self.container.color_channels,
            self.container.alpha,
            self.container.image,
            self.export_config,
            input=input,
        )
