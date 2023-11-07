from __future__ import annotations
from typing import TYPE_CHECKING
import gc
import math
from PIL import ImageFile
from wand.image import Image
from utils import *
from utils.logging import write_log_to_file, log_file
from utils.image_container import ImageContainer

from model.utils import *

ImageFile.LOAD_TRUNCATED_IMAGES = True

if TYPE_CHECKING:
    from utils import imTypes
    from gui.frames.export_frame import ExportThread, ExportFrame


def get_cuda_device_memory(device: int):
    """
    Retrieves memory available on respective cuda device
    returns float value representing available VRAM in GiB (with increments being in 10s of MiB)
    """
    return round(torch.cuda.get_device_properties(device).total_memory / 1024**3, 2)


def load_model(device, scale, load: bool = True):
    """
    Loads the Generator model architecture and respective inference weights.
    """
    from model import RESRGAN

    model = RESRGAN(device=device, scale=scale)
    if load:
        model.load_weights(os.path.join(ExportConfig.weight_file, f"{scale}x.pth"))
    return model.gen


def process_export_location(
    export_config: Dict[str, Union[str, int, float, bool]], master: ctk.CTkFrame
):
    if (
        not export_config["export_to_original"]
        and export_config["single_export_location"] == ""
    ):
        write_log_to_file(
            "ERROR",
            f"No export location defined: \n\tOriginal export location: {export_config['export_to_original']} \n\tSingle export location: {export_config['single_export_location']}",
            log_file,
        )
        warning_mssg = True if master else False
        process = False


# TODO: implement
def handle_alpha(
    rgb_img: Image, rgb_alpha, optimize: bool, bl: int, br: float, co: float, file: str
):
    not_impletemented = True
    if not_impletemented:
        raise NotImplementedError
    # convert alphamap to 8bit greyscale to increase processing speed (it's greyscale only)
    # greyscale_alpha = rgb_alpha.convert("L")
    greyscale_alpha = rgb_alpha
    # only perform this if alpha optimizations are desired
    if optimize:
        # apply gaussian blur
        if bl != 0:
            greyscale_alpha = greyscale_alpha.filter(ImageFilter.GaussianBlur(bl))
        # apply brightness
        if br != 0.0:
            greyscale_alpha = ImageEnhance.Brightness(greyscale_alpha).enhance(1.0 + br)
        # apply contrast
        if co != 0.0:
            greyscale_alpha = ImageEnhance.Contrast(greyscale_alpha).enhance(1.0 + co)

    greyscale_alpha.save(os.path.join("results", "test_POST_alpha_" + file))
    # merge alpha channel with RGB
    return rgb_img


def calc_mipmaps(user_choice: str, image: Image):
    """
    Calculates the maximum possible mip levels for an image
    given its dimensions then sets the level to the lesser of
    (1) the user's choice or (2) the maximum level
    """
    if user_choice == "max":
        user_choice = float(1)
    else:
        user_choice = float(user_choice[:-1]) / 100
    limiting_dim = math.log2(min(image.size))
    return str(round(user_choice * limiting_dim, 0))


def handle_mipmaps(mipmaps: dict, img: torch.Tensor):
    # if export_config["exrpot_format"] == "dds":
    if not mipmaps == "none":
        num_mipmaps = calc_mipmaps(mipmaps, img)
        img.options["dds:mipmaps"] = num_mipmaps
    else:
        img.options["dds:mipmaps"] = "0"


def handle_naming(export_config: dict[str, Any], im_name, index):
    id = (str(index) + "_") if export_config["numbering"] else ""
    prefix = export_config["prefix"] + ("_" if export_config["prefix"] != "" else "")
    suffix = (("_" if export_config["suffix"] != "" else "")) + export_config["suffix"]
    format = export_config["export_format"]
    im_name = f"{id}{prefix}{im_name[:-4]}{suffix}.{format}"
    return im_name


def handle_dimensions(
    img: imTypes, im_name: str, im_type: str, log_file: TextIOWrapper
) -> imTypes:
    if im_type == "Numpy":
        shape = list(img.shape)
    elif im_type == "PIL":
        shape = img.size

    changed = False
    if shape[0] % 2 != 0:
        shape[0] += 1
        changed = True
    if shape[1] % 2 != 0:
        shape[1] += 1
        changed = True

    if changed:
        write_log_to_file(
            "WARNING",
            f"Reshaped image {im_name} to dimensions {shape[0]}x{shape[1]} to allow for processing. Please double-check that this has not affected the UV mapping.",
            log_file,
        )
        img = (
            img.resize(tuple(shape))
            if type(img) == np.array
            else cv2.resize(src=img, dsize=shape[:2], interpolation=cv2.INTER_LANCZOS4)
        )
    return img


def handle_unprocessed_images(unprocessed_list):
    return "\n" + "\n".join(
        [
            f" - {unprocessed_list[i][0]} >> {unprocessed_list[i][1]}"
            for i in range(len(unprocessed_list))
        ]
    )


def unsharp_mask(
    image: np.ndarray,
    kernel_size: tuple = (5, 5),
    sigma: float = 1.0,
    amount: float = 1.0,
    threshold: float = 0,
    dtype: str = "uint8",
):
    """
    Return a sharpened version of the image, using an unsharp mask.
    Credit: Soroush (2019). https://stackoverflow.com/questions/4993082/how-can-i-sharpen-an-image-in-opencv.
    """
    scale_ = {
        "uint8": 255,
        "uint16": 65535,
        "float16": 1.0,
        "float32": 1.0,
        "float64": 1.0,
    }[dtype]
    blurred = cv2.GaussianBlur(image, kernel_size, sigma)
    sharpened = float(amount + 1) * image - float(amount) * blurred
    sharpened = np.maximum(sharpened, np.zeros(sharpened.shape))
    sharpened = np.minimum(sharpened, scale_ * np.ones(sharpened.shape))
    sharpened = sharpened.round().astype(dtype)
    if threshold > 0:
        low_contrast_mask = np.absolute(image - blurred) < threshold
        np.copyto(sharpened, image, where=low_contrast_mask)
    return sharpened


def handle_noise(
    noisy_image: np.ndarray,
    denoised_image: np.ndarray,
    factor: int,
    noise_factor: float,
    dtype: "str",
):
    scale_ = {
        "uint8": 255,
        "uint16": 65535,
        "float32": 1.0,
    }[dtype]
    if factor == 1:
        denoised_image = denoised_image / scale_
    noisy_image = unsharp_mask(
        cv2.resize(
            src=noisy_image,
            dsize=tuple(dim * factor for dim in noisy_image.shape[:2][::-1]),
            interpolation=cv2.INTER_LANCZOS4,
        )
    )
    # A more sophisticated algorithm can be used to retain only the lightest/darkest patterns in the original texture and add them back as noise to the AI-upscaled texture
    img = noisy_image * (noise_factor) + denoised_image * scale_ * (1 - noise_factor)
    return img / scale_


def handle_downscaling(image: np.ndarray) -> np.ndarray:
    orig_dtype = image.dtype
    image = cv2.resize(
        src=image.astype("float32" if orig_dtype == "float16" else orig_dtype),
        dsize=tuple(int(dim * 0.5) for dim in image.shape[:2][::-1]),
        interpolation=cv2.INTER_LANCZOS4,
    )
    return image


def handle_channel_order(
    img: np.array, read_format: str, write_format: str
) -> np.ndarray:
    if read_format in confref.opencv_formats:
        if not confref.write_lib_map[write_format] == "opencv":
            img[..., :3] = img[..., 2::-1]
    else:
        if confref.write_lib_map[write_format] == "opencv":
            img[..., :3] = img[..., 2::-1]
    return img


def setup_generator(
    export_config: Union[Dict[str, Union[str, int, bool]], None], generator: Generator
):
    scale = confref.scale_map[export_config["scale"]]
    if scale != 1:
        if scale != 0.5:
            try:
                generator = (
                    load_model(
                        device=export_config["device"],
                        scale=scale,
                    )
                    if generator == None
                    else generator
                )
                generator.eval() if export_config[
                    "upscale_precision"
                ] == "high" else generator.eval().half()
                torch.cuda.set_per_process_memory_fraction(confref.limit_vram_value, 0)
            except (
                Exception
            ) as e:  # this will raise an error related to lacking weight (.pth) files or missing Cuda .libs
                write_log_to_file(
                    "Error",
                    f"Failed to process selected image(s) due to: \n\t{e}\n",
                    log_file,
                )
                warning_mssg = True
                process = False
        else:
            write_log_to_file(
                "INFO",
                f"Downscaling. Chosen scale factor: {scale}",
                log_file,
            )
            generator = None
    else:
        write_log_to_file(
            "INFO",
            f"Skipping upscaling, chosen scale factor: {scale}",
            log_file,
        )
        generator = None
    return generator, scale


def handle_padding_size(size: int) -> int:
    """
    Determines the padding size for image splitting
    based on the user's setting.
    """
    # take the lesser of the dimensions since the padding size is a % that,
    # if dependent on the longer dimension, may exceed the length of the
    # shorter dimension
    pad_size = math.floor(ExportConfig.padding_size * min(size[:2]) / 2)
    pad_size = int(pad_size) if pad_size % 2 == 0 else int(pad_size + 1)
    return pad_size


def handle_image_split(channel_type: str = "color") -> Tuple[np.ndarray, int]:
    """
    Determines if the image is to be split and processed in patches based on:
        1. the maximum available vram
        2. the split_large_image flag
        3. the padding size
    Returns an array of shape (num of patches, c, h,w)
    """

    global split
    split = False  # flag used for code organization
    if channel_type == "color":
        size: Tuple[int] = img.color_channels.shape
    else:
        size: Tuple[int] = img.alpha.shape
    # 262144 the the pixel count of the image, 0.1835 (GiB)
    # is the video memory required process it. The memory
    # required for other images is:
    # w x h x scale x (vram for 512x512 image) x (pixel count of 512x512 image)

    factor: float = (1 / 262144) * scale * 2 * 0.1835
    required_vram: float = (size[0] * size[1]) * factor
    split = True if max_vram * 0.95 < required_vram else False

    if split:
        if channel_type == "color":
            confref.split_color: bool = True
        else:
            confref.split_alpha: bool = True

        if ExportConfig.split_large_image:
            pad_size: int = handle_padding_size(size)

            lr_image: np.ndarray = pad_reflect(
                img.color_channels if channel_type == "color" else img.alpha, pad_size
            )
            min_ = min(lr_image.shape[:2])
            max_ = max(lr_image.shape[:2])
            no_patches = 0
            while True:  # maximum of 50 x 50 patches
                no_patches += 1
                patch_size = (min_ / no_patches) + pad_size * 2
                if (patch_size**2) * factor < max_vram:
                    patch_size = math.ceil(min_ / no_patches)
                    break
            if not patch_size % 2 == 0:
                patch_size -= 1

            patches, p_shape = split_image_into_overlapping_patches(
                lr_image, patch_size=patch_size, padding_size=pad_size
            )
            return patches, p_shape, pad_size, size
    else:
        return (None,) * 4


def handle_patch_upscaling(
    full_image: np.ndarray,
    channel_type: str,
    generator: Generator,
    export_config: Union[Dict[str, Union[str, int, bool]], None],
) -> torch.Tensor:
    full_image, p_shape, pad_size, lr_im_shape = handle_image_split(channel_type)
    new_patches = None
    i = 0
    if type(full_image) == np.ndarray:
        for patch in full_image:
            i += 1
            if i == 1:
                new_patches = generator(
                    confref.inference_transform(image=patch)["image"]
                    .unsqueeze(0)
                    .to(export_config["device"])
                    .to(
                        dtype=confref.upscale_precision_levels[export_config["device"]][
                            export_config["upscale_precision"]
                        ][1]
                    )
                ).cpu()
            else:
                new_patches = torch.cat(
                    (
                        new_patches,
                        generator(
                            confref.inference_transform(image=patch)["image"]
                            .unsqueeze(0)
                            .to(export_config["device"])
                            .to(
                                dtype=confref.upscale_precision_levels[
                                    export_config["device"]
                                ][export_config["upscale_precision"]][1]
                            )
                        ).cpu(),
                    ),
                    dim=0,
                )
        new_patches: torch.Tensor = new_patches.permute((0, 2, 3, 1))
        padded_size_scaled: Tuple[int] = tuple(np.multiply(p_shape[:2], scale)) + (3,)
        scaled_image_shape: Tuple[int] = tuple(np.multiply(lr_im_shape[:2], scale)) + (
            3,
        )

        full_image: torch.Tensor = stitch_together(
            patches=new_patches,
            padded_image_shape=padded_size_scaled,
            target_shape=scaled_image_shape,
            padding_size=pad_size * scale,
        )
        del new_patches

        return full_image
        # return unpad_image(patches, pad_size * scale)
    else:
        return img.color_channels if channel_type == "color" else img.alpha


def scale_image(
    master: Union[ExportFrame, None],
    generator: Union[Generator, None],
    export_config: dict,
    im_name: str,
) -> None:
    """
    If a Generator object is provided, this functioncalls  the Generator.__call__(),
    which calls the Generator's .foward() method which takes an torch.Tensor object
    as input in the shape of (width,height,channels,batch size). The torch.Tensor
    object is always 3 channels and can represent color or alpha channels. If the
    Generator is not provided, the function assumes downscalin is intended.
    """
    write_log_to_file(
        "INFO",
        "Found {0} alpha channel for image: {1}, scaling RGB{2} or (Grey{3}) channels.".format(
            *("an", im_name, "A", "+ Alpha")
            if type(img.alpha) == np.ndarray
            else ("no", im_name, "", "")
        ),
        log_file,
    )
    if generator:
        # try:
        gc.collect()
        torch.cuda.empty_cache()
        torch.cuda.reset_max_memory_allocated()
        if master:
            master.print_export_logs(f"Upscaling {im_name}")
        with torch.inference_mode():
            with torch.autocast(
                device_type=export_config["device"],
                dtype=confref.upscale_precision_levels[export_config["device"]][
                    export_config["upscale_precision"]
                ][1],
            ):
                # upscaling color
                if img.upscale_color_with_generator:
                    if ExportConfig.split_large_image:
                        img.color_channels = handle_patch_upscaling(
                            img.color_channels, "color", generator, export_config
                        )
                    if (not ExportConfig.split_large_image) or (
                        not confref.split_color
                    ):
                        img.color_channels = generator(
                            confref.inference_transform(image=img.color_channels)[
                                "image"
                            ]
                            .unsqueeze(0)
                            .to(export_config["device"])
                        )[0]

                # upscaling alpha
                if img.upscale_alpha_with_generator:
                    if ExportConfig.split_large_image:
                        img.alpha = handle_patch_upscaling(
                            img.alpha, "alpha", generator, export_config
                        )
                    if (not ExportConfig.split_large_image) or (
                        not confref.split_alpha
                    ):
                        img.alpha = generator(
                            confref.inference_transform(image=img.alpha)["image"]
                            .unsqueeze(0)
                            .to(export_config["device"])
                        )[0]
        img.handle_gamma_correction(1 / export_config["gamma_adjustment"])
        img.recombine_channels()

        # except Exception as e:
        #     if type(e) == torch.cuda.OutOfMemoryError:
        #         write_log_to_file(
        #             "ERROR",
        #             f"Could not process {im_name}. There isn't enough video memory to allocate for processing the image. Try a smaller scale, or scale using CPU as the device settings \n (path: {img.trg_path}).",
        #             log_file,
        #         )
        #     else:
        #         write_log_to_file(
        #             "ERROR",
        #             f"Could not process {im_name}. The program ran into an unhandled error. \n (path: {img.trg_path})."
        #             f"ERROR: \n\n{e}\n\n",
        #             log_file,
        #         )
        #     warning_mssg = True if master else False
    # Downscale Color+Alpha
    else:
        img.handle_gamma_correction(
            1 / export_config["gamma_adjustment"]
        ).recombine_channels()
        if scale == 0.5:
            img.image = handle_downscaling(image=img.image)


def export_images(
    master: Union[ExportFrame, None],
    export_config: Union[Dict[str, Union[str, int, bool]], None],
    gen: Union[Generator, None],
    export_indices: Union[List[int], None],
    prog_bar: Union[ctk.CTkProgressBar, None],
    stop_export_button: Union[ctk.CTkButton, None],
    verbose: bool,
    task: Union[ExportThread, None],
):
    # 1. Set up variables/objects

    global warning_mssg, process, scale, max_vram, img, not_processed
    try:
        if export_indices == "all":
            export_indices = list(range(0, len(im_cache[0])))
        warning_mssg = False
        process = True

        # 2. Determine whether to process image

        if export_config == None:
            write_log_to_file(
                "ERROR", f"No export config found: {export_config}", log_file
            )
            write_log_to_file(
                "INFO",
                f"No processed \n: All images from this run have not been processed.",
                log_file,
            )
            warning_mssg, process = True, False

        process_export_location(export_config=export_config, master=master)
    except Exception as e:
        write_log_to_file(
            "ERROR",
            f"Processing export configuration and image source and export paths: \n {e}.",
            log_file,
        )

    # 3. Process image
    if process:
        try:
            not_processed = []
            tot_images = len(export_indices)
            # determine maximum vram available once before the loop to batch process images
            max_vram = (
                torch.cuda.get_device_properties(0).total_memory / (1024**3)
                if ExportConfig.device == "cuda"
                else None
            )

            # 3. b) Setup UI and processing metrics

            cache_copy = deepcopy(im_cache)
            if master:
                prog_bar.grid(row=1, column=0, sticky="w", padx=7, pady=2)
                stop_export_button.grid(row=2, column=0, sticky="we", padx=7, pady=2)
                step_size = 1 / tot_images

            start_time = time.time()
            count, progress = 0, 0
            if master:
                prog_bar.set(value=progress)

            # 3. setup generator and determine scale
            generator, scale = setup_generator(export_config, gen)
        except Exception as e:
            write_log_to_file(
                "ERROR",
                f"Ran into an issue while setting up the batch of images to process: \n {e}.",
                log_file,
            )

        for i in export_indices:
            # try:
            count += 1
            im_name, im_path = cache_copy[0][i], cache_copy[1][i]
            fp, step = os.path.join(im_path, im_name), "reading image."
            sub_time_start = time.time()

            if master:
                master.print_image_index(f"Processed/Total: {count-1}/{tot_images}")
            if not master and verbose:
                print(f"\nAttempting to process file:\n\t {fp}\n")

            if master:
                master.print_export_logs(f"Preprocessing: {im_name}")

            step = "setting up image for processing"
            img = ImageContainer(
                img_index=i,
                src_path=im_path,
                trg_path=export_config["single_export_location"]
                if not export_config["export_to_original"]
                else im_path,
                img_name=im_name,
                **export_config,
            )

            step = "attempting to scale linearly."
            img.check_all_values_equivalent()
            step = "attempting to split color and alpha channels for separate processing."
            img.split_image()
            step = "attempting to correct gamma."
            img.handle_gamma_correction(export_config["gamma_adjustment"])
            step = "converting the data type before upscaling."
            img.convert_datatype(input=True)
            step = "attempting to upscale the image with the chosen model."
            scale_image(
                master=master,
                generator=generator,
                export_config=export_config,
                im_name=im_name,
            )  # recombines color and alpha (if any) channel into a single array

            step = (
                "attempting to reconvert the back to the chosen export color depth."
            )
            # pixel values adjustments based on export color depth, export color space and gamma correction settings
            img.convert_datatype(input=False)
            step = "attempting to process export color mode."
            # write color mode (RGB, RGBA, L, LA)
            # exporting images as .dds forced RGBA
            img.image = img.handle_write_channel_mode(img.image)

            step = "applying the dds mip level workaround for the .dds image export format."
            # dds mipmap fix
            if export_config["export_format"] == "dds":
                img.apply_dds_mipmap_fix()

            # noise
            if (export_config["noise_level"] != 0.0) and (
                not img.linear_upscale_all_channels  # if the entire image is a single value, no point in noisifying
            ):
                if master:
                    master.print_export_logs(f"Processing noise for: {im_name}")
                step = "attempting to process color mode for noisy image."
                img.noisy_copy = img.handle_write_channel_mode(img.noisy_copy)
                step = "attempting to add noise."
                img.handle_noise()

            step = "attempting reverse color channels."

            # channel order for wand vs. open cv write functions
            img.handle_channel_order()

            step = "attempting to save image."
            # write
            if master:
                master.print_export_logs(f"Saving: {im_name}")
            img.write_image(master=master, verbose=verbose)

            if master:
                progress += step_size
                prog_bar.set(value=progress)
                write_log_to_file(
                    "INFO",
                    f"Processing time for image {im_name}: {round(time.time()-sub_time_start, 2)} seconds.",
                    log_file,
                )
                if task.stopped():
                    break
            split, img, warn_mssg, confref.split_color, confref.split_alpha = (
                False,
                None,
                False,
                False,
                False,
            )  # reset global variables related to the current image
            # except:
            #     not_processed.append((im_name, im_path))
            #     write_log_to_file(
            #         "ERROR",
            #         f"Ran into an issue while {step}: {im_name} ",
            #         log_file,
            #     )
            #     warning_mssg = True if master else False
            #     continue

        tot_time = round(time.time() - start_time, 2)
        write_log_to_file(
            "INFO",
            f"Total time to upscale {count} image(s): {tot_time} seconds for an average of {round(tot_time/count,2)} seconds per image.",
            log_file,
        )
        not_processed = handle_unprocessed_images(not_processed)
        write_log_to_file(
            "INFO",
            f"The following images were not written {not_processed}.",
            log_file,
        )
        task.stop()
        # sleep before removing progress bar
        time.sleep(0.5)
    if master:
        master.print_export_logs(f"")
        master.print_image_index(f"")
        prog_bar.grid_forget()
        stop_export_button.grid_forget()

    if warning_mssg:
        warn_mssg = (
            "Some files were not processed. Please refer to the latest log file."
        )
        if not master and verbose:
            print(warn_mssg)
        else:
            CTkMessagebox(
                title="Error Message!",
                width=400,
                message=warn_mssg,
                icon="warning",
                option_1="Ok",
            )
    if master:
        master.export_sub_frame.export_button.grid(
            row=1, column=0, sticky="ew", padx=85, pady=10
        )
    if not master:
        log_file.close()  # global TextIOWrapper file needs to be closed manually since the write_to_lof_file function doesn't close it


def copy_files(export_indices: Union[List[int], None] = None, copy_location: str = ""):
    # log_file = write_log_to_file(None, None, None)
    warning_mssg = False
    cache_copy = deepcopy(im_cache)
    for i in export_indices:
        im_name, im_path = cache_copy[0][i], cache_copy[1][i]
        source_img = os.path.join(im_path, im_name)
        target_img = os.path.join(copy_location, im_name)
        try:
            shutil.copyfile(source_img, target_img)
        except Exception as e:
            if type(e) == shutil.SameFileError:
                error = f"Copying a file to its source location \n\t({e})"
            else:
                error = f"Unknown \n\t({e})."

            write_log_to_file(
                "Error",
                f"Ran into an error when attempting to copy file {im_name} due to: {error} \n  (original path: {im_path})",
                log_file,
            )
            warning_mssg = True

    if warning_mssg:
        CTkMessagebox(
            title="Warning Message!",
            message=f"Some files were not copied. Please refer to the latest log file.",
            icon="warning",
            option_1="Ok",
        )
