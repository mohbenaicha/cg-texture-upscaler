from typing import TYPE_CHECKING, Union
import numpy as np

if TYPE_CHECKING:
    from utils.image_utilities.orchestrator import ImageContainer
    import torch
from app_config.config import ConfigReference


def determine_if_alpha_is_0(image_conatiner: ImageContainer) -> None:
    # TODO: automatic not working consistently
    if ("A" in image_conatiner.config.mode) and (
        image_conatiner.config.compression == "automatic"
    ):
        max_, min_ = (
            image_conatiner.image.transpose(2, 0, 1)[-1].max(),
            image_conatiner.image.transpose(2, 0, 1)[-1].min(),
        )
        image_conatiner.config.alpha_0 = True if max_ == min_ == 255 else False
    elif not "A" in image_conatiner.config.mode:
        image_conatiner.config.alpha_0 = True


def sRGB_to_linear(
    p: Union[np.float32, np.float16],
) -> Union[np.float16, np.float32, np.float64]:
    """
    Converts a np.array's elements from linear sRGB color space to sRGB color space.
    Transformaion equation based on: https://www.nayuki.io/page/srgb-transform-library
    """
    gamma = 2.4
    if p <= 0.04045:
        p /= 12.92
    else:
        p = ((p + 0.055) / 1.055) ** gamma
    return p


def linear_to_sRGB(
    p: Union[np.float32, np.float16],
) -> Union[np.float16, np.float32, np.float64]:
    """
    Converts a np.array's elements from sRGB color space to linear sRGB color space
    Transformaion equation based on: https://www.nayuki.io/page/srgb-transform-library
    """
    inv_gamma = 1 / 2.4
    if p <= 0.0031308:
        p *= 12.92
    else:
        p = (1.055 * (p**inv_gamma)) - 0.055
    return p


def apply_gamma_correction(image, gamma: float):
    """
    image: color channels that are modified in place
    * perceived value = ( ( pixel value / max value ) ** ( 1 / gamma ) ) * max value
    """
    cc_dtype = image.dtype
    if not gamma == 1.0:
        if cc_dtype == "uint8":
            type_ = "uint8"
            max_value = 255
        elif cc_dtype == "uint16":
            type_ = "uint16"
            max_value = 65535
        elif cc_dtype == "float16":
            type_ = "float16"
            max_value = 1.0
        elif cc_dtype == "float32":
            type_ = "float32"
            max_value = 1.0
        else:
            type_ = "float64"
            max_value = 1.0

        image = ((image / max_value) ** (1 / gamma)) * max_value

        # before color channels are fed to the Generator
        if type(image) == np.ndarray:
            image.astype(ConfigReference.supported_dtypes["array"][type_])
        else:
            # self.color_channels are corrected by the inverse of the gamma
            # after color channels upscaled, they are tensors
            image.to(ConfigReference.supported_dtypes["tensor"][type_])


def normalize_uint(image: np.ndarray, minmax_norm: bool = False) -> None:
    """
    Normalize value in a np.array between 0 and 1 or -1 and 1
    """
    dtype = image.dtype
    if not minmax_norm:
        image /= 255 if dtype == "uint8" else 65535
    else:
        min, max = image.min(), image.max()
        b = 0
        image = (1 - b) * (image - min) / (max - min) - b


def convert_datatype_in(color_channels, alpha_channels, config) -> None:
    """
    Converts uint8/uint16/float32 to float16/float32 types to be process by the generator.
    Also converts color space of input to sRGB the generator is trained on sRGB colors and
    does not linear images well. The it further the color space to linear post-upscale if
    so desired by the user.
    """

    if (
        config.upscale_color_with_generator
    ):  # if color channels weren't upscaled using the linear algorithm
        convert_input_image_dtype(config, color_channels)
    if (
        config.upscale_alpha_with_generator
    ):  # if the alpha channel wasn't upscaled using the linear algorithm
        convert_input_image_dtype(config, alpha_channels)


def convert_datatype_out(full_image, config) -> None:
    full_image = convert_output_image_dtype(config, channels=full_image)


def convert_input_image_dtype(config, channels: np.ndarray) -> torch.Tensor:
    """
    Convert the input image to a level of float precision that is compatible with torch
    types.
    """
    if channels.dtype == np.uint8:
        normalize_uint(channels)
    elif channels.dtype == np.uint16:
        normalize_uint(channels)

    # to reduce method bloat, the color space sRGB-Linear conversion is subsumed under data type conversion
    # as a technical note, no color space conversion is actually happening since sRGB is a standard RGB color
    # space
    if "Linear In" in config.color_space:
        channels = np.vectorize(linear_to_sRGB)(channels)

    channels.astype(config.upscale_precision[0], copy=False)


def convert_output_image_dtype(
    config, channels: np.ndarray, input_dtype: str = None, out_dtype: str = None
) -> np.ndarray:
    """
    Convert (scale) the upscaled image to the proper export datatype as
    indicated in the app_config.ConfigReference class.
    """
    # unlike for the PNG format, the IMWRITE function requires float arrays and exports half or float precision based on the cv2.IMWRITE flag speficier when saving the image
    trg_dtype = (
        config.trg_image_dtype if not config.export_format == "exr" else "float32"
    )

    # see the method above for details
    if "Linear Out" in config.color_space:
        channels = np.vectorize(sRGB_to_linear)(channels)
        input_dtype = channels.dtype

    # the self.output_dtype_mapping dictionary contains lambdas that are called on the channels passed in
    return config.output_dtype_mapping[
        f"{str(channels.dtype if not input_dtype else input_dtype)}:{str(trg_dtype if not out_dtype else out_dtype)}"
    ](channels)
