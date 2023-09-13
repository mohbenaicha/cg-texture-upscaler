import os, sys
from gui.frames import SearchFilterFrame, TkListbox
from app_config.config import PrePostProcessingConfig as ppconf
from app_config.config import ExportConfig as expconf
from app_config.config import SearchConfig as serconf
from caches.cache import image_paths_cache
from model import write_log_to_file
import argparse

parser = argparse.ArgumentParser()
parser.add_argument(
    "--device",
    type=str,
    choices=expconf.available_devices,
    default=expconf.available_devices[0],
    required=True,
    help="The device to use if upscaling. Defaults to CPU.",
)
parser.add_argument(
    "--scale",
    type=str,
    choices=ppconf.available_scales,
    default=ppconf.available_scales[0],
    required=True,
    help="The desired export scale. Set to none if no upscaling is needed.",
)
parser.add_argument(
    "--export_format",
    type=str,
    choices=ppconf.available_export_formats,
    required=True,
    default=ppconf.available_export_formats[0],
    help="The desired export file format.",
)

compression_formats = []
for group in list(ppconf.compression_map.values()):
    for item in group:
        compression_formats.append(item)
parser.add_argument(
    "--and_filters",
    nargs="*",
    default=[
        "",
    ],
    help="Process files with all of the character sequences specified.",
)
parser.add_argument(
    "--or_filters",
    nargs="*",
    default=[
        "",
    ],
    help="Process files with any of the character sequences specified.",
)
parser.add_argument(
    "--compression",
    type=str,
    choices=sorted(set(compression_formats)),
    default=compression_formats[0],
    help="The compression format if it is supported for the respective image format. Refer to the cli guide for more information.",
)
parser.add_argument(
    "--mipmaps",
    type=str,
    choices=ppconf.mipmap_levels,
    default=ppconf.mipmap_levels[0],
    help="The percentage of mip level you wish to include",
)
parser.add_argument(
    "--unique_id",
    "-id",
    action="store_true",
    help="Give eah file a unique ID to avoid files overwriting others with the same name.",
)
parser.add_argument(
    "--prefix",
    type=str,
    default="",
    help="The prefix to append to the export file name",
)
parser.add_argument(
    "--suffix",
    type=str,
    default="",
    help="The suffix to append to the export file name before the extension",
)
parser.add_argument(
    "--source_location",
    type=str,
    required=True,
    help="Full path to the export location if it's a single location or use 'single_location' to export to a single location",
)
parser.add_argument(
    "--recursive",
    "-r",
    action="store_true",
    help="Process the chosen folder and all subfolders.",
)

parser.add_argument(
    "--verbose",
    "-v",
    action="store_true",
    help="Print log information to console (does not affect logging to file)",
)

parser.add_argument(
    "--export_location",
    type=str,
    default="original_location",
    help="Full path to the export location if it's a single location or use 'original_location' to export images to their original locations",
)


def clean_args(args):
    ''' Handles user's command line arguments.'''
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
        print(
            "[ERROR] Either the source location or export location is not a valid location."
        )
        sys.exit(1)

    # clean pre/suffix

    for char in serconf.illegal_search_characters:
        if char in args.prefix or char in args.suffix:
            write_log_to_file(
                "Error",
                f"Found an illegal character(s) in the prefix or suffix. Ensure you don't have a any of these characters in your prefix or suffix \n"
                f"{serconf.illegal_search_characters}",
                log_file,
            )
            print(
                f"[ERROR] Found an illegal character(s) in the prefix or suffix. Ensure you don't have a any of these characters in your prefix or suffix \n"
                f"{serconf.illegal_search_characters}",
            )
            sys.exit(1)

    # 2. populate image cache using TKListbox.populate
    TkListbox.populate(
        obj=None, parent=args.source_location, recursive=args.recursive, thread=False
    )

    # 3. filter image list and import that processed ma
    serconf.last_used_dir_or_file = args.source_location
    serconf.recursive = args.recursive
    SearchFilterFrame.apply_filter(
        None, None, "chosen_directory", args.and_filters, args.or_filters
    )
    if len(image_paths_cache[0]) == 0:
        write_log_to_file(
            "Warning",
            "No images that match the filters were found in the source location. Did you mean to add the recursive flag (-r) ?",
            log_file,
        )
        print(
            "[WARNING] No images that match the filters were found in the source location. Did you mean to add the recursive flag? (-r)?"
        )
        sys.exit(0)

    export_config = {
        "device": args.device,
        "scale": args.scale,
        "format": args.export_format,
        "compression": "undefined"
        if args.compression not in ppconf.compression_map[args.export_format]
        else args.compression,
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
        "custom_weights": None,
    }
    return export_config
