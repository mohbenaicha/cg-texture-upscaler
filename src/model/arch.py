import sys, os
import torch
from torch import nn as nn
from torch.nn import functional as F
from model.utils import default_init_weights


class DenseBlock(nn.Module):
    """Residual Dense Block.

    Used in RRDB block in ESRGAN.

    Args:
        num_feat (int): Channel number of intermediate features.
        num_grow_ch (int): Channels for each growth.
        res_scale (float): The value by which to scale down the residual layer. Default: 0.2
    """

    def __init__(self, in_channels=64, channels_per_conv=32, res_scale=0.2):
        super().__init__()
        self.res_scale = res_scale
        self.conv_block_1 = nn.Conv2d(in_channels, channels_per_conv, 3, 1, 1)
        self.conv_block_2 = nn.Conv2d(
            in_channels + channels_per_conv, channels_per_conv, 3, 1, 1
        )
        self.conv_block_3 = nn.Conv2d(
            in_channels + 2 * channels_per_conv, channels_per_conv, 3, 1, 1
        )
        self.conv_block_4 = nn.Conv2d(
            in_channels + 3 * channels_per_conv, channels_per_conv, 3, 1, 1
        )
        self.conv_block_5 = nn.Conv2d(
            in_channels + 4 * channels_per_conv, in_channels, 3, 1, 1
        )
        self.conv_list = [
            self.conv_block_1,
            self.conv_block_2,
            self.conv_block_3,
            self.conv_block_4,
            self.conv_block_5,
        ]

        self.act = nn.LeakyReLU(0.2, True)

        # initialization
        default_init_weights(
            [
                self.conv_block_1,
                self.conv_block_2,
                self.conv_block_3,
                self.conv_block_4,
                self.conv_block_5,
            ],
            0.1,
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

    Used in RRDB-Net in Generator.

    Args:
        num_feat (int): Channel number of intermediate features.
        num_grow_ch (int): Channels for each growth.
        res_scale (float): The value by which to scale down the residual layer. Default: 0.2
    """

    def __init__(self, in_channels=64, channels_per_conv=32, res_scale=0.2):
        super().__init__()
        self.res_scale = res_scale
        self.dense_block_1 = DenseBlock(in_channels, channels_per_conv)
        self.dense_block_2 = DenseBlock(in_channels, channels_per_conv)
        self.dense_block_3 = DenseBlock(in_channels, channels_per_conv)
        self.dense_blocks = [self.dense_block_1, self.dense_block_2, self.dense_block_3]

    def forward(self, x):
        residual = x.clone()
        for block in self.dense_blocks:
            x = block(x)

        return x * self.res_scale + residual


class Generator(nn.Module):
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
        self.scale = scale
        num_in_ch = num_in_ch * (4 if self.scale == 2 else 1)

        self.initial_conv = nn.Conv2d(num_in_ch, num_feat, 3, 1, 1)
        self.basic_blocks = nn.Sequential(
            *[
                Basic_Block(in_channels=num_feat, channels_per_conv=num_grow_ch)
                for _ in range(num_block)
            ]
        )
        self.conv_body = nn.Conv2d(num_feat, num_feat, 3, 1, 1)

        # upsample

        self.upsample_2x_1_convblock = nn.Conv2d(num_feat, num_feat, 3, 1, 1)
        self.upsample_2x_2_convblock = nn.Conv2d(num_feat, num_feat, 3, 1, 1)
        self.pen_conv = nn.Conv2d(num_feat, num_feat, 3, 1, 1)
        self.final_conv = nn.Conv2d(num_feat, num_out_ch, 3, 1, 1)

        self.act = nn.LeakyReLU(negative_slope=0.2, inplace=True)

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
        x = self.initial_conv(x)
        basic_blocks = self.conv_body(self.basic_blocks(x))
        x = x + basic_blocks
        del basic_blocks
        x = self.act(
            self.upsample_2x_1_convblock(
                F.interpolate(x, scale_factor=2, mode="nearest")
            )
        )
        x = self.act(
            self.upsample_2x_2_convblock(
                F.interpolate(x, scale_factor=2, mode="nearest")
            )
        )
        x = self.final_conv(self.act(self.pen_conv(x)))
        # print(f"::: post final conv:::{torch.cuda.memory_reserved()/1024**3}")

        # mem_alloc_after = torch.cuda.memory_allocated()/1024**3
        # mem_res_after = torch.cuda.memory_reserved()/1024**3

        # print("::: mem_alloc_after::: : ", mem_alloc_after)
        # print("::: mem_res_after::: : ", mem_res_after)
        return x
