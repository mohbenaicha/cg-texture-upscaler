from typing import TYPE_CHECKING
import numpy as np
import torch
from utils.image_utilities.interfaces import IImageUpscaler
from utils.logger import write_log_to_file, log_to_interface
from utils.image_utilities.patch_upscale_strategy import (
    PatchUpscalingStrategy,
    RegularUpscalingStrategy,
)
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
        container: "ImageContainer",
        master_frame: "MasterFrame",
        generator: "Generator",
    ):
        self.master_frame = master_frame
        self.generator = generator
        self.container = container
        self.image_config = self.container.config

    def scale_image(self) -> None:
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
                    ("an", self.image_config.src_image_name, "A", "+ Alpha")
                    if type(self.container.alpha) == np.ndarray
                    else ("no", self.image_config.src_image_name, "", "")
                )
            ),
        )

        patch_upscale_strategy = (
            PatchUpscalingStrategy(self.container, self.image_config)
            if ExportConfig.split_large_image
            else RegularUpscalingStrategy(
                self.container, self.image_config
            )
        )

        if self.generator:
            try:
                # determine sort cuda memory allocation if gpu-based upscaling is chosen
                device = self.image_config.device
                print("Got past set update in upscaler for loggin patching strategy")
                self.container.step.update_step(
                    "attempting to upscale image according to {0}.".format(
                        "'split image into patches'"
                        if ExportConfig.split_large_image
                        else "'full image upscaling'"
                    )
                )
                log_to_interface(
                    self.master_frame, f"Upscaling {self.image_config.src_image_name}"
                )

                with torch.inference_mode():
                    if device == "cuda":
                        with torch.autocast(
                            device_type="cuda",
                            dtype=self.image_config.upscale_precision[1],
                        ):
                            # upscaling color
                            print(
                                "ExportConfig.split_large_image: ",
                                ExportConfig.split_large_image,
                            )
                            print(
                                "self.image_config.upscale_color_with_generator: ",
                                self.image_config.upscale_color_with_generator,
                            )
                            print(
                                "self.image_config.upscale_alpha_with_generator: ",
                                self.image_config.upscale_alpha_with_generator,
                            )
                            if self.image_config.upscale_color_with_generator:
                                print(
                                    ".....................determine_color_image_split....................."
                                )
                                print("1")
                                print(
                                    "ConfigReference.split_color: ",
                                    ConfigReference.split_color,
                                )
                                print("2")
                                if ConfigReference.split_color:
                                    print("3")
                                    print("Patch color upscaling...")
                                    self.container.color_channels = (
                                        patch_upscale_strategy.upscale(
                                            self.container.color_channels,
                                            "color",
                                            self.generator,
                                        )
                                    )
                                    print("4")
                                else:
                                    print("5")
                                    print("Full color upscaling...")
                                    self.container.color_channels = self.generator(
                                        ConfigReference.inference_transform(
                                            image=self.container.color_channels
                                        )["image"]
                                        .unsqueeze(0)
                                        .to("cuda")
                                    )[0]
                                    print("6")

                            # upscaling alpha
                            if self.image_config.upscale_alpha_with_generator:
                                print(
                                    ".....................determine_alpha_image_split....................."
                                )
                                print(
                                    "ConfigReference.split_alpha: ",
                                    ConfigReference.split_alpha,
                                )
                                if ConfigReference.split_alpha:
                                    print("Patch alpha upscaling alpha...")
                                    self.container.alpha = (
                                        patch_upscale_strategy.upscale(
                                            self.container.alpha,
                                            "alpha",
                                            self.generator,
                                        )
                                    )
                                else:
                                    print("Full alpha upscaling alpha...")
                                    self.container.alpha = self.generator(
                                        ConfigReference.inference_transform(
                                            image=self.container.alpha
                                        )["image"]
                                        .unsqueeze(0)
                                        .to("cuda")
                                    )[0]

                    else:  # float32 precision cpu upscaling
                        if self.image_config.upscale_color_with_generator:
                            self.container.color_channels = self.generator(
                                ConfigReference.inference_transform(
                                    image=self.container.color_channels
                                )["image"]
                                .unsqueeze(0)
                                .to(device="cpu", dtype=torch.float32)
                            )[0]
                        if self.image_config.upscale_alpha_with_generator:
                            self.container.alpha = self.generator(
                                ConfigReference.inference_transform(
                                    image=self.container.alpha
                                )["image"]
                                .unsqueeze(0)
                                .to(device="cpu", dtype=torch.float32)
                            )[0]
            except Exception as e:
                if type(e) == torch.cuda.OutOfMemoryError:
                    write_log_to_file(
                        "ERROR",
                        f"Could not process {self.image_config.src_image_name}. There isn't enough video memory to allocate for processing the image. Use the Split and Recombine Large Images feature , or scale using CPU as the device settings \n (path: {self.image_config.trg_path}).",
                    )
                else:
                    write_log_to_file(
                        "ERROR",
                        f"Could not process {self.image_config.src_image_name}. The program ran into an unhandled error. \n (path: {self.image_config.trg_path})."
                        f"ERROR: \n\n{e}\n\n",
                    )
