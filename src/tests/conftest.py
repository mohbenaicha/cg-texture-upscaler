import os
import sys
from typing import List, Tuple

sys.path.append("C:\\Users\\Moham\\Desktop\\official_cg_tool_dev_repo\\src")
import pytest
from model.utils import write_log_to_file
from tests.test_data.testing_config.test_generator_config import (
    generator_constructor_args,
)
from tests.test_data.testing_config.test_export_config import TestConfig
from gui.frames import TkListbox


test_log_file = write_log_to_file(None, None, None)


@pytest.fixture()  # TODO Reenable
def test_generator_constructor():
    """Fixture for testing Generator constructor with valid and invalid arguments
    Generator component constructors like the Basic_Block and Dense_Block
    are not tested since they don't have variable input arguments"""
    return generator_constructor_args


@pytest.fixture()  # TODO Reenable
def test_export_config(multiple_images: bool = False):
    """Fixture for testing export configuration."""
    if not multiple_images:
        test_image_path = os.path.join(
            os.getcwd()+"\\",
            "tests" # TODO: remove for pytest
            "test_data",
            "export_test_data",
            "model_output_test_media",
            "terrain",
            "metal",
        )
        recursive = False
    else:
        test_image_path = os.path.join(
            os.getcwd()+"\\",
            "tests", # TODO: remove for pytest
            "test_data",
            "export_test_data",
            "model_output_test_media",
        )
        recursive = True
    TkListbox.populate(
        obj=None, parent=test_image_path, recursive=recursive, thread=False
    )
    return TestConfig
