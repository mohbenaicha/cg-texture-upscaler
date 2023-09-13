import sys

sys.path.append("C:\\Users\\Moham\\Desktop\\official_cg_tool_dev_repo\\src")
import os
import time
from functools import partial
from typing import Any
import torch
import pytest
from gui.frames.export_frame import ExportFrame, ExportThread
from model.utils import export_images
# from conftest import test_export_config  # TODO: remove
from app_config.config import PrePostProcessingConfig as ppconf, ExportConfig

# export_config = partial(test_export_config, multiple_images=False)
export_img_path = os.path.join(
    os.getcwd()+"\\",
    "tests" # TODO: Uncomment for pytest
    "test_data",
    "export_test_data",
    "model_output_test_media",
    "single_export_location",
)

export_img_path_naming_and_export = os.path.join(
    os.getcwd()+"\\",
    "tests" # TODO: Uncomment for pytest
    "test_data",
    "export_test_data",
    "model_output_test_media",
)


def handle_compression_test(
    export_config: ExportConfig,
    extensions: list[str],
    assertion_to_evaluate: str,
    set_export_format: bool,
    no_compression_map: dict,
):
    """
    Exports an image based on the specified format and compression
    specification then evalutes the assertion to pass the test.
    """
    for ext in extensions:
        if set_export_format:
            setattr(export_config, "export_format", ext)
        parsed_config = ExportFrame.parse_export_config(export_config)

        export_thread = ExportThread(
            target=export_images,
            args=(None, parsed_config, None, "all", None, None, False),
        )
        export_thread.start()
        time.sleep(1)

        grep_val = "Compression" if ext != "jpg" else "Quality"
        print()
        result = os.popen(  # userd in assertion
            f"identify -verbose {export_img_path}\single_panel.{ext} | grep {grep_val}"
        ).read()
        exec(assertion_to_evaluate)
        os.remove(os.path.join(export_img_path, f"single_panel.{ext}"))


@pytest.mark.parametrize("test_export_config", ["False"], indirect=True)
def test_device(test_export_config):  # TODO: restore pytest fixture argument
    """
    Test the appropriate device is used for processing and exporting an image.
    This test exportes an image using CPU then NVidia's CUDA technology and
    checks to see if the appropriate device is active during the export process
    """
    for device in ExportConfig.available_devices:
        config = test_export_config().test_device_config_map[device]
        # config = export_config().test_device_config_map[device]
        parsed_config = ExportFrame.parse_export_config(config)
        export_thread = ExportThread(
            target=export_images,
            args=(None, parsed_config, None, "all", None, None, False),
        )
        export_thread.start()
        time.sleep(7)
        assert (
            torch.cuda.is_initialized()
            if device == "cuda"
            else torch.cuda.is_initialized() == False
        )
    os.remove(os.path.join(export_img_path, "single_panel.tga"))


@pytest.mark.parametrize("test_export_config", ["False"], indirect=True)
def test_scale(test_export_config):  # TODO: restore pytest fixture argument
    """
    Tests 1, 2, and 4 resolutions of the upscaled image.
    This test scales an image at 1x, 2x and 4x the image format
    then reads the output image size to ensure it has been upscaled.
    """
    scales = ["512x512", "1024x1024", "2048x2048"]
    sleep = [1, 8, 60]
    # for i, config in enumerate(export_config().test_scale_config):
    for i, config in enumerate(test_export_config().test_scale_config):
        parsed_config = ExportFrame.parse_export_config(config)
        export_thread = ExportThread(
            target=export_images,
            args=(None, parsed_config, None, "all", None, None, False),
        )

        export_thread.start()
        time.sleep(sleep[i])
        result = os.popen(
            f"identify -verbose {export_img_path}\single_panel.tga | grep Geometry"
        ).read()
        assert scales[i] in result
        os.remove(os.path.join(export_img_path, f"single_panel.tga"))


@pytest.mark.parametrize("test_export_config", ["False"], indirect=True)
def test_format(test_export_config):  # TODO: restore pytest fixture argument
    """
    Test that images are exported in their proper format.
    This test exports an image as various image formats and then reads them
    to ensure they export as expected.
    """
    for frmt in ppconf.available_export_formats:
        # parsed_config = ExportFrame.parse_export_config(
        #     export_config().export_format_config_map[frmt]
        # )
        parsed_config = ExportFrame.parse_export_config(
            test_export_config().export_format_config_map[frmt]
        )
        export_thread = ExportThread(
            target=export_images,
            args=(None, parsed_config, None, "all", None, None, False),
        )
        export_thread.start()
        time.sleep(1)
        result = os.popen(
            f"identify -verbose {export_img_path}\single_panel.{frmt} | grep Format"
        ).read()

        # here image magick identifies .jpg formats officially as jpeg
        if frmt == "jpg":
            magick_frmt = "jpeg"
        else:
            magick_frmt = frmt
        assert magick_frmt.upper() in result
        os.remove(os.path.join(export_img_path, f"single_panel.{frmt}"))


@pytest.mark.parametrize("test_export_config", ["False"], indirect=True)
def test_compression(test_export_config):  # TODO: restore pytest fixture argument
    """
    Test that proper compression is applied.
    This test exports an image using various image formats and compresisons
    and then reads them to ensure they are compressed as expected.
    """
    # for compression, config in export_config().compression_config_map.items():
    for compression, config in test_export_config().compression_config_map.items():
        formats = [
            ext
            for ext in list(ppconf.compression_map.keys())
            if compression.lower() in ppconf.compression_map[ext]
        ]

        # adjusting the assertion condition to fit Image Magick's compression syntax
        if compression == "JPEG":
            condition = "92"
        elif compression == "LOSSLESSJPEG":
            condition = "100"
        else:
            condition = (
                compression
                if not compression in ["PXR24", "PIZ", "ZIP", "ZIPS"]
                else (
                    compression[0] + compression[1:].lower()
                    if not compression == "ZIPS"
                    else "ZipS"
                )
            )
        print()
        handle_compression_test(
            export_config=config,
            extensions=formats,
            assertion_to_evaluate=f"assert '{condition}' in result",
            set_export_format=True,
            no_compression_map=None,
        )


@pytest.mark.parametrize("test_export_config", ["True"], indirect=True)
def test_naming(test_export_config):  # TODO: restore pytest fixture argument
    """'Test if unique IDs, suffixes and prefixes are assigned to file names.
    This test exports images with and without assigning a unique ID,
    with and without assgining a prefix and suffix, and then reads them
    to ensure that they have unique IDs and/or prefixes/suffixes or not.
    """
    # export_config = partial(test_export_config, multiple_images=True)
    orig_f_names = []
    exp_path = export_img_path_naming_and_export
    [orig_f_names.extend(files[2]) for files in os.walk(os.path.join(exp_path))]
    for cond in ["True", "False"]:
        # config = export_config().test_numbering_config_map[cond]
        config = test_export_config().test_numbering_config_map[cond]
        parsed_config = ExportFrame.parse_export_config(config)
        export_thread = ExportThread(
            target=export_images,
            args=(None, parsed_config, None, "all", None, None, False),
        )
        export_thread.start()
        time.sleep(2)
        for i, f_name in enumerate(
            sorted(os.listdir(os.path.join(exp_path, "single_export_location")))
        ):
            if cond == "True":
                assert str(i) in f_name
            else:
                assert f_name[:-4] == sorted(orig_f_names)[i][:-4]
            os.remove(os.path.join(exp_path, "single_export_location", f_name))

    for add_name in ["pre", "suf", "none"]:
        # config = export_config().test_prefix_suffix_config_map[add_name]
        config = test_export_config().test_prefix_suffix_config_map[add_name]
        parsed_config = ExportFrame.parse_export_config(config)
        export_thread = ExportThread(
            target=export_images,
            args=(None, parsed_config, None, "all", None, None, False),
        )
        export_thread.start()
        time.sleep(2)
        for i, f_name in enumerate(
            sorted(os.listdir(os.path.join(exp_path, "single_export_location")))
        ):
            if add_name == "none":
                assert f_name[:-4] == sorted(orig_f_names)[i][:-4]
            elif add_name == "pre":
                assert (
                    f_name[:-4]
                    == parsed_config["prefix"] + "_" + sorted(orig_f_names)[i][:-4]
                )
            elif add_name == "suf":
                assert (
                    f_name[:-4]
                    == sorted(orig_f_names)[i][:-4] + "_" + parsed_config["suffix"]
                )
            os.remove(os.path.join(exp_path, "single_export_location", f_name))


@pytest.mark.parametrize("test_export_config", ["True"], indirect=True)
def test_export_location(test_export_config):  # TODO: restore pytest fixture argument
    """
    Test exporting images to a single location, or to the original location.
    This test exports images to a single location and then checks to see they
    have all been exported there. It then exports the images to their original
    location using a prefix and checks to see each image is exported to its
    original path.
    """
    # export_config = partial(test_export_config, multiple_images=True)
    # config = export_config().test_save_to_original
    config = test_export_config().test_save_to_original
    parsed_config = ExportFrame.parse_export_config(config)
    orig_files_map = {
        f_name: item[0]
        for item in os.walk(export_img_path_naming_and_export)
        for f_name in item[2]
    }

    export_thread = ExportThread(
        target=export_images,
        args=(None, parsed_config, None, "all", None, None, False),
    )
    export_thread.start()
    time.sleep(2)
    for f_name, f_path in orig_files_map.items():
        assert "test_" + f_name[:-4] + ".tga" in os.listdir(f_path)
        os.remove(os.path.join(f_path, "test_" + f_name[:-4] + ".tga"))

    # config = export_config().test_save_to_single_folder
    config = test_export_config().test_save_to_single_folder
    parsed_config = ExportFrame.parse_export_config(config)
    export_thread = ExportThread(
        target=export_images,
        args=(None, parsed_config, None, "all", None, None, False),
    )
    export_thread.start()
    time.sleep(2)

    for f_name, f_path in orig_files_map.items():
        assert f_name[:-4] + ".tga" in os.listdir(
            parsed_config["single_export_location"]
        )
        os.remove(
            os.path.join(parsed_config["single_export_location"], f_name[:-4] + ".tga")
        )
    return
