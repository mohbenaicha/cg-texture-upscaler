from abc import ABC, abstractmethod
from typing import Tuple, TYPE_CHECKING
from PIL import Image
import math
import numpy as np
import torch
from app_config.config import ConfigReference, ExportConfig
from model.utils import (
    stitch_together,
    pad_reflect,
    split_image_into_overlapping_patches,
    handle_padding_size,
)

if TYPE_CHECKING:
    from model.model import Generator


class UpscalingStrategy(ABC):
    """
    Abstract base class for defining an upscaling strategy.

    Methods
    -------
    upscale(full_image: np.ndarray, channel_type: str, generator: Generator, export_config: dict) -> torch.Tensor
        Abstract method to upscale an image.

        Parameters
        ----------
        full_image : np.ndarray
            The full image to be upscaled.
        channel_type : str
            The type of channels to be used for upscaling.
        generator : Generator
            The generator instance to be used for upscaling.
        Returns
        -------
        torch.Tensor
            The upscaled image as a tensor.
    """

    @abstractmethod
    def upscale(
        self,
        full_image: np.ndarray,
        channel_type: str,
        generator: "Generator",
    ) -> torch.Tensor:
        pass


class RegularUpscalingStrategy(UpscalingStrategy):
    """
    A strategy for upscaling images using a regular method.

    Methods
    -------
    upscale(full_image: np.ndarray, channel_type: str, generator: Generator, export_config: dict) -> torch.Tensor
        Returns the input image without any modifications.
    """

    def __init__(self, container, export_config):
        ConfigReference.split_alpha = ConfigReference.split_color = False

    def upscale(
        self,
        container: np.ndarray,
        channel_type: str,
        generator: "Generator",
    ) -> np.ndarray:
        return container.color_channels if channel_type == "color" else container.alpha


class PatchUpscalingStrategy(UpscalingStrategy):
    """
    A class to handle the upscaling of image patches using a specified generator model.
    Methods
    -------
    upscale(full_image: np.ndarray, channel_type: str, generator: Generator, export_config: dict) -> torch.Tensor
        Upscales the provided full image by splitting it into patches, processing each patch with the generator,
        and then stitching the patches back together.
        Parameters
        ----------
        full_image : np.ndarray
            The full image to be upscaled, represented as a numpy array.
        channel_type : str
            The type of channels in the image, e.g., "color" or "alpha".
        generator : Generator
            The generator instance used to upscale the image patches.
        Returns
        -------
        torch.Tensor
            The upscaled full image as a torch tensor.
    """

    def __init__(self, container, export_config):
        self.container = container
        self.config = export_config

        if self.config.upscale_color_with_generator:
            self._determine_image_split("color")
        
        if self.config.upscale_alpha_with_generator:
            self._determine_image_split("alpha")

    def _determine_image_split(self, channel_type: str) -> None:
        self.split = False  # flag used for code organization
        if channel_type == "color":
            self.size: Tuple[int] = self.container.color_channels.shape
        elif channel_type == "alpha":
            self.size: Tuple[int] = self.container.alpha.shape
        # 262144 the the pixel count of the image, 0.1835 (GiB)
        # is the video memory required process it. The memory
        # required for other images is:
        # w x h x scale x (vram for 512x512 image) x (pixel count of 512x512 image)

        self.max_size_to_split = ConfigReference.split_sizes[ExportConfig.patch_size][
            1
        ]  # 4096*4096 # assuming 10xx + cards have 4.0 GB of available VRAM, a 2048 x 2048 image should fit; further 2x multiples of these dimensions don't
        self.split = (
            True
            if self.size[0]
            * self.size[1]
            * self.config.upscale_factor
            * self.config.upscale_factor
            > self.max_size_to_split
            else False
        )
        if self.split:
            if channel_type == "color":
                ConfigReference.split_color = True
            elif channel_type == "alpha":
                ConfigReference.split_alpha = True

    def _handle_image_split(
        self,
        scale: float = 0.5,
        img: np.ndarray | None = None,
    ) -> Tuple[np.ndarray, int]:
        """
        Determines if the image is to be split and processed in patches based on:
            1. the maximum available vram
            2. the split_large_image flag
            3. the padding size
        Returns an array of shape (num of patches, c, h,w)
        """
        if self.split:
            pad_size: int = handle_padding_size(self.size)
            lr_image: np.ndarray = pad_reflect(img, pad_size)
            min_ = min(lr_image.shape[:2])
            no_patches = 0
            while True:
                no_patches += 1
                patch_size = (min_ / no_patches) + pad_size * 2
                if (patch_size * scale) ** 2 <= self.max_size_to_split:
                    patch_size = math.ceil(min_ / no_patches)
                    break
            patch_size += 1 if not patch_size % 2 == 0 else 0
            patches, p_shape = split_image_into_overlapping_patches(
                lr_image, patch_size=patch_size, padding_size=pad_size
            )

            return patches, p_shape, pad_size, self.size
        else:
            return (None,) * 4

    def upscale(
        self,
        img: np.ndarray,
        channel_type: str,
        generator: "Generator",
    ) -> torch.Tensor:

        full_image, p_shape, pad_size, lr_im_shape = self._handle_image_split(
            self.config.upscale_factor, img
        )
        new_patches = None
        i = 0
        if type(full_image) == np.ndarray:
            for patch in full_image:
                i += 1
                if i == 1:
                    new_patches = generator(
                        ConfigReference.inference_transform(image=patch)["image"]
                        .unsqueeze(0)
                        .to(self.config.device)
                        .to(dtype=self.config.upscale_precision[1])
                    ).cpu()
                else:
                    new_patches = torch.cat(
                        (
                            new_patches,
                            generator(
                                ConfigReference.inference_transform(image=patch)[
                                    "image"
                                ]
                                .unsqueeze(0)
                                .to(self.config.device)
                                .to(dtype=self.config.upscale_precision[1])
                            ).cpu(),
                        ),
                        dim=0,
                    )

            new_patches: torch.Tensor = new_patches.permute((0, 2, 3, 1))
            padded_size_scaled: Tuple[int] = tuple(
                np.multiply(p_shape[:2], self.config.upscale_factor)
            ) + (3,)
            scaled_image_shape: Tuple[int] = tuple(
                np.multiply(lr_im_shape[:2], self.config.upscale_factor)
            ) + (3,)
            full_image: torch.Tensor = stitch_together(
                patches=new_patches,
                padded_image_shape=padded_size_scaled,
                target_shape=scaled_image_shape,
                padding_size=pad_size * self.config.upscale_factor,
            )

            del new_patches
            return full_image
        else:
            return img.color_channels if channel_type == "color" else img.alpha
