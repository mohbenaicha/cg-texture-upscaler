from abc import ABC, abstractmethod
import numpy as np
from typing import Any, Tuple

class IImageIO(ABC):
    """Interface for reading and writing images."""
    
    @abstractmethod
    def read_image(self, src_path: str, img_name: str) -> np.ndarray:
        """Reads an image from disk and returns it as a NumPy array."""
        pass
    
    @abstractmethod
    def write_image(self, image: np.ndarray, trg_path: str, export_config: dict) -> None:
        """Writes an image to disk based on export configuration."""
        pass

class IImageProcessor(ABC):
    """Interface for image processing operations."""
    
    @abstractmethod
    def check_all_values_equivalent(self, image: np.ndarray) -> bool:
        """Checks if all pixel values in an image are the same."""
        pass
    
    @abstractmethod
    def apply_gamma_correction(self, image: np.ndarray, gamma: float) -> np.ndarray:
        """Applies gamma correction to an image."""
        pass
    
    @abstractmethod
    def convert_datatype(self, image: np.ndarray, input: bool) -> np.ndarray:
        """Converts image datatype before or after processing."""
        pass

class IChannelManager(ABC):
    """Interface for handling color and alpha channel operations."""
    
    @abstractmethod
    def split_channels(self, image: np.ndarray) -> Tuple[np.ndarray, np.ndarray | None]:
        """Splits an image into color and alpha channels."""
        pass
    
    @abstractmethod
    def recombine_channels(self, color: np.ndarray, alpha: np.ndarray | None) -> np.ndarray:
        """Recombines color and alpha channels into a single image."""
        pass

class IImageUpscaler(ABC):
    """Interface for image upscaling."""
    
    @abstractmethod
    def upscale(self, image: np.ndarray, export_config: dict) -> np.ndarray:
        """Upscales an image based on export configuration."""
        pass

class IImageConfig(ABC):
    """Interface for handling image processing configurations."""
    
    @abstractmethod
    def get_setting(self, key: str) -> Any:
        """Retrieves a setting from the configuration."""
        pass
    
    @abstractmethod
    def update_setting(self, key: str, value: Any) -> None:
        """Updates a setting in the configuration."""
        pass
