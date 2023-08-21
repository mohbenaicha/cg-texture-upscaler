import torch
from torch import nn as nn
from torch.nn import functional as F

from .arch_utils import default_init_weights  # , pixel_unshuffle #make_layer,


class DenseBlock(nn.Module):
    """Residual Dense Block.

    Used in RRDB block in ESRGAN.

    Args:
        num_feat (int): Channel number of intermediate features.
        num_grow_ch (int): Channels for each growth.
    """

    def __init__(self, in_channels=64, channels_per_conv=32, res_scale=0.2):
        super().__init__()
        self.res_scale = res_scale
        self.conv1 = nn.Conv2d(in_channels, channels_per_conv, 3, 1, 1)
        self.conv2 = nn.Conv2d(
            in_channels + channels_per_conv, channels_per_conv, 3, 1, 1
        )
        self.conv3 = nn.Conv2d(
            in_channels + 2 * channels_per_conv, channels_per_conv, 3, 1, 1
        )
        self.conv4 = nn.Conv2d(
            in_channels + 3 * channels_per_conv, channels_per_conv, 3, 1, 1
        )
        self.conv5 = nn.Conv2d(
            in_channels + 4 * channels_per_conv, in_channels, 3, 1, 1
        )
        self.conv_list = [self.conv1, self.conv2, self.conv3, self.conv4, self.conv5]

        self.act = nn.LeakyReLU(0.2, True)

        # initialization
        default_init_weights(
            [self.conv1, self.conv2, self.conv3, self.conv4, self.conv5], 0.1
        )

    def forward(self, x):
        outs = [x]
        for i, layer in enumerate(self.conv_list):
            i += 1
            outs.append(
                self.act(layer(outs[i - 1]) if i == 1 else layer(torch.cat(outs, 1)))
            ) if i != 5 else outs.append(layer(torch.cat(outs, 1)))
        return outs[-1] * self.res_scale + outs[0]


class Basic_Block(nn.Module):
    """Residual in Residual Dense Block.

    Used in RRDB-Net in ESRGAN.

    Args:
        num_feat (int): Channel number of intermediate features.
        num_grow_ch (int): Channels for each growth.
    """

    def __init__(self, in_channels=64, channels_per_conv=32, res_scale=0.2):
        super().__init__()
        self.res_scale = res_scale
        self.rdb1 = DenseBlock(in_channels, channels_per_conv)
        self.rdb2 = DenseBlock(in_channels, channels_per_conv)
        self.rdb3 = DenseBlock(in_channels, channels_per_conv)
        self.dense_blocks = [self.rdb1, self.rdb2, self.rdb3]

    def forward(self, x):
        residual = x.clone()
        for block in self.dense_blocks:
            x = block(x)

        return x * self.res_scale + residual


class GeneratorALT(nn.Module):
    """Networks consisting of Residual in Residual Dense Block, which is used
    in ESRGAN.

    ESRGAN: Enhanced Super-Resolution Generative Adversarial Networks.

    We extend ESRGAN for scale x2 and scale x1.
    Note: This is one option for scale 1, scale 2 in RRDBNet.
    We first employ the pixel-unshuffle (an inverse operation of pixelshuffle to reduce the spatial size
    and enlarge the channel size before feeding inputs into the main ESRGAN architecture.

    Args:
        num_in_ch (int): Channel number of inputs.
        num_out_ch (int): Channel number of outputs.
        scale (int): The scale by which to upscale the image tensor. Default: 4
        num_feat (int): Channel number of intermediate features.
            Default: 64
        num_block (int): Block number in the trunk network. Defaults: 23
        num_grow_ch (int): Channels for each growth. Default: 32.
    """

    def __init__(
        self, num_in_ch, num_out_ch, scale=4, num_feat=64, num_block=23, num_grow_ch=32
    ):
        super().__init__()
        self.scale: int = scale
        num_in_ch: int = num_in_ch * (4 if self.scale == 2 else 1)

        self.conv_first = nn.Conv2d(num_in_ch, num_feat, 3, 1, 1)
        self.body = nn.Sequential(
            *[
                Basic_Block(in_channels=num_feat, channels_per_conv=num_grow_ch)
                for _ in range(num_block)
            ]
        )
        self.conv_body = nn.Conv2d(num_feat, num_feat, 3, 1, 1)

        # upsample

        self.conv_up1 = nn.Conv2d(num_feat, num_feat, 3, 1, 1)
        self.conv_up2 = nn.Conv2d(num_feat, num_feat, 3, 1, 1)
        if scale == 8:
            self.conv_up3 = nn.Conv2d(num_feat, num_feat, 3, 1, 1)
        self.conv_hr = nn.Conv2d(num_feat, num_feat, 3, 1, 1)
        self.conv_last = nn.Conv2d(num_feat, num_out_ch, 3, 1, 1)

        self.act = nn.LeakyReLU(negative_slope=0.2, inplace=True)

        # the pixel unshuffle layer will reorganize a tensor to:
        #   reduce the dimensions by the scale factor (i.e. if scale = 2, new dimesions are halved, if scale = 4, dimensions are quartered)
        #   the number of channel will be increased to the existing channels multipled by the scale squared, i.e. if scale = 2, new channels = old channel x 2^2
        if self.scale == 2:
            self.unshuffle = nn.PixelUnshuffle(downscale_factor=2)

    def forward(self, x):
        """
        Args:
            x (torch.Tensor): the input image tensor

        Returns:
            torch.Tensor: the output image tensor
        """

        if self.scale == 2:
            x = self.unshuffle(x)

        x = self.conv_first(x)
        body_feat = self.conv_body(self.body(x))
        x = x + body_feat

        # upsample
        x = self.act(self.conv_up1(F.interpolate(x, scale_factor=2, mode="nearest")))
        x = self.act(self.conv_up2(F.interpolate(x, scale_factor=2, mode="nearest")))
        if self.scale == 8:
            x = self.act(
                self.conv_up3(F.interpolate(x, scale_factor=2, mode="nearest"))
            )
        out = self.conv_last(self.act(self.conv_hr(x)))
        return out
