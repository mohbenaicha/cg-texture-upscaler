from typing import List, Dict, Tuple, Union
import torch
from enum import Enum
import albumentations as A
from albumentations.pytorch import ToTensorV2
from pydantic import BaseModel, validator


class PrePostProcessingConfig:
    has_alpha: bool = False
    available_scales: List[str] = ["none", "2x", "4x"]
    mipmap_levels = ["max", "75%", "50%", "25%", "none"]
    available_export_formats: List[str] = ["tga", "dds", "png", "jpg", "bmp", "exr"]
    supports_mipmaps: Dict[str, bool] = {
        "dds": True,
        "tga": False,
        "png": False,
        "jpg": False,
        "bmp": False,
        "exr": False,
    }
    compression_map: Dict[str, Tuple] = {
        "dds": tuple(("none", "dxt1", "dxt3", "dxt5")),
        "tga": tuple(("none", "rle")),
        "bmp": tuple(("none")),
        "jpg": tuple(("none", "jpeg", "losslessjpeg")),
        "exr": tuple(("none", "pxr24", "rle", "piz", "zip", "zips")),
        "png": tuple(("none",)),
    }
    test_transform: A.Compose = A.Compose(
        [
            A.Normalize(mean=[0, 0, 0], std=[1, 1, 1]),
            ToTensorV2(),
        ]
    )
    # TODO: implement
    denoise_factor_maxmin: Union[Tuple[float, float], None] = None  # opencv types
    sharpness_factor_maxmin: Union[Tuple[float, float], None] = None  # opencv types


class SearchConfig:
    file_or_folder: str = "file"
    last_used_dir_or_file: str = ""
    recursive: bool = False
    illegal_search_characters: set = set('*:?<>"|/\\')
    supported_file_types: Tuple[Tuple[str, str]] = (
        ("DirectDraw Surface", "*.dds"),
        ("TARGA", "*.tga"),
        ("Portable Network Graphics", "*.png"),
        ("Bitmap", "*.bmp"),
        ("JPEG", "*.jpg"),
        ("Extended Dynamic Range", "*.exr"),
    )
    last_and_filters: Union[List[str], None] = [""] * 4
    last_or_filters: Union[List[str], None] = [""] * 4
    num_and_filters: int = 4
    num_or_filters: int = 4
    go_to_file_name: Union[str, None] = ""
    copy_location: Union[str, None] = ""


class ExportConfig:
    available_devices: List[str] = ["cpu"] + (
        ["cuda"] if torch.cuda.is_available() else []
    )
    device: str = available_devices[0]
    scale: int = PrePostProcessingConfig.available_scales[0]
    export_format: str = "tga"
    compression: str = "none"
    active_compression: Tuple[
        Union[str, None]
    ] = PrePostProcessingConfig.compression_map[export_format]
    mipmaps: str = "none"
    save_numbering: bool = False
    save_prefix: str = ""
    save_suffix: str = ""
    single_export_location: Union[str, None] = ""
    save_in_existing_location: bool = False
    # TODO: implement
    weight_file: Union[str, None] = "saved_models"
    noise_level: float = 0.5
    # sharpness_factor: Union[float, None] = None


class GUIScale(Enum):
    small: int = 1
    medium: int = 2
    large: int = 3


class GUITheme(Enum):
    light: int = 1
    dark: int = 2
    contrast: int = 3


class GUIConfig:
    master_default_width: int = 690
    master_default_height: int = 1050
    main_listbox_height: int = 38
    main_listbox_width: int = 60
    labels_fontsize: int = 16
    header_labels_fontsize: int = 20
    option_fontsize: int = 16
    textbox_items_fontsize: int = 14
    main_listbox_items_fontsize = 11
    listbox_items_fontsize: int = 18
    export_button_fontsize: int = 22
    button_fontsize: int = 16
    tooltip_hover_delay: float = 200
    tooltip_color: str = "#2E2E2E"
    tooltop_text_color: str = "#CDCDC0"
    lb_cleared: bool = False
    lb_populated_once: bool = False
    weight_file: str = ""
    user_config_file_name: str = ""
    dark_theme_color: str = "#2E2E2E"
    light_theme_color: str = "#E3E3E3"
    current_theme: str = "dark"
    rel_config_path: str = "./user_config/"
    rel_log_path: str = "./logs/"


