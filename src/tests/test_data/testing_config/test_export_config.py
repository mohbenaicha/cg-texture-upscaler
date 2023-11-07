# import sys
import os

# sys.path.append("C:\\Users\\Moham\\Desktop\\official_cg_tool_dev_repo\\src")
from app_config.config import ExportConfig


ExportConfig.single_export_location = os.path.join(
    os.getcwd()+"\\",
    "tests", # TODO: remove for pytest
    "test_data",
    "export_test_data",
    "model_output_test_media",
    "single_export_location",
)
ExportConfig.device = 'cuda'


class TestConfig:
    test_device_cpu = type("", ExportConfig.__bases__, dict(ExportConfig.__dict__))
    test_device_cpu.scale = "2x"
    test_device_cpu.device = "cpu"

    test_device_gpu = type("", ExportConfig.__bases__, dict(ExportConfig.__dict__))
    test_device_gpu.scale = "2x"

    test_device_config_map = {"cpu": test_device_cpu, 
                              "cuda": test_device_gpu}

    test_scale_none = type("", ExportConfig.__bases__, dict(ExportConfig.__dict__))
    test_scale_none.scale = "none"

    test_scale_2x = type("", ExportConfig.__bases__, dict(ExportConfig.__dict__))
    test_scale_2x.scale = "2x"

    test_scale_4x = type("", ExportConfig.__bases__, dict(ExportConfig.__dict__))
    test_scale_4x.scale = "4x"

    test_scale_config = [test_scale_none, test_scale_2x, test_scale_4x]

    test_format_png = type("", ExportConfig.__bases__, dict(ExportConfig.__dict__))
    test_format_png.export_format = "png"

    test_format_bmp = type("", ExportConfig.__bases__, dict(ExportConfig.__dict__))
    test_format_bmp.export_format = "bmp"

    test_format_jpg = type("", ExportConfig.__bases__, dict(ExportConfig.__dict__))
    test_format_jpg.export_format = "jpg"

    test_format_dds = type("", ExportConfig.__bases__, dict(ExportConfig.__dict__))
    test_format_dds.export_format = "dds"

    test_format_tga = type("", ExportConfig.__bases__, dict(ExportConfig.__dict__))
    test_format_tga.export_format = "tga"

    test_format_exr = type("", ExportConfig.__bases__, dict(ExportConfig.__dict__))
    test_format_exr.export_format = "exr"

    export_format_config_map = {
        "png": test_format_png,
        "bmp": test_format_bmp,
        "jpg": test_format_jpg,
        "dds": test_format_dds,
        "tga": test_format_tga,
        "exr": test_format_exr,
    }

    test_compression_none = type(
        "", ExportConfig.__bases__, dict(ExportConfig.__dict__)
    )
    test_compression_none.compression = "no"

    test_compression_rle = type("", ExportConfig.__bases__, dict(ExportConfig.__dict__))
    test_compression_rle.compression = "rle"

    test_compression_dxt1 = type(
        "", ExportConfig.__bases__, dict(ExportConfig.__dict__)
    )
    test_compression_dxt1.compression = "dxt1"

    test_compression_dxt3 = type(
        "", ExportConfig.__bases__, dict(ExportConfig.__dict__)
    )
    test_compression_dxt3.compression = "dxt3"

    test_compression_dxt5 = type(
        "", ExportConfig.__bases__, dict(ExportConfig.__dict__)
    )
    test_compression_dxt5.compression = "dxt5"

    test_compression_jpeg = type(
        "", ExportConfig.__bases__, dict(ExportConfig.__dict__)
    )
    test_compression_jpeg.compression = "jpeg"

    test_compression_lossless_jpeg = type(
        "", ExportConfig.__bases__, dict(ExportConfig.__dict__)
    )
    test_compression_lossless_jpeg.compression = "losslessjpeg"

    test_compression_pxr24 = type(
        "", ExportConfig.__bases__, dict(ExportConfig.__dict__)
    )
    test_compression_pxr24.compression = "pxr24"

    test_compression_piz = type("", ExportConfig.__bases__, dict(ExportConfig.__dict__))
    test_compression_piz.compression = "piz"

    test_compression_zips = type(
        "", ExportConfig.__bases__, dict(ExportConfig.__dict__)
    )
    test_compression_zips.compression = "zips"

    compression_config_map = {
        "RLE": test_compression_rle,
        "DXT1": test_compression_dxt1,
        # "DXT3": test_compression_dxt3, # TODO: double-check
        "DXT5": test_compression_dxt5,
        "JPEG": test_compression_jpeg, # represented by Quality 92 
        "LOSSLESSJPEG": test_compression_lossless_jpeg, # represented by Quality 100
        "PXR24": test_compression_pxr24,
        "PIZ": test_compression_piz,
        "ZIPS": test_compression_zips,
    }

    
    test_numbering_true = type("", ExportConfig.__bases__, dict(ExportConfig.__dict__))    
    test_numbering_true.save_numbering = True

    test_numbering_false = type("", ExportConfig.__bases__, dict(ExportConfig.__dict__))
    test_numbering_false.save_numbering = False

    test_numbering_config_map = {
        "True": test_numbering_true, 
        "False": test_numbering_false
        }

    test_prefix = type("", ExportConfig.__bases__, dict(ExportConfig.__dict__))
    test_prefix.save_prefix = "test_prefix"

    test_suffix = type("", ExportConfig.__bases__, dict(ExportConfig.__dict__))
    test_suffix.save_suffix = "test_suffix"

    test_prefix_suffix_config_map = {
        "pre": test_prefix,
        "suf": test_suffix,
        "none": ExportConfig
    }

    test_save_to_original = type(
        "", ExportConfig.__bases__, dict(ExportConfig.__dict__)
    )
    test_save_to_original.save_prefix = "test"
    test_save_to_original.single_export_location = ""
    test_save_to_original.save_in_existing_location = True

    test_save_to_single_folder = type(
        "", ExportConfig.__bases__, dict(ExportConfig.__dict__)
    )
    test_save_to_single_folder.single_export_location = os.path.join(
        os.getcwd()+"\\",
        "tests", 
        "test_data", "export_test_data", "model_output_test_media", "single_export_location"
    )
