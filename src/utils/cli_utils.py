from typing import Dict, Union
import os, sys, pprint
from gui.frames import SearchFilterFrame, TkListbox
from app_config.config import (
    ConfigReference as confref,
    SearchConfig as serconf,
    TechnicalConfig as tconf,
    ExportConfig as expconf,
)
from caches.cache import image_paths_cache
from utils.validation_utils import write_log_to_file
import argparse


parser = argparse.ArgumentParser(
    prog=f"{tconf.app_cli_name} {tconf.cli_version}",
    usage="Please refer to the 'Using the CLI' text file for guidance on using this tool.",
)

parser.add_argument(
    "--device",
    type=str,
    choices=confref.available_devices,
    default=confref.available_devices[0],
    required=True,
    help="The device to use for processing. Defaults to CPU. For GPU, use the argument cuda. i.e. --device cuda ",
)

parser.add_argument(
    "--scale",
    type=str,
    choices=confref.available_scales,
    default=confref.available_scales[0],
    required=True,
    help="The desired export scale. Set to none if no upscaling is needed. i.e. --scale 2x ",
)

parser.add_argument(
    "--noise_level",
    type=float,
    default=0.5,
    required=False,
    help="The desired level of noise, between 0.0 and 1.0, you wish to add on top of the AI-upscaled texture. i.e. --noise_level 0.25",
)

parser.add_argument(
    "--export_format",
    type=str,
    choices=confref.available_export_formats,
    required=True,
    default=confref.available_export_formats[0],
    help="The desired export file format. i.e. --export_format png ",
)

parser.add_argument(
    "--and_filters",
    nargs="*",
    default=[
        "",
    ],
    help="Process files with all of the character sequences specified. Space-separated strings. i.e. --and_filters albedo png ",
)

parser.add_argument(
    "--not_filters",
    nargs="*",
    default=[
        "",
    ],
    help="Process files without any of the character sequences specified. Space-separated strings. i.e. --not_filters mask met ",
)

parser.add_argument(
    "--or_filters",
    nargs="*",
    default=[
        "",
    ],
    help="Process files with any of the character sequences specified. Space-separated strings. i.e. --or_filters albedo door wall roof ",
)

compression_formats = set(
    [val for set_ in confref.discrete_compression_map.values() for val in set_]
)
parser.add_argument(
    "--compression",
    type=str,
    choices=sorted(set(compression_formats)),
    default="none",
    help=(
        f"The compression format if it is supported for the respective image format. Refer to 'Using the CLI' for more information. Supported compressions: {confref.discrete_compression_map}".replace(
            ":", " ->"
        )
        .replace(")", " ")
        .replace("(", " ")
        .replace("'bmp'", "[BMP]")
        .replace("'exr'", "[EXR]")
        .replace("'dds'", "[DDS]")
        .replace("'tga'", "[TGA]")
        .replace(",", "")
        .replace("{", "")
        .replace("}", "")
        + " [PNG] -> use --png_compression argument [JPG] -> use --jpg_quality argument"
    ),
)

parser.add_argument(
    "--png_compression",
    type=int,
    choices=list(range(0, 10)),
    default=0,
    help=" png compression value if the export format is .png. 0 = no compression, 9 = highest compression level. i.e. --png_compression 3",
)

parser.add_argument(
    "--jpg_quality",
    type=int,
    choices=list(range(1, 101)),
    default=0,
    help=" jpg image if the export format is .jpg. 0 = lowest quality, 100 = highest quality. i.e. --jpg_quality 92",
)

parser.add_argument(
    "--gamma_correction",
    type=float,
    default=1.0,
    help=" The amount by which to correct the gamma when an image is sent for upscaling. Note: this will not affect the outputted image's gamma. i.e. --gamma_correction 2.2",
)

parser.add_argument(
    "--color_space",
    type=str,
    choices=confref.supported_color_spaces,
    default="sRGB  In/ sRGB Out",
    help=" The color space of the image read (In) and written (Out). i.e. --color_space 'sRGB In/Linear Out'",
)

parser.add_argument(
    "--upscale_precision",
    type=str,
    choices=list(confref.upscale_precision_levels["cuda"].keys()),
    default="normal",
    help=""" 
        The quality of detail in the upscale. Normal is good for most usecases since most image formats 
        support an 8 or 16 bit depth (bpc). High upscale precision should be used for images exported 
        in exr format. 
        """,
)

parser.add_argument(
    "--mipmaps",
    type=str,
    choices=confref.mipmap_levels,
    default=confref.mipmap_levels[0],
    help="The percentage of mip levels you wish to include. i.e. --mipmaps 75%% ",
)


parser.add_argument(
    "--export_color_mode",
    type=str,
    choices=["RGBA", "RGB", "Greyscale", "Indexed"],
    default="RGBA",
    help=f" Export color mode if supported (i.e. the jpg format only supports RGB and Greyscale). i.e. --color_mode RGBA | Supported color modes: "
    "dds: RGB, RGBA | tga: RGBA, RGB | bmp: RGB, RGBA, Indexed | jpg: RGB, Greyscale | png: RGB, RGBA, Greyscale | exr: RGB, RGBA, Greyscale ",
)


parser.add_argument(
    "--split_image_if_too_large",
    "-s",
    action="store_true",
    help="if the chosen image is too large to upscale using video memory, this option allows splitting it up into patches and upscaling each invidually, afterwhich they'll be recombined into a seamless image. i.e. -s",
)

parser.add_argument(
    "--image_split_size",
    type=str,
    choices=["small", "medium", "large", "extra large"],
    default="large",
    help=" If split_image_if_too_large is used, specify the split size of the image. If the chosen size is too large for your video memory capacity, try a smaller split size. i.e. --image_split_size large ",
)

parser.add_argument(
    "--unique_id",
    "-id",
    action="store_true",
    help="Give each file a unique ID to avoid files overwriting others with the same name when exporting to a single location. i.e. -id",
)

parser.add_argument(
    "--prefix",
    type=str,
    default="",
    help="The prefix to append to the export file name. i.e. --prefix cgtu_test ",
)

parser.add_argument(
    "--suffix",
    type=str,
    default="",
    help="The suffix to append to the exported file name before the extension, i.e. --suffix 2x_upscale ",
)

parser.add_argument(
    "--export_color_depth",
    type=int,
    default=8,
    choices=[8, 16, 32],
    help=f" The color depth (in bits per channel) in which to write the image. i.e. --export_color_depth 8. | Supported color depths: \n "
    " .jpg .dds .bmp .tga -> 8-bit | .png -> 8-bit, 16-bit | .exr -> 16-bit, 32-bit ",
)


parser.add_argument(
    "--source_location",
    type=str,
    required=True,
    help="Full path to the source location of images to process wrapped in quotes. i.e. 'C:\\Users\\johndoe\\Deskop\\source_images' ",
)

parser.add_argument(
    "--recursive",
    "-r",
    action="store_true",
    help="Process the chosen source folder and all subfolders.",
)

parser.add_argument(
    "--export_location",
    type=str,
    default="original_location",
    help="Full path to the export location if it's a single location wrapped in quotes or use 'original_location' as the argument to export images to their original locations. i.e. --export_location 'C:\\Users\\johndoe\\Deskop\\results' | i.e. --export_location original_location ",
)

parser.add_argument(
    "--verbose",
    "-v",
    action="store_true",
    help="Print log information to console (does not affect logging to file since that's done by default)",
)


def parse_args(args: argparse.ArgumentParser):
    """Handles user's command line arguments."""
    # 0. Setup log file and args object
    log_file = write_log_to_file(None, None, None)
    parser.parse_args()
    # 1. Clean args

    # ensure source/target locations are valid
    raise_directory_error = False
    if not os.path.isdir(args.source_location):
        raise_directory_error = True
    if args.export_location != "original_location":
        if not os.path.isdir(args.export_location):
            raise_directory_error = True

    if raise_directory_error:
        write_log_to_file(
            "Error",
            f"[ERROR] Either the source location or export location is not a valid location.",
            log_file,
        )
        if args.verbose:
            print(
                "[ERROR] Either the source location or export location is not a valid location."
            )
        sys.exit(1)

    # compression
    if args.export_format == "exr" and args.compression == "none":
        args.compression = "NO"

    if args.export_format == "png":
        args.compression = args.png_compression
    elif args.export_format == "jpg":
        args.compression = args.jpg_quality
    
    # clean pre/suffix
    for char in serconf.illegal_search_characters:
        if char in args.prefix or char in args.suffix:
            write_log_to_file(
                "Error",
                f"Found an illegal character(s) in the prefix or suffix. Ensure that you don't have a any of these characters in your prefix or suffix \n"
                f"{serconf.illegal_search_characters}",
                log_file,
            )
            if args.verbose:
                print(
                    f"[ERROR] Found an illegal character(s) in the prefix or suffix. Ensure that you don't have any of these characters in your prefix or suffix \n"
                    f"{serconf.illegal_search_characters}",
                )
            sys.exit(1)
    # device
    if args.device == "cpu":
        args.upscale_precision = "high"

    # color depth
    if not args.export_color_depth in [8, 16, 32]:
        write_log_to_file(
            "ERROR", "Color depth not supported for the format selected.", log_file
        )
        if args.verbose:
            print("[ERROR] Color depth not supported. Please use 8, 16 or 32 (bpc)")
        sys.exit(1)
    # else:
    if (
        not str(args.export_color_depth)
        in confref.export_color_depth[args.export_format]
    ):
        write_log_to_file(
            "WARNING",
            "{0}-bit color depth not supported for {1} export format. Using highest depth supported by {1} export format: {0}".format(
                args.export_color_depth, args.export_format
            ),
            log_file,
        )
        if args.verbose:
            print(
                "{0}-bit color depth not supported for {1} export format. Using highest depth supported by {1} export format: {0}".format(
                    args.export_color_depth, args.export_format
                ),
            )
        args.export_color_depth = str(
            confref.export_color_depth[args.export_format][-1]
        )
        
    else:
        args.export_color_depth = str(args.export_color_depth)

    # color mode
    args.export_color_mode = {
        "RGBA": "RGBA",
        "RGB": "RGB",
        # "Greyscale+Alpha": "LA", # currently unsupported
        "Greyscale": "L",
        "Indexed": "Indexed",
    }[args.export_color_mode]

    if not args.export_color_mode in confref.format_to_channel_map[args.export_format]:
        supported_modes = str(
            confref.format_to_channel_map[args.export_format]
        ).replace(
            "L",
            ("Greyscale" if not args.export_format == "bmp" else "Indexed")
            .replace("'", "")
            .replace("(", "")
            .replace(")", "")
            .replace("(", ""),
        )
        if args.verbose:
            print(
                f"[ERROR] Export color mode {args.export_color_mode} not supported for the specified export format {args.export_format}.\n Supported color mode for the specified export format are: \n{supported_modes}"
            )
        write_log_to_file(
            "ERROR",
            f"Export color mode {args.export_color_mode} not supported for the specified export format {args.export_format}.\n Supported color mode for the specified export format are: \n{supported_modes}",
            log_file,
        )
        sys.exit(1)

    if (
        (args.export_format == "dds")
        and (args.export_color_mode == "RGB")
        and ((args.mipmaps != "none") or (args.compression != "none"))
    ):
        while True:
            res = input(
                "RGB export color mode only supported with no compression and no mipmaps (i.e.: --compression none --mipmaps none).\nProceed with RGBA export color mode? (y/n)"
            )
            if res in ["y", "n"]:
                if res == "y":
                    args.export_color_mode = "RGBA"
                    break
                else:
                    sys.exit(1)
            else:
                print(
                    "Please type 'y' for YES or 'n' for NO the press Enter to proceed."
                )
    elif (args.export_format == "bmp") and (args.export_color_mode == "Indexed"):
        while True:
            res = input(
                "Indexed export color mode supported only with RLE compression for .bmp images. \nProceed with RGBA? (y/n)"
            )
            if res in ["y", "n"]:
                if res == "y":
                    args.export_color_mode = "RGBA"
                    break
                else:
                    sys.exit(1)
            else:
                print(
                    "Please type 'y' for YES or 'n' for NO the press Enter to proceed."
                )

    # gamma correction

    if not (0.1 <= args.gamma_correction <= 5.0):
        if args.verbose:
            print("[ERROR] Gamma value must be between 0.1 and 5.0 inclusive.")
        write_log_to_file(
            "ERROR",
            "Gamma value must be between 0.1 and 5.0 inclusive. ",
            log_file,
        )
        sys.exit(1)

    # upscale_precision
    if args.upscale_precision == "high":
        args.image_split_size = "small"
        args.split_image_if_too_large = False

    # split large image
    if args.split_image_if_too_large:
        args.image_split_size = {
            "small": "1",
            "medium": "2",
            "large": "3",
            "extra large": "4",
        }[args.image_split_size]

    # noise factor
    if not (0.0 <= args.noise_level <= 1.0):
        if args.verbose:
            print("[ERROR] noise_factor must be between 0.0 and 1.0 inclusive.")
        write_log_to_file(
            "ERROR",
            "noise_factor must be between 0.0 and 1.0 inclusive. ",
            log_file,
        )
        sys.exit(1)  
    # 2. populate image cache TKListbox.populate
    TkListbox.populate(
        obj=None, parent=args.source_location, recursive=args.recursive, thread=False
    )

    # 3. filter image list and import that processed ma
    serconf.last_used_dir_or_file = args.source_location
    serconf.recursive = args.recursive
    SearchFilterFrame.apply_filter(
        None,
        None,
        "chosen_directory",
        args.and_filters,
        args.or_filters,
        args.not_filters,
    )

    
    if len(image_paths_cache[0]) == 0:
        write_log_to_file(
            "WARNING",
            "No images that match the filters were found in the source location. Did you mean to add the recursive flag (-r) ?",
            log_file,
        )
        if args.verbose:
            print(
                "[WARNING] No images that match the filters were found in the source location. Did you mean to add the recursive flag? (-r)?"
            )
        sys.exit(0)

    # setup export config dict to pass to the validator
    export_config: Dict[str, Union[int, float, bool, str]] = {
        "device": args.device,
        "scale": args.scale,
        "export_format": args.export_format,
        "compression": "none" if args.compression is None else args.compression,
        "mipmaps": args.mipmaps,
        "prefix": args.prefix,
        "suffix": args.suffix,
        "numbering": args.unique_id,
        "export_to_original": True
        if args.export_location == "original_location"
        else False,
        "single_export_location": args.export_location
        if args.export_location != "original_location"
        else "",
        "verbose": args.verbose,
        "weight_file": None,
        "noise_level": args.noise_level,
        "upscale_precision": args.upscale_precision,
        "export_color_mode": args.export_color_mode,
        "color_space": args.color_space,
        "export_color_depth": args.export_color_depth,
        "gamma_adjustment": args.gamma_correction,
        "split_large_image": args.split_image_if_too_large,
        "image_split_size": args.image_split_size,
    }

    # update ExportConfig data class
    expconf.device = export_config["device"]
    expconf.scale = export_config["scale"]
    expconf.export_format = export_config["export_format"]
    expconf.compression = export_config["compression"]
    expconf.mipmaps = export_config["mipmaps"]
    expconf.color_space = export_config["color_space"]
    expconf.export_color_depth = export_config["export_color_depth"]
    expconf.export_color_mode = export_config["export_color_mode"]
    expconf.upscale_precision = export_config["upscale_precision"]
    expconf.single_export_location = export_config["single_export_location"]
    expconf.save_in_existing_location = export_config["export_to_original"]
    expconf.save_prefix = export_config["prefix"]
    expconf.save_suffix = export_config["suffix"]
    expconf.save_numbering = export_config["numbering"]
    expconf.gamma_adjustment = export_config["gamma_adjustment"]
    expconf.split_large_image = export_config["split_large_image"]
    expconf.patch_size = export_config["image_split_size"]

    pprint.pprint(export_config)
    return export_config
