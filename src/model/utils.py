from typing import Tuple
import math
import numpy as np
import torch
from torch import nn as nn
from torch.nn import functional as F
from torch.nn import init as init
from torch.nn.modules.batchnorm import _BatchNorm


@torch.no_grad()
def default_init_weights(module_list, scale=1, bias_fill=0, **kwargs):
    """Initialize network weights.

    Args:
        module_list (list[nn.Module] | nn.Module): Modules to be initialized.
        scale (float): Scale initialized weights, especially for residual
            blocks. Default: 1.
        bias_fill (float): The value to fill bias. Default: 0
        kwargs (dict): Other arguments for initialization function.
    """
    if not isinstance(module_list, list):
        module_list = [module_list]
    for module in module_list:
        for m in module.modules():
            if isinstance(m, nn.Conv2d):
                init.kaiming_normal_(m.weight, **kwargs)
                m.weight.data *= scale
                if m.bias is not None:
                    m.bias.data.fill_(bias_fill)
            elif isinstance(m, nn.Linear):
                init.kaiming_normal_(m.weight, **kwargs)
                m.weight.data *= scale
                if m.bias is not None:
                    m.bias.data.fill_(bias_fill)
            elif isinstance(m, _BatchNorm):
                init.constant_(m.weight, 1)
                if m.bias is not None:
                    m.bias.data.fill_(bias_fill)


class ResidualBlockNoBN(nn.Module):
    """Residual block without BN
    Args:
        num_feat (int): Channel number of intermediate features.
            Default: 64.
        res_scale (float): The value by which to scale down the residual layer. Default: 0.2
        pytorch_init (bool): If set to True, use pytorch default init,
            otherwise, use default_init_weights. Default: False.
    """

    def __init__(self, num_feat=64, res_scale=1, pytorch_init=False):
        super().__init__()
        self.res_scale = res_scale
        self.conv1 = nn.Conv2d(num_feat, num_feat, 3, 1, 1, bias=True)
        self.conv2 = nn.Conv2d(num_feat, num_feat, 3, 1, 1, bias=True)
        self.relu = nn.ReLU(inplace=True)

        if not pytorch_init:
            default_init_weights([self.conv1, self.conv2], 0.1)

    def forward(self, x):
        """
        Args:
            x (torch.Tensor): the input image tensor

        Returns:
            torch.Tensor: the output image tensor
        """
        identity = x
        out = self.conv2(self.relu(self.conv1(x)))
        return identity + out * self.res_scale


class Upsample(nn.Sequential):
    """Upsample module.
    Args:
        scale (int): Scale factor. Supported scales: 2^2 and 2^3.
        num_feat (int): Channel number of intermediate features.
    """

    def __init__(self, scale, num_feat):
        m = []
        if (scale & (scale - 1)) == 0:  # scale = 2^n
            for _ in range(int(math.log(scale, 2))):
                m.append(nn.Conv2d(num_feat, 4 * num_feat, 3, 1, 1))
                m.append(nn.PixelShuffle(2))
        elif scale == 3:
            m.append(nn.Conv2d(num_feat, 9 * num_feat, 3, 1, 1))
            m.append(nn.PixelShuffle(3))
        else:
            raise ValueError(
                f"scale {scale} is not supported. " "Supported scales: 2x and 4x."
            )
        super(Upsample, self).__init__(*m)


# The following are slightly editted utility functions for dividing an image
# into patching and applying padding for the purposes of training and inference
# in case the images are too large to fit on memory.
# Credits for the following list of functions belong to AI Forever
# https://github.com/ai-forever/Real-ESRGAN/blob/main/RealESRGAN/utils.py


def pad_reflect(image: np.ndarray, pad_size: int) -> np.ndarray:
    imsize = image.shape
    height, width = imsize[:2]
    new_img = np.zeros(
        [height + pad_size * 2, width + pad_size * 2, imsize[2]]
    )  # .astype(np.uint8)
    new_img[pad_size:-pad_size, pad_size:-pad_size, :] = image

    new_img[0:pad_size, pad_size:-pad_size, :] = np.flip(
        image[0:pad_size, :, :], axis=0
    )  # top
    new_img[-pad_size:, pad_size:-pad_size, :] = np.flip(
        image[-pad_size:, :, :], axis=0
    )  # bottom
    new_img[:, 0:pad_size, :] = np.flip(
        new_img[:, pad_size : pad_size * 2, :], axis=1
    )  # left
    new_img[:, -pad_size:, :] = np.flip(
        new_img[:, -pad_size * 2 : -pad_size, :], axis=1
    )  # right

    return new_img


def unpad_image(image: np.ndarray, pad_size: int) -> torch.Tensor:
    return image[pad_size:-pad_size, pad_size:-pad_size, :]


def pad_patch(
    image_patch: np.ndarray, padding_size: int, channel_last: bool = True
) -> np.ndarray:
    """Pads image_patch with with padding_size edge values.
    w: (pad size left, pad size right), h: (pad_size upper, padsize lower), c (0,0) - i.e the same 3 channels maintained
    """

    if channel_last:
        return np.pad(
            image_patch,
            ((padding_size, padding_size), (padding_size, padding_size), (0, 0)),
            "edge",
        )
    else:
        return np.pad(
            image_patch,
            ((0, 0), (padding_size, padding_size), (padding_size, padding_size)),
            "edge",
        )


def unpad_patches(image_patches: torch.Tensor, padding_size: int) -> torch.Tensor:
    """
    For each patch in the tensor (along dim 0) only retain padding_size to -padding_size along the
    height and the width (dim 1 and 2) for each channel (dim 3)
    """
    return image_patches[:, padding_size:-padding_size, padding_size:-padding_size, :]


def split_image_into_overlapping_patches(
    image_array: np.ndarray, patch_size: int, padding_size: int = 2
) -> Tuple[np.ndarray, Tuple[int]]:
    """Splits the image into partially overlapping patches.
    The patches overlap by padding_size pixels.
    Pads the image twice:
        - first to have a size multiple of the patch size,
        - then to have equal padding at the borders.
    Args:
        image_array: numpy array of the input image.
        patch_size: size of the patches from the original image (without padding).
        padding_size: size of the overlapping area.
    """

    xmax, ymax, _ = image_array.shape
    x_remainder = xmax % patch_size
    y_remainder = ymax % patch_size

    # modulo here is to avoid extending of patch_size instead of 0
    x_extend = int((patch_size - x_remainder) % patch_size)
    y_extend = int((patch_size - y_remainder) % patch_size)

    # make sure the image is divisible into regular patches
    extended_image = np.pad(
        array=image_array, pad_width=((0, x_extend), (0, y_extend), (0, 0)), mode="edge"
    )

    # add padding around the image to simplify computations
    padded_image = pad_patch(extended_image, padding_size, channel_last=True)
    xmax, ymax, _ = padded_image.shape
    patches = []

    x_lefts = range(padding_size, xmax - padding_size, patch_size)
    y_tops = range(padding_size, ymax - padding_size, patch_size)

    for x in x_lefts:
        for y in y_tops:
            x_left = x - padding_size
            y_top = y - padding_size
            x_right = x + patch_size + padding_size
            y_bottom = y + patch_size + padding_size
            patch = padded_image[x_left:x_right, y_top:y_bottom, :]
            patches.append(patch)

    return (np.array(patches), padded_image.shape)


def stitch_together(
    patches: torch.Tensor,
    padded_image_shape: Tuple[int],
    target_shape: Tuple[int],
    padding_size: int = 4,
    no_channels: int = 3,
) -> np.ndarray:
    """Reconstruct the image from overlapping patches.
    After scaling, shapes and padding should be scaled too.
    Args:
        patches: patches obtained with split_image_into_overlapping_patches
        padded_image_shape: shape of the padded image contructed in split_image_into_overlapping_patches
        target_shape: shape of the final image
        padding_size: size of the overlapping area.
        no_channels: number of channels in the original image (thus far, the Generator only supports a 3-channel image)
    """

    xmax, ymax, _ = padded_image_shape
    patches = unpad_patches(patches, padding_size)
    patch_size = patches.size()[1]
    n_patches_per_row = ymax // patch_size

    complete_image = torch.zeros((xmax, ymax, no_channels), dtype=patches.dtype)

    row = -1
    col = 0
    for i in range(len(patches)):
        if i % n_patches_per_row == 0:
            row += 1
            col = 0
        complete_image[
            row * patch_size : (row + 1) * patch_size,
            col * patch_size : (col + 1) * patch_size,
            :,
        ] = patches[i]
        col += 1
        
    complete_image=complete_image[padding_size : target_shape[0] + padding_size, padding_size : target_shape[1] + padding_size, :]
    return complete_image
