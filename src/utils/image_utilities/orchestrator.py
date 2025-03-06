from utils.image_utilities import ImageConfig
from typing import Optional, Union
import torch, numpy as np

class ImageContainer:
    """ An image container class that orchestrates image transformation pipeline """
    def __init__(self, **kwargs):
        self.config = ImageConfig(**kwargs) # used in setting self.mode, self.proceed_with_split, self.linear_upscale_all_channels, 
        self.alpha: Optional[Union[torch.Tensor, np.ndarray]] = None
        self.color_channels: Optional[Union[torch.Tensor, np.ndarray]] = None
        # self.noisy_copy