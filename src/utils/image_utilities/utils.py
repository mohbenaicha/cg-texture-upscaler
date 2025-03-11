from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from utils.image_utilities.orchestrator import ImageContainer



def determine_if_alpha_is_0(image_conatiner: ImageContainer) -> None:
    # TODO: automatic not working consistently
    if ("A" in image_conatiner.config.mode) and (image_conatiner.config.compression == "automatic"):
        max_, min_ = (
            image_conatiner.image.transpose(2, 0, 1)[-1].max(),
            image_conatiner.image.transpose(2, 0, 1)[-1].min(),
        )
        image_conatiner.config.alpha_0 = True if max_ == min_ == 255 else False
    elif not "A" in image_conatiner.config.mode:
        image_conatiner.config.alpha_0 = True