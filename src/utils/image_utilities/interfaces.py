from abc import ABC, abstractmethod
import numpy as np
import torch


class IImageIO(ABC):
    """Interface for reading and writing images."""

    @abstractmethod
    def read_image(self, src_path: str, img_name: str) -> np.ndarray:
        """Reads an image from disk and returns it as a NumPy array."""
        pass

    @abstractmethod
    def write_image(self) -> None:
        """Writes an image to disk based on export configuration."""
        pass


class IImageProcessor(ABC):
    """Interface for image processing operations."""

    @abstractmethod
    def preprocess_image(
        self,
    ) -> None:
        """Preprocesses the image."""
        pass

    @abstractmethod
    def postprocess_image(
        self,
    ) -> None:
        """Postprocesses the image."""
        pass

    @abstractmethod
    def process_image(
        self,
    ) -> None:
        """Processes the image."""
        pass


class IImageUpscaler(ABC):
    """Interface for image upscaling."""

    @abstractmethod
    def scale_image(self) -> torch.Tensor:
        """Upscales an image based on export configuration."""
        pass


class IImageContainer(ABC):
    """Interface for an image container class that orchestrates image transformation pipeline"""

    @abstractmethod
    def read_image(self) -> None:
        """Reads the image from disk."""
        pass

    @abstractmethod
    def write_image(self) -> None:
        """Writes the image to disk."""
        pass

    @abstractmethod
    def preprocess_image(self) -> None:
        """Processes the image, including dimensions, color mode, space, depth and gamma."""
        pass

    @abstractmethod
    def postprocess_image(self) -> None:
        """Postprocesses the image including color mode, space, depth, gamma and noise."""
        pass

    @abstractmethod
    def process_image(self) -> None:
        """Processes the image including upscaling, downscaling, etc."""
        pass
