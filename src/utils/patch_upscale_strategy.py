from abc import ABC, abstractmethod
from typing import Tuple
import math
import numpy as np
import torch
from app_config.config import ConfigReference as confref
from utils import ExportConfig, Image
from model.model import Generator
from model.utils import stitch_together, pad_reflect, split_image_into_overlapping_patches

# from utils.export_utils import Generator, confref, handle_image_split


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
        export_config : dict
            Configuration dictionary for exporting the upscaled image.

        Returns
        -------
        torch.Tensor
            The upscaled image as a tensor.
    """
    @abstractmethod
    def upscale(self, full_image: np.ndarray, channel_type: str, generator: Generator, export_config: dict) -> torch.Tensor:
        pass

class RegularUpscalingStrategy(UpscalingStrategy):
    """
    A strategy for upscaling images using a regular method.

    Methods
    -------
    upscale(full_image: np.ndarray, channel_type: str, generator: Generator, export_config: dict) -> torch.Tensor
        Returns the input image without any modifications.
    """
    def upscale(self, full_image: np.ndarray, channel_type: str, generator: Generator, export_config: dict) -> torch.Tensor:
        return full_image.color_channels if channel_type == "color" else full_image.alpha

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
        export_config : dict
            Configuration dictionary containing export settings such as device and precision levels.
        Returns
        -------
        torch.Tensor
            The upscaled full image as a torch tensor.
    """
    def handle_padding_size(self, size: int) -> int:
        """
        Determines the padding size for image splitting
        based on the user's setting.
        """
        # take the lesser of the dimensions since the padding size is a % that,
        # if dependent on the longer dimension, may exceed the length of the
        # shorter dimension
        pad_size = math.floor(0.03 * min(size[:2]) / 2)
        pad_size = int(pad_size) if pad_size % 2 == 0 else int(pad_size + 1)
        return pad_size

    def handle_image_split(self, channel_type: str = "color", scale: float = 0.5, img: np.ndarray | None = None) -> Tuple[np.ndarray, int]:
        """
        Determines if the image is to be split and processed in patches based on:
            1. the maximum available vram
            2. the split_large_image flag
            3. the padding size
        Returns an array of shape (num of patches, c, h,w)
        """

        global split
        split = False  # flag used for code organization
        if channel_type == "color":
            size: Tuple[int] = img.color_channels.shape
        else:
            size: Tuple[int] = img.alpha.shape
        # 262144 the the pixel count of the image, 0.1835 (GiB)
        # is the video memory required process it. The memory
        # required for other images is:
        # w x h x scale x (vram for 512x512 image) x (pixel count of 512x512 image)
        max_size_to_split = confref.split_sizes[ExportConfig.patch_size][1] #4096*4096 # assuming 10xx + cards have 4.0 GB of available VRAM, a 2048 x 2048 image should fit; further 2x multiples of these dimensions don't
        split = True if size[0]*size[1]*scale*scale > max_size_to_split else False
        if split:
            if channel_type == "color":
                confref.split_color = True
            else:
                confref.split_alpha = True
            if ExportConfig.split_large_image:
                pad_size: int = self.handle_padding_size(size)

                lr_image: np.ndarray = pad_reflect(
                    img.color_channels if channel_type == "color" else img.alpha, pad_size
                )
                min_ = min(lr_image.shape[:2])
                no_patches = 0
                while True:  
                    no_patches += 1
                    patch_size = (min_ / no_patches) + pad_size * 2
                    if (patch_size*scale)**2 <= max_size_to_split:
                        patch_size = math.ceil(min_ / no_patches)
                        break
                patch_size += (1 if not patch_size % 2 == 0 else 0)

                patches, p_shape = split_image_into_overlapping_patches(
                    lr_image, patch_size=patch_size, padding_size=pad_size
                )
               
                return patches, p_shape, pad_size, size
        else:
            return (None,) * 4
        
    def upscale(
            self, 
            img: Image, 
            channel_type: str, 
            generator: Generator,
            export_config: dict, 
            scale: float) -> torch.Tensor:
        
        full_image, p_shape, pad_size, lr_im_shape = self.handle_image_split(channel_type, scale, img)
        new_patches = None
        i = 0

        if type(full_image) == np.ndarray:

            for patch in full_image:
                i += 1
                if i == 1:
                    new_patches = generator(
                        confref.inference_transform(image=patch)["image"]
                        .unsqueeze(0)
                        .to(export_config["device"])
                        .to(
                            dtype=confref.upscale_precision_levels[export_config["device"]][
                                export_config["upscale_precision"]
                            ][1]
                        )
                    ).cpu()
                else:
                    new_patches = torch.cat(
                        (
                            new_patches,
                            generator(
                                confref.inference_transform(image=patch)["image"]
                                .unsqueeze(0)
                                .to(export_config["device"])
                                .to(
                                    dtype=confref.upscale_precision_levels[
                                        export_config["device"]
                                    ][export_config["upscale_precision"]][1]
                                )
                            ).cpu(),
                        ),
                        dim=0,
                    )
            new_patches: torch.Tensor = new_patches.permute((0, 2, 3, 1))
            padded_size_scaled: Tuple[int] = tuple(np.multiply(p_shape[:2], scale)) + (3,)
            scaled_image_shape: Tuple[int] = tuple(np.multiply(lr_im_shape[:2], scale)) + (
                3,
            )

            full_image: torch.Tensor = stitch_together(
                patches=new_patches,
                padded_image_shape=padded_size_scaled,
                target_shape=scaled_image_shape,
                padding_size=pad_size * scale,
            )
      

            del new_patches
            return full_image
        else:
            return img.color_channels if channel_type == "color" else img.alpha
