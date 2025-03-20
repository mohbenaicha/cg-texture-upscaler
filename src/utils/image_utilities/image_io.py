import numpy as np
import cv2, os, math
from PIL import Image
from utils.image_utilities.interfaces import IImageIO
from utils.logger import write_log_to_file, log_to_interface
from app_config.config import *
from wand.image import Image as wand_image
from utils.image_utilities.utils import determine_if_alpha_is_0

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from utils.image_utilities.orchestrator import ImageContainer


class ImageIO(IImageIO):
    """Handles reading and writing images."""

    def __init__(self, container: 'ImageContainer'):
        self.container = container

    def read_image(self, src_path: str, img_name: str) -> None:
        self.container.step.update_step("attempting to read image.")
        src_path = os.path.join(src_path, img_name)
        if self.container.config.src_format in ConfigReference.opencv_formats:
            self.container.image = cv2.imread(src_path, cv2.IMREAD_UNCHANGED)
        else:
            self.container.image = Image.open(src_path)
            self.container.image = np.array(self.container.image)

        # extract datatype for future use
        self.container.config.src_dtype = str(self.container.image.dtype)
        self.container.config.mode = self._get_mode_from_array()
        self.container.config.length = len(self.container.config.mode)

    def write_image(self) -> None:
        im_name = self.container.config.src_image_name
        
        self.container.step.update_step("attempting to save image.")
        log_to_interface(self.container.master_frame, f"\n[INFO] Saving {im_name}", ExportConfig.cli_verbosity)
        
        im_name = self._handle_naming(
            im_name,
            self.container.config.img_index,
        )

        if self.container.config.flag_export_to_original:
            save_path = os.path.join(self.container.config.trg_path, im_name)
        else:
            save_path = os.path.join(self.container.config.single_export_location, im_name)

        if self.container.config.export_format in ConfigReference.opencv_formats:
            self._write_opencv_image(save_path)
        else:
            self._write_wand_image(save_path, im_name)
        write_log_to_file("INFO", f"Saved {im_name} to {save_path}")
        log_to_interface(self.container.master_frame, f"\n[INFO] Saved {im_name} to {save_path}\n", ExportConfig.cli_verbosity)
       

    def _write_wand_image(self, save_path, im_name: str) -> None:
        """
        Writes an image using Wand's Image object. Handles compression and color mode.
        Depends on Image Magick to be installed on user's system.
        """
        determine_if_alpha_is_0(self.container)
        with wand_image.from_array(self.container.image) as img:
            img.format = self.container.config.export_format

            # .dds automatic vs general manual compression setting
            if self.container.config.compression == "automatic":
                if self.container.config.alpha_0:
                    img.compression = "dxt1"
                else:
                    img.compression = "dxt5"
            else:
                img.compression = (
                    self.container.config.compression
                    if not self.container.config.compression == "none"
                    else "no"
                )
            # bmp specific information TODO: add warning about color mode being changed
            if (
                self.container.config.export_format == "bmp"
                and self.container.config.compression == "rle"
            ):
                img.type = "palette"
                write_log_to_file(
                    "WARNING",
                    f"{im_name} saved under {save_path} is converted to paletted color mode"
                    "to export using rle compression. True color has been indexed to 256 colors."
                    "To avoid this behaviour in the future, set bmp compression to none.",
                )
            # the other color types pertain to grayscale/true color
            elif self.container.config.export_format != "dds":
                if self.container.config.export_mode == "L":
                    img.type = "grayscale"
                # elif self.export_mode == 'LA':
                #     img.type = "grayscalealpha"
                elif self.container.config.export_mode == "RGB":
                    img.type = "truecolor"
                elif self.container.config.export_mode == "RGBA":
                    img.type = "truecoloralpha"

            if self.container.config.mipmaps:
                self._handle_mipmaps(self.container.config.mipmaps, img)

            img.save(filename=save_path)

    def _get_mode_from_array(self) -> None:
        """
        Determines image channel mode from the length of a np.array object using a naive yet practical approach.
        """
        shape = self.container.image.shape
        if len(shape) == 2:
            return "L"
        else:
            if shape[2] == 4:
                return "RGBA"
            elif shape[2] == 3:
                return "RGB"
            elif shape[2] == 2:
                return "LA"
            else:
                return None

    def _write_opencv_image(self, save_path: str) -> None:
        """
        Writes an image using OpenCV's imwrite function.
        """
        cv2.imwrite(filename=save_path, img=self.image, params=self.opencv_write_flgs)

    def _handle_mipmaps(self, mipmaps: str, img):
        """
        img: a wand image object
        """
        if not mipmaps == "none":
            num_mipmaps = self._calc_mipmaps(mipmaps, img)
            img.options["dds:mipmaps"] = num_mipmaps
        else:
            img.options["dds:mipmaps"] = "0"

    def _calc_mipmaps(self, user_choice: str, image: Image):
        """
        Calculates the maximum possible mip levels for an image
        given its dimensions then sets the level to the lesser of
        (1) the user's choice or (2) the maximum level
        """
        if user_choice == "max":
            user_choice = float(1)
        else:
            user_choice = float(user_choice[:-1]) / 100
        limiting_dim = math.log2(min(image.size))
        return str(round(user_choice * limiting_dim, 0))

    def _handle_naming(self, im_name, index):
        config = self.container.config
        id = f"{index}_" if config.numbering else ""
        prefix = f"{config.prefix}_" if config.prefix else ""
        suffix = f"_{config.suffix}" if config.suffix else ""
        format = config.export_format
        im_name = f"{id}{prefix}{im_name[:-4]}{suffix}.{format}"
        return im_name
