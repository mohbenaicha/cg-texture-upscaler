from typing import TYPE_CHECKING, Union
import numpy as np
import cv2

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


def convert_input_image_dtype(
    color_space, upscale_precision, channels: np.ndarray
) -> torch.Tensor:
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
    if "Linear In" in color_space:
        channels = np.vectorize(linear_to_sRGB)(channels)

    channels.astype(upscale_precision, copy=False)


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


def convert_RGB_to_grayscale(channels: np.ndarray) -> np.ndarray:
    """
    channels: np.array of shape (channels, height, width)
    Returns a greyscale image of shape (1, height, width)
    """
    return np.expand_dims(cv2.cvtColor(channels, cv2.COLOR_BGR2GRAY), 2)


def add_alpha(trg_image_dtype: str, channels: np.ndarray, opacity: float):
    """
    returns a np.array of shape (channels.shape[0] + 1, height, width) 
    i.e. with the alpha channel appended to the input channels using the same dtype
    """
    alpha = np.ones(channels.shape[:2], dtype=channels.dtype)
    dtype = (
        (255 if trg_image_dtype == "uint8" else 65535)
        if not "float" in trg_image_dtype
        else 1
    )
    alpha = np.expand_dims(alpha, 2) * opacity * dtype
    return np.concatenate(
        (channels, alpha),
        axis=2,
    ).astype(channels.dtype)


def process_output_color_mode(channels: np.ndarray, export_color_mode: str) -> np.ndarray:
    """
    channels: np.array of shaep (channels, height, width)
    export_color_mode: str of the form "RGB", "RGBA", "L", "LA"
    """
    no_channels = channels.shape[2]

    if no_channels == 1:  # grey
        if "L" not in export_color_mode:  # write as RGB
            channels = np.repeat(channels, 3, axis=2)
    elif no_channels == 2:  # grey + alpha
        if "L" in export_color_mode:  # write in greyscale
            channels = channels[..., :1]
        else:  # write in RGB
            temp = np.repeat(channels[:, :, 0:1], 3, axis=2)
            channels = temp if "A" not in export_color_mode else np.concatenate((temp, channels[:, :, 1:2]), axis=2)
    elif no_channels == 3:  # RGB
        if "L" in export_color_mode:  # write in greyscale
            channels = convert_RGB_to_grayscale(channels)
    elif no_channels == 4:  # RGBA
        if "L" in export_color_mode:  # write in greyscale
            channels = convert_RGB_to_grayscale(channels[..., :3])
            if "A" in export_color_mode:
                channels = np.concatenate((channels, channels[..., 3:]), axis=2)
        else:  # write in RGB
            channels = channels[..., :3] if "A" not in export_color_mode else channels

    if "A" in export_color_mode and no_channels != 4:
        channels = add_alpha(channels=channels, opacity=1.0)

    return channels


def unsharp_mask(
    image: np.ndarray,
    kernel_size: tuple = (5, 5),
    sigma: float = 1.0,
    amount: float = 1.0,  #
    threshold: float = 0,  # 0 to 1
    input_dtype: str = "uint8",
):
    """
    Return a sharpened version of the image, using an unsharp mask.
    This is a modified version of Soroush (2019) that incorporates various color depth adjustments and condenses some operations .
    Comments have been added for clarification of the steps.
    Credit: Soroush (2019). https://stackoverflow.com/questions/4993082/how-can-i-sharpen-an-image-in-opencv.
    """
    scale_ = {
        "uint8": 255,
        "uint16": 65535,
        "float16": 1.0,
        "float32": 1.0,
        "float64": 1.0,
    }
    blurred = cv2.GaussianBlur(image, kernel_size, sigma)
    sharpened = (
        float(amount + 1) * image - float(amount) * blurred
    )  # combine a ratio of the original image and blurred image; the blurry image is generated using a guassian distribution
    sharpened = np.clip(sharpened, 0, scale_[input_dtype])

    sharpened = sharpened.astype(input_dtype)
    if threshold > 0:
        # don't sharpen pixel values less than the threshold
        low_contrast_mask = (
            np.absolute(image - blurred) < threshold * scale_[input_dtype]
        )  # yields array of true/false values
        np.copyto(
            sharpened, image, where=low_contrast_mask
        )  # restore the original pixel values where the threshold holds
    return sharpened

def downscale_image(image: np.ndarray):
    orig_dtype = image.dtype
    image = cv2.resize(
        src=image.astype("float32" if orig_dtype == "float16" else orig_dtype),
        dsize=tuple(int(dim / 2) for dim in image.shape[:2][::-1]),
        interpolation=cv2.INTER_LANCZOS4,
    )
    if len(image.shape) == 2:
        image = np.expand_dims(image, 2)