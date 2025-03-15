from typing import Optional, Union
import torch, numpy as np
from utils.image_utilities.interfaces import IImageContainer
from utils.image_utilities import ImageConfig, ImageIO, ImageProcessor
from app_config.config import ExportConfig
import os


class ImageContainer(IImageContainer):
    """An image container class that orchestrates image transformation pipeline"""

    def __init__(self, **kwargs):
        self._alpha: Optional[Union[torch.Tensor, np.ndarray]] = None
        self._color_channels: Optional[Union[torch.Tensor, np.ndarray]] = None
        self._image: Optional[Union[torch.Tensor, np.ndarray]] = None
        self._config = ImageConfig(**kwargs)
        # self.noisy_copy
        self._image_io = ImageIO(self)
        self._image_processor = ImageProcessor(self, gamma_adjustment=ExportConfig.gamma_adjustment)
        self.master_frame = kwargs.get("master_frame", None)


        def read_image(self, src_path: str) -> None:
            dir_path, img_name = os.path.split(src_path)
            self._image_io.read_image(dir_path, img_name)
        
        def write_image(self, path: str) -> None:
            self._image_io.write_image(self.master_frame, ExportConfig.cli_verbosity)
        
        def process_image(self) -> None:
            self._image_processor.preprocess_image()
            self._image_processor.process_image()
            self._image_postprocessor.postprocess_image()
            raise NotImplementedError

        @property
        def config(self):
            return self._config  # public method to access the private attribute

        @property
        def image(self):
            return self._image  # public method to access the private attribute

        @property
        def color_channels(self):
            return self._color_channels

        @property
        def alpha(self):
            return self._alpha
