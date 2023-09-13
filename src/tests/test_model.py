import os
import sys
import time


sys.path.append("C:\\Users\\Moham\\Desktop\\official_cg_tool_dev_repo\\src")
import pytest
import torch
import numpy
import PIL
from model.rrdbnet_arch import Generator
from model.utils import export_images
from gui.frames.export_frame import ExportFrame, ExportThread
# from conftest import test_generator_constructor, test_export_config




def test_model_constructor(test_generator_constructor):  # TODO: restore pytest fixture (test_generator_constructors):
    """
    Sanity check model loading is correct.
    This test ensures the correct model architecture is loaded. For checking the values
    of parameters. The following tests the model output.
    """
    config = test_generator_constructor()
    with open(
        os.path.join(
            os.getcwd()+"\\",
            "tests",
            "test_data",
            "testing_config",
            "model_params.config",
        ),
        "r",
    ) as fp:
        loaded_params = [fp.readline().rstrip("\n") for _ in range(702)]
    for i in range(4):
        gen = Generator(**config[i])
        assert [loaded_params == [param[0] for param in gen.named_parameters()]]
        if config[i]["scale"] == 2:
            assert type(gen.unshuffle) == torch.nn.PixelUnshuffle
    return


def test_model_output(test_export_config): #TODO: restore pytest fixture argument
    """
    Test upscaled images outputted by the model for pixel-by-pixel color accuracy.
    This test exports 6 sample images (representing the supported formats
    at 3 individual resolutions, the origal, 2x and 4x. It then reads the images
    and ensures that pixel values are as expected.
    """
    sample_dir = os.path.join(os.getcwd()+"\\",
                              "test", 
                              "test_data", "model_test_data", "upscaled_samples")
    export_dir = os.path.join(os.getcwd()+"\\",
                              "test", 
                              "test_data", "model_test_data", "model_output_images")
    
    upscale_2x_config = test_export_config(multiple_images=True).test_scale_2x
    upscale_4x_config = test_export_config(multiple_images=True).test_scale_4x
    
    upscale_2x_config.single_export_location = export_dir
    upscale_4x_config.single_export_location = export_dir

    conf_map = {"2x": upscale_2x_config, "4x":upscale_4x_config}
    
    for scale, config in conf_map.items():
        parsed_config = ExportFrame.parse_export_config(config)
        export_thread = ExportThread(
            target=export_images,
            args=(None, parsed_config, None, "all", None, None, False),
        )
        export_thread.start()
        time.sleep(10)
        pairs = [(test_img, sample) for test_img, sample in zip(os.listdir(export_dir), [img_name for img_name in os.listdir(sample_dir) if scale in img_name])]
        for pair in pairs:
            test = numpy.asarray(PIL.Image.open(
                os.path.join(export_dir, pair[0])
                ))
            sample = numpy.asarray(PIL.Image.open(
                os.path.join(sample_dir, pair[1])
            ))
            assert all(
                [all([val == 0 for val in (test[channel].flatten()-sample[channel].flatten())])
                for channel in range(test.shape[2])]
                )
            os.remove(os.path.join(export_dir, pair[0]))
