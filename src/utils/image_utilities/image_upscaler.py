from typing import TYPE_CHECKING
import numpy as np
import torch
from utils.image_utilities.interfaces import IImageUpscaler
from utils.logger import write_log_to_file
from utils.image_utilities.patch_upscale_strategy import (
    PatchUpscalingStrategy,
    RegularUpscalingStrategy,
)
from utils.export_utils import log_to_interface
from app_config.config import ExportConfig, ConfigReference

if TYPE_CHECKING:
    from utils.image_utilities.orchestrator import ImageContainer
    from gui.frames.master_frame import MasterFrame
    from model.model import Generator


class ImageUpscaler(IImageUpscaler):
    """
    SoP class for upscaling images. Still not completely decoupled from the GAN-based upscaling method.
    """

    # TODO: decouple further in future iterations
    def __init__(
        self,
        image_container: ImageContainer,
        master_frame: MasterFrame,
        generator: Generator,
    ):
        self.master_frame = master_frame
        self.generator = generator
        self.container = image_container
        self.image_config = self.container._config

    def scale_image(self, export_config: dict) -> None:
        """
        This method calls the Generator.__call__(), which calls the Generator's .foward()
        method which takes an torch.Tensor object as input in the shape of
        (width,height,channels,batch size). The torch.Tensor object is always 3 channels
        and can represent color or alpha channels. If the Generator is not provided,
        the function assumes downscalin is intended.
        """
        write_log_to_file(
            "INFO",
            "Found {0} alpha channel for image: {1}, scaling RGB{2} or (Grey{3}) channels.".format(
                *(
                    ("an", export_config.src_image_name, "A", "+ Alpha")
                    if type(self.container.alpha) == np.ndarray
                    else ("no", export_config.src_image_name, "", "")
                )
            ),
        )

        patch_upscale_strategy = (
            PatchUpscalingStrategy()
            if ExportConfig.split_large_image
            else RegularUpscalingStrategy()
        )


        if self.generator:
            try:
                # determine sort cuda memory allocation if gpu-based upscaling is chosen
                device = export_config["device"]
                self.container.step.update_step(f"attempting to upscale image according to {0}.".format("'split image into patches'" if ExportConfig.split_large_image else "'full image upscaling'"))
                log_to_interface(self.master_frame, f"Upscaling {export_config.src_image_name}")
                
                with torch.inference_mode():
                    if device == "cuda":
                        with torch.autocast(
                            device_type=device,
                            dtype=ConfigReference.upscale_precision_levels[device][
                                export_config["upscale_precision"]
                            ][1],
                        ):
                            # upscaling color
                            if self.image_config.upscale_color_with_generator:

                                self.contianer.color_channels = (
                                    patch_upscale_strategy.upscale(
                                        self.contianer,
                                        "color",
                                        self.generator,
                                        export_config,
                                        self.image_config.scale,
                                    )
                                )
                                if (not ExportConfig.split_large_image) or (
                                    not ConfigReference.split_color
                                ):
                                    self.contianer.color_channels = self.generator(
                                        ConfigReference.inference_transform(
                                            image=self.contianer.color_channels
                                        )["image"]
                                        .unsqueeze(0)
                                        .to(export_config["device"])
                                    )[0]

                            # upscaling alpha
                            if self.image_config.upscale_alpha_with_generator:
                                self.contianer.alpha = patch_upscale_strategy.upscale(
                                    self.contianer,
                                    "alpha",
                                    self.generator,
                                    export_config,
                                    self.image_config.scale,
                                )
                                if (not ExportConfig.split_large_image) or (
                                    not ConfigReference.split_alpha
                                ):
                                    self.contianer.alpha = self.generator(
                                        ConfigReference.inference_transform(
                                            image=self.contianer.alpha
                                        )["image"]
                                        .unsqueeze(0)
                                        .to(export_config["device"])
                                    )[0]

                    else:  # float32 precision cpu upscaling
                        if self.image_config.upscale_color_with_generator:
                            self.contianer.color_channels = self.generator(
                                ConfigReference.inference_transform(
                                    image=self.contianer.color_channels
                                )["image"]
                                .unsqueeze(0)
                                .to(device=device, dtype=torch.float32)
                            )[0]
                        if self.image_config.upscale_alpha_with_generator:
                            self.contianer.alpha = self.generator(
                                ConfigReference.inference_transform(
                                    image=self.contianer.alpha
                                )["image"]
                                .unsqueeze(0)
                                .to(device=device, dtype=torch.float32)
                            )[0]
            except Exception as e:
                if type(e) == torch.cuda.OutOfMemoryError:
                    write_log_to_file(
                        "ERROR",
                        f"Could not process {export_config.src_image_name}. There isn't enough video memory to allocate for processing the image. Use the Split and Recombine Large Images feature , or scale using CPU as the device settings \n (path: {self.image_config.trg_path}).",
                    )
                else:
                    write_log_to_file(
                        "ERROR",
                        f"Could not process {export_config.src_image_name}. The program ran into an unhandled error. \n (path: {self.image_config.trg_path})."
                        f"ERROR: \n\n{e}\n\n",
                    )
