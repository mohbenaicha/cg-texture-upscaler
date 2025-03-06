from typing import Optional, Dict, List
from app_config.config import *
import cv2


class ImageConfig:
    """A config class for the current image being processed for export. Differs from other config classes which aren't instantiated."""

    def __init__(self, **kwargs):
        self.output_dtype_mapping = DTypeMapping.mapping # reference
        self.img_index: int = kwargs.get("img_index", 0)
        self.src_path: str = kwargs.get("src_path", None)
        self.trg_path: str = kwargs.get("trg_path", None)
        self.single_export_location: str = kwargs.get("single_export_location", None)

        self.src_image_name: Optional[str] = kwargs.get("img_name", None)
        self.src_format: Optional[str] = self.src_image_name[-3:]
        self.color_space: Optional[str] = kwargs.get("color_space", None)
        self.write_color_depth: Optional[str] = kwargs.get("export_color_depth", None)
        self.export_mode: Optional[str] = kwargs.get(
            "export_color_mode", None
        )  # RGB/RGBA/L/LA
        self.export_format: Optional[str] = kwargs.get("export_format", None)
        self.trg_image_dtype: Optional[Dict[str]] = {
            "8": "uint8" if not self.export_format == "exr" else None,
            "16": "uint16" if not self.export_format == "exr" else "float16",
            "32": "float32",
        }[self.write_color_depth]
        self.color_mode: Optional[str] = kwargs.get(
            "color_mode", "true_color"
        )  # true_color, indexed
        self.device: Optional[str] = kwargs.get("device", "cuda")
        self.upscale_factor: int = ConfigReference.scale_map[kwargs.get("scale", None)]
        self.upscale_precision: str = ConfigReference.upscale_precision_levels[
            self.device
        ][kwargs.get("upscale_precision", None)]
        self.compression: Optional[str] = kwargs.get("compression", None)
        self.mipmaps: Optional[str] = kwargs.get("mipmaps", None)
        self.noise_factor: Optional[float] = kwargs.get("noise_level", None)
        self.numbering: Optional[str] = kwargs.get("numbering", None)
        self.prefix: Optional[str] = kwargs.get("prefix", None)
        self.suffix: Optional[str] = kwargs.get("suffix", None)
        self.flag_export_to_original: bool = kwargs.get("export_to_original", False)
        self.opencv_read_args: List[int] = [cv2.IMREAD_UNCHANGED]
        self.write_compression: Optional[str] = kwargs.get(
            "write_compression", None
        )  # automatic
        if self.export_format in ConfigReference.opencv_formats:
            self.handle_opencv_flags()
        self.export_naming: dict["str", "str"] = {
            "export_format": self.export_format,
            "numbering": kwargs.get("numbering", ""),
            "prefix": kwargs.get("prefix", ""),
            "suffix": kwargs.get("suffix", ""),
        }
        self.alpha_0: bool = False
        # attributes to be set later include:
        # self.proceed_with_split, self.linear_upscale_all_channels, self.mode (current mode),

    def handle_opencv_flags(self) -> None:
        if self.export_format == "png":
            self.opencv_write_flgs = [
                cv2.IMWRITE_PNG_COMPRESSION,
                int(ExportConfig.compression),  # compression level (0 to 9)
            ]
        elif self.export_format == "jpg":
            self.opencv_write_flgs = [
                cv2.IMWRITE_JPEG_QUALITY,
                int(ExportConfig.compression),  # image quality (0-100)
            ]
        else:
            self.opencv_write_flgs = [
                cv2.IMWRITE_EXR_COMPRESSION,
                EXR_COMPRESSION_TYPES.__members__[
                    ExportConfig.compression
                ].value,  # compression (nominal)
                cv2.IMWRITE_EXR_TYPE,
                EXR_DEPTH.__members__[
                    {"16": "HALF", "32": "FLOAT"}[ExportConfig.export_color_depth]
                ].value,  # color depth (16, 32 bit floats)
            ]