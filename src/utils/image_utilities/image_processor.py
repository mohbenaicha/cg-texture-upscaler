import torch
from copy import deepcopy
import cv2
import numpy as np
from typing import TYPE_CHECKING, Optional
from utils.image_utilities.interfaces import IImageProcessor
from utils.image_utilities.image_upscaler import ImageUpscaler
from utils.image_utilities.utils import (
    determine_if_alpha_is_0,
    sRGB_to_linear,
    apply_gamma_correction,
    convert_input_image_dtype,
    convert_output_image_dtype,
    process_output_color_mode,
    unsharp_mask,
    downscale_image,
    upscale_linear,
)
from utils.logger import write_log_to_file
from app_config.config import ConfigReference
from model.utils import setup_generator, ModelManager

if TYPE_CHECKING:
    from utils.image_utilities.orchestrator import ImageContainer


class ImageProcessor(IImageProcessor):
    def __init__(self, container: "ImageContainer", gamma_adjustment):
        self.container = container  # orchestrator/container that has image and config
        self.config = self.container.config  # reference to the config object
        print("ImageProcessor received config as: ", self.config)
        self.gamma_adjustment = gamma_adjustment

    def preprocess_image(self):
        self._handle_dimensions()
        self._check_all_values_equivalent()
        # self._handle_channel_order()
        self._preprocess_noisy_image()
        self._split_image()
        self._handle_gamma(self.gamma_adjustment)  # handle_gamma_correction
        self._convert_dtype(input=True)

    def postprocess_image(self):
        self._handle_gamma(1 / self.gamma_adjustment)
        self._recombine_channels()
        self._convert_dtype(input=False)
        self._handle_export_channels()
        self._apply_dds_mipmap_fix
        self._handle_noise()
        self._handle_channel_order()

    def process_image(self):
        if self.config.upscale_factor > 1:
            self.container.step.update_step(
                "attempting to upscale the image with the chosen model"
            )
            self._upscale_image()
        elif self.config.upscale_factor < 1:
            self.container.step.update_step(
                "attempting to downscale image using chosen method"
            )
            self._downscale_image()

    def _upscale_image(self, method: str = "resrgan"):
        if method in ["resrgan", "vgg19", "vgg16"]:
            print("Upscale method: ", method)
            if not ModelManager.get_model(method):
                ModelManager.set_model(method, setup_generator(self.config, None)[0])
            self._resrgan_upscale()

        elif method == "linear":
            # no model setup needed for linear scaling
            self._linear_upscale()

    def _downscale_image(self, method: str = "lanczos4"):
        # downscales image
        if method in ["lanczos4", "linear", "cubic", "area", "nearest"]:
            self._handle_downscaling(
                strategy=method
            )

    def _resrgan_upscale(self):
        resrgan_upscaler = ImageUpscaler(
            self.container,
            self.container.master_frame,
            ModelManager.get_model("resrgan"),
        )
        print("RESRGAN setup successfully, dtype: ", type(ModelManager.get_model("resrgan")))

        resrgan_upscaler.scale_image()

    def _linear_upscale():
        raise NotImplementedError

    def _handle_dimensions(self) -> None:
        """
        Reshapes an image by adding a single row and/or column of pixel to make
        a multiple of 2.
        """
        self.container.step.update_step("attempting to reshape image to multiple of 2.")
        shape = list(self.container.image.shape)
        w_mod, h_mod = shape[0] % 2, shape[1] % 2
        if w_mod != 0 or h_mod != 0:
            write_log_to_file(
                "WARNING",
                f"Image {self.config.src_image_name} has dimensions {shape[0]}x{shape[1]}. Upscaling this image"
                "Will affect UV mapping.",
            )
            # check if the width and/or height is a multiple of 2
            shape[0] += 1 if w_mod != 0 else 0
            shape[1] += 1 if h_mod != 0 else 0
            write_log_to_file(
                "INFO",
                f"Reshaped image {self.config.src_image_name} to dimensions {shape[0]}x{shape[1]} to allow for processing.",
            )
            self.container.image = cv2.resize(
                src=self.container.image,
                dsize=shape[:2],
                interpolation=cv2.INTER_LANCZOS4,
            )

    def _check_all_values_equivalent(self):
        self.container.step.update_step("attempting to scale linearly.")

        if self.container.image.max() == self.container.image.min():
            write_log_to_file(
                "WARNING",
                f"Using linear scaling to scale image {self.config.src_image_name}'s channels.",
            )
            determine_if_alpha_is_0(self.container)
            self.container.image = upscale_linear(
                self.container.image,
                self.config.upscale_factor,
                self.container.image.max(),
                self.config.upscale_precision,
            )
            self.container.config.linear_upscale_all_channels = True
            self.container.config.proceed_with_split = False
            
        else:
            self.container.config.linear_upscale_all_channels = False
            if (
                "A" in self.config.mode
            ):  # split channels to process by either the generator or through linear upscaling
                self.container.config.proceed_with_split = True
            else:  # if only rgb or grayscale channels exist, no split is required
                self.container.config.proceed_with_split = True

            # at this point, if noise is added, the noisy image is added before the channels to
            # be upscaled are processed further

    def _preprocess_noisy_image(self) -> None:

        if self.config.noise_factor > 0.0:
            self.container.step.update_step("attempting to preprocess noisy image.")

            self.container.noisy_copy = deepcopy(self.container.image)
            if self.config.mode == "RGBA":  # RGB + Alpha
                temp = np.copy(self.container.noisy_copy)[..., :3]
            elif self.config.mode == "LA":  # Greyscale + alpha
                temp = np.copy(self.container.noisy_copy)[..., :1]
            else:  # RGB or Greyscale
                temp = np.copy(self.container.noisy_copy)[..., :]

            # concatenate tranformed color channels with alpha channel TODO: is there a better way to avoid repeating the if/else statements
            if self.config.mode == "RGBA":
                self.container.noisy_copy = np.concatenate(
                    (temp, self.container.noisy_copy[..., 3:]), axis=2
                )
            elif self.config.mode == "LA":
                self.container.noisy_copy = np.concatenate(
                    (temp, self.container.noisy_copy[..., 1:]), axis=2
                )
            else:
                self.container.noisy_copy = temp
            del temp

            self.container.noisy_copy = self.config.output_dtype_mapping[
                f"{str(self.container.noisy_copy.dtype)}:{self.config.trg_image_dtype if self.config.export_format != 'exr' else 'float32'}"
            ](channels=self.container.noisy_copy)

            if "Linear In" in self.config.color_space:
                self.container.noisy_copy = self.config.output_dtype_mapping[
                    f"{self.container.noisy_copy.dtype}:float32"
                ](channels=self.container.noisy_copy)
                self.container.noisy_copy = np.vectorize(sRGB_to_linear)(
                    self.container.noisy_copy
                ).astype(self.container.noisy_copy.dtype)

            if self.config.mode == "L":
                self.container.noisy_copy = np.expand_dims(self.container.noisy_copy, 2)

    def _split_image(self):
        """
        Separates alpha from color channels creating two new members to represent the original image object.
        Also saves the images depth (data type) and removes the original image object from memory.
        """
        self.container.step.update_step(
            "attempting to split color and alpha channels for separate processing."
        )

        self.alpha_scale_linear, self.color_scale_linear = False, False
        (
            self.container.config.upscale_color_with_generator,
            self.container.config.upscale_alpha_with_generator,
        ) = (
            (
                True
                if (
                    self.config.upscale_factor in [2, 4]
                    and self.config.proceed_with_split
                )
                else False
            ),
            False,  # will handle separately
        )
        if self.config.proceed_with_split:
            # extract alpha information
            self.container.alpha = (
                self.container.image[:, :, self.config.length - 1 :]
                if ("A" in self.config.mode and "A" in self.config.export_mode)
                else None
            )
            self.container.config.upscale_alpha_with_generator = (
                True
                if (
                    type(self.container.alpha) == np.ndarray
                    and "A" in self.config.export_mode
                    and self.config.upscale_factor in [2, 4]
                )
                else False
            )
            if self.config.upscale_alpha_with_generator:
                # ensure image channels and elements vary (masks in CG textures can exhibit such qualities)
                alpha_max, alpha_min = (
                    self.container.alpha.max(),
                    self.container.alpha.min(),
                )
                # if the entire alpha channel is a single value, conduct a linear upscale
                if alpha_max == alpha_min:
                    write_log_to_file(
                        "WARNING",
                        f"Using linear scaling to scale image {self.config.src_image_name}'s alpha channel.",
                    )
                    self.container.alpha = upscale_linear(  # todo
                        self.container.alpha,
                        self.config.upscale_factor,
                        alpha_max,
                        self.config.upscale_precision,
                    )
                    self.container.config.upscale_alpha_with_generator = False
                    self.alpha_scale_linear = True

                else:  # prepare alpha channel to be fed to the Generator
                    self.container.alpha = (
                        np.repeat(self.container.alpha, repeats=3, axis=2)
                        if not self.config.upscale_factor in [0.5, 1]
                        else self.container.alpha
                    )
            # exctract color information (rgb/grayscale)
            if self.config.mode == "RGBA":
                self.container.color_channels = self.container.image[
                    :, :, : self.config.length - 1
                ]  # rgb
            elif self.config.mode == "RGB":
                self.container.color_channels = self.container.image[:, :, :]  # rgb
            elif self.config.mode in ["LA"]:
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
                    f"Using linear scaling to scale image {self.config.src_image_name}'s color channel(s).",
                )
                self.container.color_channels = upscale_linear(
                    self.container.color_channels,
                    self.config.upscale_factor,
                    color_max,
                    self.config.upscale_precision,
                )
                self.container.config.upscale_color_with_generator = False
                self.color_scale_linear = True
            else:
                # the the color channels are to be fed to the generator, ensure the grayscale image
                # is expanded into 3 channels
                if self.config.mode == "L":  # i.e. either grayscale or grayscale+alpha
                    self.container.color_channels = np.repeat(
                        np.expand_dims(self.container.image, 2), repeats=3, axis=2
                    )
                elif (
                    self.config.mode == "LA"
                ):  # i.e. either grayscale or grayscale+alpha
                    self.container.color_channels = np.repeat(
                        self.container.image, repeats=3, axis=2
                    )
        else:
            if not "L" in self.config.mode:
                self.container.alpha = None
            self.container.color_channels = self.container.image
            # remove image from memory once channels are separated
        self.container.image = None

    def _recombine_channels(self):
        """
        Recombines color and alpha channels using a lambda or np.concatente function.
        If an alpha channel exists and is 3 channels (generator output), channels are
        combined into a single channel based on a fixed weighting
        """
        self.container.step.update_step(
            "attempting to recombine color and alpha channels"
        )
        t_alpha, t_color = type(self.container.alpha), type(
            self.container.color_channels
        ) # np.ndarray or torch.Tensor or type(None)

        if not self.config.upscale_factor == 0.5: # downscaling does split channels
            if not t_alpha == type(None):
                if len(self.container.alpha.shape) == 2:
                    self.container.alpha = (
                        np.expand_dims(self.container.alpha, axis=2)
                        if t_alpha == np.ndarray
                        else self.container.alpha.unsqueeze(dim=2)
                    )

            if len(self.container.color_channels.shape) == 2:
                self.container.color_channels = (
                    np.expand_dims(self.container.color_channels, axis=2)
                    if t_color == np.ndarray
                    else self.container.color_channels.unsqueeze(dim=2)
                )

            if self.config.upscale_alpha_with_generator:
                if not type(self.container.alpha) == type(None):
                    alpha_dims = len(self.container.alpha.shape)

                if alpha_dims == 2:
                    self.container.alpha = self.container.alpha.unsqueeze(0)
                if ConfigReference.split_alpha and t_alpha == torch.Tensor:
                    self.container.alpha = self.container.alpha.permute(2, 0, 1)

                self.container.alpha = (
                    self.container.alpha[0] * (0.2989)
                    + self.container.alpha[1] * (0.5870)
                    + self.container.alpha[2] * (0.1140)
                ).unsqueeze(0)

                if ConfigReference.split_alpha and t_alpha == torch.Tensor:
                    self.container.alpha.permute(2, 0, 1)

            else:
                if t_alpha == np.ndarray:

                    temp, self.container.alpha = (
                        np.transpose(self.container.alpha, axes=(2, 0, 1)),
                        None,
                    )

                    self.container.alpha, temp = temp, None

            if self.config.upscale_color_with_generator:

                if ConfigReference.split_color and t_color == torch.Tensor:
                    self.container.color_channels = (
                        self.container.color_channels.permute(2, 0, 1)
                    )
            else:

                if t_color == np.ndarray:
                    temp, self.container.color_channels = (
                        np.transpose(self.container.color_channels, axes=(2, 0, 1)),
                        None,
                    )
                    self.container.color_channels, temp = temp, None

            if t_alpha == torch.Tensor:

                self.container.alpha = (
                    self.container.alpha.detach().cpu()
                    if self.config.device == "cuda"
                    else self.container.alpha.to(dtype=torch.float32)
                )
                self.container.alpha = self.container.alpha.numpy()

            if t_color == torch.Tensor:

                self.container.color_channels = (
                    self.container.color_channels.detach().cpu()
                    if self.config.device == "cuda"
                    else self.container.color_channels.to(dtype=torch.float32)
                )
                self.container.color_channels = self.container.color_channels.numpy()

        if not t_alpha == type(None):
            print("self.container.alpha.shape: ", self.container.alpha.shape)
            print("self.container.color_channels.shape: ", self.container.color_channels.shape)
            self.container.image = np.concatenate(
                (self.container.color_channels, self.container.alpha),
                axis=(0 if self.config.upscale_factor != 0.5 else 2),
            )
        else:
            self.container.image = self.container.color_channels

        temp, self.container.image = (
            (
                self.container.image.transpose(1, 2, 0)
                if self.config.upscale_factor != 0.5
                else self.container.image
            ),
            None,
        )

        self.container.image, temp = temp, None
        self.container.color_channels, self.container.alpha = None, None

    def _handle_gamma(self, gamma: float):
        self.container.step.update_step("attempting to correct gamma.")
        if self.config.upscale_color_with_generator:
            apply_gamma_correction(self.container.color_channels, gamma)

    def _convert_dtype(self, input: bool = True):
        """
        Converts uint8/uint16/float32 to float16/float32 types to be process by the generator.
        """
        if input:
            self.container.step.update_step(
                "converting the data type (color depth) before upscaling."
            )
            self.container.color_channels, self.container.alpha = (
                self._convert_datatype_in(
                    self.container.color_channels,
                    self.container.alpha,
                )
            )
        else:
            self.container.step.update_step(
                "converting the data type (color depth) after upscaling."
            )
            self._convert_datatype_out(self.container.image, self.config)

    def _convert_datatype_in(self, color_channels, alpha_channels) -> None:
        """
        Converts input color space to sRGB the generator is trained on sRGB colors and
        does not linear images well. The it further the color space to linear post-upscale if
        so desired by the user.
        """

        if (
            self.config.upscale_color_with_generator
        ):  # if color channels weren't upscaled using the linear algorithm
            color_channels = convert_input_image_dtype(
                self.config.color_space,
                self.config.upscale_precision[0],
                color_channels,
            )
        if (
            self.config.upscale_alpha_with_generator
        ):  # if the alpha channel wasn't upscaled using the linear algorithm
            alpha_channels = convert_input_image_dtype(
                self.config.color_space,
                self.config.upscale_precision[0],
                alpha_channels,
            )
        return color_channels, alpha_channels

    def _convert_datatype_out(self, full_image, config) -> None:
        self.container.image = convert_output_image_dtype(config, channels=full_image)

    def _handle_export_channels(self):
        self.container.step.update_step("attempting to process export color mode.")

        self.container.image = process_output_color_mode(
            self.container.image, self.config.export_mode
        )

    def _apply_dds_mipmap_fix(self):
        """
        Wand (Image Magick's Python binding) does not handle mipmaps correctly when the alpha channel is all zeros.
        """
        self.container.step.update_step(
            "applying the dds mip level workaround for the .dds image export format."
        )

        if self.config.mipmaps != "none":
            image = self.container.image
            if len(image) == 3:
                self.container.alpha = np.ones_like(
                    self.container.image[0], dtype="uint8"
                )
                write_log_to_file(
                    log_type="Warning",
                    message="Added an alpha channel with a transparency value of 1/255 "
                    "so that mipmaps are written correctly.",
                )
                self.container.image = np.concatenate(
                    (image, self.container.alpha), axis=0
                )
            elif len(image) == 4:
                alpha_channel = image[3]
                alpha_channel[alpha_channel == 0] = 1
                self.container.image = image

    def _handle_noise(self) -> None:


        if (
            self.config.noise_factor != 0.0
            and not self.config.linear_upscale_all_channels
            and self.config.upscale_factor != 0.5
            and self.container.master_frame
        ):
            print("shhhckhkhkh::::Found noise > 0", self.config.noise_factor)
            self.container.step.update_step("attempting to process noisy image.")

            self.container.master_frame.print_export_logs(
                f"Processing noise for: {self.container.config.src_image_name}"
            )
            self.container.step.update_step(
                "attempting to process color mode noisy image."
            )
            self.container.noisy_copy = process_output_color_mode(
                self.container.noisy_copy, self.config.export_mode
            )
            self.container.step.update_step("attempting to create noisy image.")
            self.container.noisy_copy = unsharp_mask(
                image=cv2.resize(
                    src=self.container.noisy_copy,
                    dsize=tuple(
                        int(dim * self.config.upscale_factor)
                        for dim in self.container.noisy_copy.shape[:-1][::-1]
                    ),
                    interpolation=cv2.INTER_LANCZOS4,
                ),
                threshold=0.0,
                amount=15,
                input_dtype=str(self.container.noisy_copy.dtype),
            )
            if len(self.container.noisy_copy.shape) == 2:
                self.container.noisy_copy = np.expand_dims(
                    self.container.noisy_copy, axis=2
                )
            self.container.step.update_step(
                "attempting to process color depth for noisy image."
            )
            self.container.noisy_copy = convert_output_image_dtype(
                self.config,
                self.container.noisy_copy,
                self.container.noisy_copy.dtype,
                self.container.image.dtype,
            )
            # A more sophisticated algorithm can be used to retain only the lightest/darkest patterns in the original texture and add them back as noise to the AI-upscaled texture
            self.container.step.update_step(
                "attempting to combine noisy and upscaled image."
            )
            mask = self.container.noisy_copy < self.container.image * (
                self.config.noise_factor
            )
            np.copyto(self.container.image, self.container.noisy_copy, where=mask)
            self.container.noisy_copy = None

    def _handle_channel_order(self) -> None:
        """
        Expands grayscale images to (W, H, 1) and reverses color channels for opencv format compatibility if necessary.
        """
        # Ensure grayscale images are expanded to (W, H, 1)
        self.container.step.update_step(
            "attempting reverse color channels for image writing."
        )
        # if not isinstance(channels, np.ndarray):
        #     channels = self.container.image
        if len(self.container.image) == 2:
            self.container.image = np.expand_dims(self.container.image, axis=2)

        # Reverse color channels if necessary
        if self.config.length > 2:
            src_frmt_is_opencv = (
                self.config.src_format in ConfigReference.opencv_formats
            )
            dest_frmt_is_opencv = (
                ConfigReference.write_lib_map[self.config.export_format] == "opencv"
            )

            if src_frmt_is_opencv != dest_frmt_is_opencv:  # Only swap if formats differ
                self.container.image[..., :3] = self.container.image[..., 2::-1]  # Swap BGR <-> RGB

    def _handle_downscaling(
        self, strategy: str = "lanczos4"
    ) -> np.ndarray:
        print("downscaling image")
        if not self.container.config.linear_upscale_all_channels:
            if not self.alpha_scale_linear:
                self.container.alpha = downscale_image(self.container.alpha, strategy, self.config.upscale_factor)
            if not self.color_scale_linear:
                self.container.color_channels = downscale_image(self.container.color_channels, strategy, self.config.upscale_factor)
