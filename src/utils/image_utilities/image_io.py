from utils.image_utilities.interfaces import IImageIO
import numpy as np
import cv2, os
from PIL import Image
from typing import Optional, Self
from utils import confref
from utils.logger import write_log_to_file

class ImageIO(IImageIO):
    """Handles reading and writing images."""
    def read_image(parent, src_path: str, img_name: str) -> np.ndarray:
        """Reads an image from disk and returns it as a NumPy array."""
        pass

    def read_and_preprocess_image(parent) -> None:
        src_path = os.path.join(parent.src_path, parent.src_image_name)
        if parent.src_format in confref.opencv_formats:
            parent.image = cv2.imread(src_path, cv2.IMREAD_UNCHANGED)
        else:
            parent.image = Image.open(src_path)
            parent.image = np.array(parent.image)
        # extract datatype for future use
        parent.src_dtype: str = str(parent.image.dtype)
        parent.mode: Optional[str] = parent.get_mode_from_array()
        parent.length = len(parent.mode)
        # handle dimensions
        parent.handle_dimensions(
        )
    
    def write_image(parent, image: np.ndarray, trg_path: str, export_config: dict) -> None:
        """Writes an image to disk based on export configuration."""
        pass

    def handle_dimensions(parent) -> None:
        """
        Reshapes an image by adding a single row and/or column of pixel to make
        a multiple of 2.
        """
        shape = list(parent.image.shape)
        w_mod, h_mod = shape[0] % 2, shape[1] % 2
        if w_mod != 0 or h_mod != 0:
            write_log_to_file(
                "WARNING",
                f"Image {parent.src_image_name} has dimensions {shape[0]}x{shape[1]}. Upscaling this image"
                "Will affect UV mapping.",
            )
            # check if the width and/or height is a multiple of 2
            shape[0] += 1 if w_mod != 0 else 0
            shape[1] += 1 if h_mod != 0 else 0
            write_log_to_file(
                "INFO",
                f"Reshaped image {parent.src_image_name} to dimensions {shape[0]}x{shape[1]} to allow for processing.",
            )
            parent.image = cv2.resize(
                src=parent.image, dsize=shape[:2], interpolation=cv2.INTER_LANCZOS4
            )
        return parent