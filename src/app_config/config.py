from typing import List, Dict, Tuple, Union, Callable
from enum import Enum
import numpy as np
import torch
import albumentations as A
from albumentations.pytorch import ToTensorV2


class GUIScale(Enum):
    small: int = 1
    medium: int = 2
    large: int = 3


class GUITheme(Enum):
    light: int = 1
    dark: int = 2
    contrast: int = 3


class EXR_COMPRESSION_TYPES(Enum):
    NO: int = 0
    RLE: int = 1
    ZIPS: int = 2
    ZIP: int = 3
    PIZ: int = 4
    PXR24: int = 5
    B44: int = 6
    B44A: int = 7
    DWAA: int = 8
    DWAB: int = 9


class EXR_DEPTH(Enum):
    HALF: int = 1
    FLOAT: int = 2


class ConfigReference:
    has_alpha: bool = False
    split_color: bool = False  # basic reference for patch upscalin to refer to
    split_alpha: bool = False
    available_devices: List[str] = ["cpu"] + (
        ["cuda"] if torch.cuda.is_available() else []
    )
    available_scales: List[str] = ["none", "0.5x", "2x", "4x"]
    scale_map: Dict[str, Union[int, float]] = {"0.5x": 0.5, "none": 1, "2x": 2, "4x": 4}
    mipmap_levels: List[str] = ["max", "75%", "50%", "25%", "none"]
    available_export_formats: List[str] = ["tga", "dds", "bmp", "exr", "png", "jpg"]
    limit_vram_value = 1.0
    supports_mipmaps: Dict[str, bool] = {
        "dds": True,
        "tga": False,
        "png": False,
        "jpg": False,
        "bmp": False,
        "exr": False,
    }
    supported_color_spaces: List[str] = [
        "Linear In/ Linear Out",
        "sRGB In/ sRGB Out",
        "sRGB In/ Linear Out",
        "Linear In/ sRGB Out",
    ]
    # all image formats technically have discrete but the
    # ordinal nature of jpg/png compression classifies them as a range
    compression_option: Dict[str, Tuple[str]] = {
        "discrete": ("bmp", "dds", "tga", "exr"),
        "range": ("png", "jpg"),
    }
    discrete_compression_map: Dict[str, Tuple[str]] = {
        "bmp": ("none", "rle"),
        "dds": ("automatic", "none", "dxt1", "dxt3", "dxt5"),
        "tga": ("none", "rle"),
        "exr": tuple(EXR_COMPRESSION_TYPES.__members__.keys()),
    }
    range_compression_map: Dict[str, Dict[str, Union[Tuple[int], int]]] = {
        "png": {"range": (0, 9), "step": 1},
        "jpg": {"range": (0, 100), "step": 1},
    }
    format_to_channel_map: Dict[str, str] = {
        "png": ("RGBA", "RGB", "L"),
        "jpg": ("RGB", "L"),
        "bmp": ("RGBA", "RGB", "L"),
        "dds": ("RGBA", "RGB"),
        "tga": ("RGBA", "RGB"),
        "exr": ("RGBA", "RGB", "L"),
    }
    supported_color_depth: List[str] = ["8", "16", "32"]  # bits per channel
    export_color_depth: Dict[str, Tuple[str]] = {
        "png": ("8", "16"),
        "jpg": ("8",),
        "bmp": ("8",),
        "dds": ("8",),
        "tga": ("8",),
        "exr": ("16", "32"),
    }
    upscale_precision_levels: Dict[str, Tuple[type, torch.dtype]] = {
        "cuda": {
            "normal": (np.float16, torch.float16),
            "high": (np.float32, torch.float32),
        },
        "cpu": {
            "normal": (np.float16, torch.bfloat16),
            "high": (np.float32, torch.float32),
        },
    }
    # palette based images are not naitvely intended by most image formats, only bmp with rle compression
    color_modes: List[str] = [
        "RGB",
        "RGBA",
        "Greyscale",
        "Greyscale+Alpha",
    ]
    opencv_formats: List[str] = ["png", "jpg", "exr"]
    read_lib_map: Dict[str, str] = {
        "png": "opencv",
        "jpg": "opencv",
        "exr": "opencv",
        "bmp": "PIL",
        "tga": "PIL",
        "dds": "PIL",
    }
    write_lib_map: Dict[str, str] = {
        "png": "opencv",
        "jpg": "opencv",
        "exr": "opencv",
        "bmp": "wand",
        "tga": "wand",
        "dds": "wand",
    }
    inference_transform: A.Compose = A.Compose(
        [
            ToTensorV2(),
        ]
    )
    supported_dtypes: dict[str, Union[type, torch.dtype]] = {
        "array": {"uint8": np.uint8, "uint16": np.uint16, "float32": np.float32},
        "tensor": {
            "uint8": torch.uint8,
            "bfloat16": torch.bfloat16,  # for cpu autocasting
            "float16": torch.float16,
            "float32": torch.float32,
            "float64": torch.float64,
        },
    }
    truncated_casting: Tuple[str] = (
        # "float64:float32", "float64:float16", "float64:uint16", "float64:uint8",
        "float32:float16",
        "float32:uint16",
        "float32:uint8",
        "uint16:uint8",
    )
    split_sizes: dict[str,Tuple[str, int]] = {
        "1": ("small", 1024*1024),
        "2": ("medium", 2048*2048),
        "3": ("large", 4096*4096),
        "4": ("extra large", 8192*8192)
    }


class SearchConfig:
    file_or_folder: str = "file"
    last_used_dir_or_file: str = ""
    recursive: bool = False
    illegal_search_characters: set = set('*:?<>"|/\\')
    legal_filter_by_dimension_characters: set = set("1234567890<>=!,")
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
    last_not_filters: Union[List[str], None] = [""] * 4
    num_and_filters: int = 4
    num_or_filters: int = 4
    num_not_filters: int = 4
    go_to_file_name: Union[str, None] = ""
    copy_location: Union[str, None] = ""
    dimension_filter_string: str = "2,2,>="
    dimension_filter_operator_map: dict[str, Callable] = {
        "==": lambda a, b: (a[0] == b[0]) and (a[1] == b[1]),
        ">=": lambda a, b: (a[0] >= b[0]) and (a[1] >= b[1]),
        "<=": lambda a, b: (a[0] <= b[0]) and (a[1] <= b[1]),
        ">": lambda a, b: (a[0] > b[0]) and (a[1] > b[1]),
        "<": lambda a, b: (a[0] < b[0]) and (a[1] < b[1]),
        "!=": lambda a, b: (a[0] != b[0]) and (a[1] != b[1])
    }


class ExportConfig:
    device: str = ConfigReference.available_devices[0]
    scale: str = ConfigReference.available_scales[0]
    export_format: str = "tga"
    compression: str = "none"
    active_compression: Tuple[
        Union[str, None]
    ] = ConfigReference.discrete_compression_map[export_format]
    mipmaps: str = "none"
    save_numbering: bool = False
    save_prefix: str = ""
    save_suffix: str = ""
    single_export_location: Union[str, None] = ""
    save_in_existing_location: bool = False
    weight_file: Union[str, None] = "saved_models"
    noise_level: float = 0.5
    upscale_precision: str = "normal"
    export_color_mode: str = ConfigReference.color_modes[0]
    color_space: str = ConfigReference.supported_color_spaces[0]
    export_color_depth: int = ConfigReference.export_color_depth[export_format][0]
    gamma_adjustment: float = 1.0
    # TODO: implement
    split_large_image: bool = True
    patch_size: str = "3"


class GUIConfig:
    master_default_width: int = 765
    master_default_height: int = 1070
    tab_view_height: int = 1062
    tab_view_width: int = 1  # overidden by column frames
    main_listbox_height: int = 35
    main_listbox_width: int = 60
    labels_fontsize: int = 16
    header_labels_fontsize: int = 20
    option_fontsize: int = 16
    smaller_option_fontsize: int = 12
    textbox_items_fontsize: int = 14
    main_listbox_items_fontsize = 11
    listbox_items_fontsize: int = 18
    export_button_fontsize: int = 22
    button_fontsize: int = 16
    small_button_fontsize: int = 14
    tooltip_hover_delay: float = 200
    tooltip_color: str = "#2E2E2E"
    tooltop_text_color: str = "#CDCDC0"
    lb_cleared: bool = False
    lb_populated_once: bool = False
    browser_mode_on: bool = True
    weight_file: str = ""
    user_config_file_name: str = ""
    dark_theme_color: str = "#2E2E2E"
    light_theme_color: str = "#E3E3E3"
    current_theme: str = "dark"
    rel_config_path: str = "./user_config/"
    rel_log_path: str = "./logs/"


class TechnicalConfig:
    gui_version: str = "0.0.6"
    cli_version: str = "0.0.5"
    app_display_name: str = "CG Texture Upscaler and Utility" 
    app_cli_name: str = "CG Texture Upscaler and Utility"#"CG Texture Upscaler CLI"
    app_author: str = "Mohamed Benaicha" 
