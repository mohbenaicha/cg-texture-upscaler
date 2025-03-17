from typing import Optional, Union
import torch, numpy as np
from utils.image_utilities.interfaces import IImageContainer
from utils.image_utilities import ImageConfig, ImageIO, ImageProcessor
from utils.export_utils import ProcessingStep
from app_config.config import ExportConfig # shared state config accross images
import os


class ImageContainer(IImageContainer):
    """An image container class that orchestrates image transformation pipeline"""

    def __init__(self, processing_step: ProcessingStep, **kwargs):
        self.alpha: Optional[Union[torch.Tensor, np.ndarray]] = None
        self.color_channels: Optional[Union[torch.Tensor, np.ndarray]] = None
        self.image: Optional[Union[torch.Tensor, np.ndarray]] = None
        self.noisy_copy: Optional[np.ndarray] = None
        self.config = ImageConfig(**kwargs) # unique per-image config, may contained shared state config
        self._image_io = ImageIO(self) 
        self._image_processor = ImageProcessor(
            self, gamma_adjustment=ExportConfig.gamma_adjustment
        )
        self.master_frame = kwargs.get("master_frame", None)
        self.step = processing_step

        def read_image(self) -> None:
            dir_path, img_name = os.path.split(self.config.src_path)
            self._image_io.read_image(dir_path, img_name)

        def write_image(self) -> None:
            self._image_io.write_image()

        def preprocess_image(self) -> None:
            self._image_processor.preprocess_image()

        def postprocess_image(self) -> None:
            self._image_processor.postprocess_image()

        def process_image(self) -> None:
            self._image_processor.process_image()
