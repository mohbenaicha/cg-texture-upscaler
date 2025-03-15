from abc import ABC, abstractmethod
import numpy as np
from typing import TYPE_CHECKING
import customtkinter as ctk

if TYPE_CHECKING:
    import torch 


class IImageIO(ABC):
    """Interface for reading and writing images."""

    @abstractmethod
    def read_image(self, src_path: str, img_name: str) -> np.ndarray:
        """Reads an image from disk and returns it as a NumPy array."""
        pass

    @abstractmethod
    def write_image(self, master: ctk.CTkFrame, verbose: bool) -> None:
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
    def scale_image(self, export_config: dict) -> torch.Tensor:
        """Upscales an image based on export configuration."""
        pass


class IImageContainer(ABC):
    """Interface for an image container class that orchestrates image transformation pipeline"""

    @abstractmethod
    def read_image(self, path: str) -> None:
        """Reads the image from disk."""
        pass

    @abstractmethod
    def write_image(self, path: str) -> None:
        """Writes the image to disk."""
        pass

    @abstractmethod
    def process_image(self) -> None:
        """Processes the image, could call preprocess, upscale, and postprocess."""
        pass
