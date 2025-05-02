from __future__ import annotations
from typing import TYPE_CHECKING
import gc
from PIL import ImageFile
from wand.image import Image
# from utils.image_utilities.patch_upscale_strategy import *
from utils.patch_upscale_strategy import *
from utils import *
from utils.logger import write_log_to_file, log_to_interface
from utils.image_container import ImageContainer
from utils.image_utilities.orchestrator import ImageContainer as Container

from model.utils import *

ImageFile.LOAD_TRUNCATED_IMAGES = True

if TYPE_CHECKING:
    from utils import imTypes
    from gui.frames.export_frame import ExportThread, ExportFrame


# TODO: deprecate
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
        )
        warning_mssg = True if master else False
        process = False


# TODO: deprecate
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

# TODO: deprecate
def handle_naming(export_config: dict[str, Any], im_name, index):
    id = (str(index) + "_") if export_config["numbering"] else ""
    prefix = export_config["prefix"] + ("_" if export_config["prefix"] != "" else "")
    suffix = (("_" if export_config["suffix"] != "" else "")) + export_config["suffix"]
    format = export_config["export_format"]
    im_name = f"{id}{prefix}{im_name[:-4]}{suffix}.{format}"
    return im_name

# TODO: deprecate
def handle_dimensions(img: imTypes, im_name: str, im_type: str) -> imTypes:
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
        )
        img = (
            img.resize(tuple(shape))
            if type(img) == np.array
            else cv2.resize(src=img, dsize=shape[:2], interpolation=cv2.INTER_LANCZOS4)
        )
    return img


def handle_unprocessed_images(unprocessed_list):
    if len(unprocessed_list) == 0:
        return "all_processed"
    else:
        return "\n" + "\n".join(
            [
                f" - {unprocessed_list[i][0]} > > > {unprocessed_list[i][1]}"
                for i in range(len(unprocessed_list))
            ]
        )

# TODO: deprecate
def unsharp_mask(
    image: np.ndarray,
    kernel_size: tuple = (5, 5),
    sigma: float = 1.0,
    amount: float = 1.0,  #
    threshold: float = 0,  # 0 to 1
    input_dtype: str = "uint8",
):
    """
    Return a sharpened version of the image, using an unsharp mask.
    This is a modified version of Soroush (2019) that incorporates various color depth adjustments and condenses some operations .
    Comments have been added for clarification of the steps.
    Credit: Soroush (2019). https://stackoverflow.com/questions/4993082/how-can-i-sharpen-an-image-in-opencv.
    """
    scale_ = {
        "uint8": 255,
        "uint16": 65535,
        "float16": 1.0,
        "float32": 1.0,
        "float64": 1.0,
    }
    blurred = cv2.GaussianBlur(image, kernel_size, sigma)
    sharpened = (
        float(amount + 1) * image - float(amount) * blurred
    )  # combine a ratio of the original image and blurred image; the blurry image is generated using a guassian distribution
    sharpened = np.clip(sharpened, 0, scale_[input_dtype])

    sharpened = sharpened.astype(input_dtype)
    if threshold > 0:
        # don't sharpen pixel values less than the threshold
        low_contrast_mask = (
            np.absolute(image - blurred) < threshold * scale_[input_dtype]
        )  # yields array of true/false values
        np.copyto(
            sharpened, image, where=low_contrast_mask
        )  # restore the original pixel values where the threshold holds
    return sharpened

# TODO: deprecate
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

# TODO: deprecate
def handle_downscaling(image: np.ndarray) -> np.ndarray:
    orig_dtype = image.dtype
    image = cv2.resize(
        src=image.astype("float32" if orig_dtype == "float16" else orig_dtype),
        dsize=tuple(int(dim / 2) for dim in image.shape[:2][::-1]),
        interpolation=cv2.INTER_LANCZOS4,
    )
    if len(image.shape) == 2:
        image = np.expand_dims(image, 2)
    return image

# TODO: deprecate
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

# TODO: deprecate
def setup_generator(
    export_config: Union[Dict[str, Union[str, int, bool]], None], generator: Generator
):
    scale = confref.scale_map[export_config["scale"]]
    if scale != 1:
        if scale != 0.5:
            try:
                if generator == None:
                    generator = load_model(device=export_config["device"], scale=scale)

                if (
                    export_config["upscale_precision"] != "high"
                    and export_config["device"] != "cpu"
                ):
                    generator.half()

                if export_config["device"] == "cuda":
                    torch.cuda.set_per_process_memory_fraction(
                        confref.limit_vram_value, 0
                    )

            except (
                Exception
            ) as e:  # this will raise an error related to lacking weight (.pth) files or missing Cuda .libs
                write_log_to_file(
                    "Error",
                    f"Failed to process selected image(s) due to an error in setting up the Generator model: \n\t{e}\n",
                )
                warning_mssg = True
                process = False
        else:
            write_log_to_file(
                "INFO",
                f"Downscaling. Chosen scale factor: {scale}",
            )
            generator = None
    else:
        write_log_to_file(
            "INFO",
            f"Skipping upscaling, chosen scale factor: {scale}",
        )
        generator = None
    return generator, scale

# TODO: deprecate
def handle_upscaling(
    full_image: np.ndarray,
    channel_type: str,
    generator: Generator,
    export_config: dict,
    strategy: UpscalingStrategy,
) -> torch.Tensor:
    return strategy.upscale(full_image, channel_type, generator, export_config)


# TODO: deprecate
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
            *(
                ("an", im_name, "A", "+ Alpha")
                if type(container.alpha) == np.ndarray
                else ("no", im_name, "", "")
            )
        ),
    )
    patch_upscale_strategy = (
        PatchUpscalingStrategy()
        if ExportConfig.split_large_image
        else RegularUpscalingStrategy()
    )


    if generator:
        try:
            # determine sort cuda memory allocation if gpu-based upscaling is chosen
            device = export_config["device"]
            if master:
                master.print_export_logs(f"Upscaling {im_name}")
            with torch.inference_mode():
                if device == "cuda":
                    with torch.autocast(
                        device_type=device,
                        dtype=confref.upscale_precision_levels[device][
                            export_config["upscale_precision"]
                        ][1],
                    ):
                        # upscaling color
                        if container.upscale_color_with_generator:

                            container.color_channels = patch_upscale_strategy.upscale(
                                container, "color", generator, export_config, scale
                            )
                            if (not ExportConfig.split_large_image) or (
                                not confref.split_color
                            ):
                                container.color_channels = generator(
                                    confref.inference_transform(
                                        image=container.color_channels
                                    )["image"]
                                    .unsqueeze(0)
                                    .to(export_config["device"])
                                )[0]

                        # upscaling alpha
                        if container.upscale_alpha_with_generator:
                            container.alpha = patch_upscale_strategy.upscale(
                                container, "alpha", generator, export_config, scale
                            )
                            if (not ExportConfig.split_large_image) or (
                                not confref.split_alpha
                            ):
                                container.alpha = generator(
                                    confref.inference_transform(image=container.alpha)[
                                        "image"
                                    ]
                                    .unsqueeze(0)
                                    .to(export_config["device"])
                                )[0]

                else:
                    if container.upscale_color_with_generator:
                        container.color_channels = generator(
                            confref.inference_transform(image=container.color_channels)[
                                "image"
                            ]
                            .unsqueeze(0)
                            .to(device=device, dtype=torch.float32)
                        )[0]
                    if container.upscale_alpha_with_generator:
                        container.alpha = generator(
                            confref.inference_transform(image=container.alpha)["image"]
                            .unsqueeze(0)
                            .to(device=device, dtype=torch.float32)
                        )[0]

                container.handle_gamma_correction(
                    1 / export_config["gamma_adjustment"]
                ).recombine_channels()
        except Exception as e:
            if type(e) == torch.cuda.OutOfMemoryError:
                write_log_to_file(
                    "ERROR",
                    f"Could not process {im_name}. There isn't enough video memory to allocate for processing the image. Use the Split and Recombine Large Images feature , or scale using CPU as the device settings \n (path: {container.trg_path}).",
                )
            else:
                write_log_to_file(
                    "ERROR",
                    f"Could not process {im_name}. The program ran into an unhandled error. \n (path: {container.trg_path})."
                    f"ERROR: \n\n{e}\n\n",
                )
            warning_mssg = True if master else False
    # Downscale Color+Alpha
    else:
        if scale == 0.5:
            if container.upscale_alpha_with_generator:
                container.alpha = handle_downscaling(image=container.alpha)
            if container.upscale_color_with_generator:
                container.color_channels = handle_downscaling(image=container.color_channels)
        container.handle_gamma_correction(
            1 / export_config["gamma_adjustment"]
        ).recombine_channels()

    

class ProcessingStep:
    """
    A class that keeps track of the processing step for error logging.
    """
    def __init__(self, step: str = ""):
        self.step = step

    def update_step(self, new_step: str):
        self.step = new_step

    def __str__(self):
        return self.step


def _export_images(
    master: Union[ExportFrame, None],
    export_config: Union[Dict[str, Union[str, int, bool]], None],
    gen: Union[Generator, None],
    export_indices: Union[List[int], None],
    prog_bar: Union[ctk.CTkProgressBar, None],
    stop_export_button: Union[ctk.CTkButton, None],
    verbose: bool,
    task: Union[ExportThread, None],
):
    """
    Handles the export of images based on the provided configuration and parameters.
    **DEPRECATION WARNING**: This function is deprecated.
    Please use `utils/export_utils.py/export_images` instead for improved functionality and maintainability.
    """
    # 1. Set up variables/objects
    global warning_mssg, process, scale, max_vram, container, not_processed
    try:
        if export_indices == "all":
            export_indices = list(range(0, len(im_cache[0])))
        warning_mssg = False
        process = True

        # 2. Determine whether to process image

        if export_config == None:
            write_log_to_file("ERROR", f"No export config found: {export_config}")
            write_log_to_file(
                "INFO",
                f"No processed \n: All images from this run have not been processed.",
            )
            warning_mssg, process = True, False

        process_export_location(export_config=export_config, master=master)
    except Exception as e:
        write_log_to_file(
            "ERROR",
            f"Processing export configuration and image source and export paths: \n {e}.",
        )

    # 3. Process image
    if process:
        step = ProcessingStep("setting up upscaling model.")
        try:
            not_processed = []
            tot_images = len(export_indices)

            if not export_config["device"] == "cpu":
                # clean up unused objects, free up unused GPU memory cached by torch but does not release memory back to the OS, resets the peak memory usage tracker for the current session
                gc.collect()
                torch.cuda.empty_cache()
                torch.cuda.reset_max_memory_allocated()
            else:
                ExportConfig.split_large_image = False
                confref.split_color = False
                confref.split_alpha = False

            # determine maximum vram available once before the loop to batch process images
            if export_config["device"] == "cuda":
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
            )

        for i in export_indices:
            try:
                count += 1
                im_name, im_path = cache_copy[0][i], cache_copy[1][i]
                fp = os.path.join(im_path, im_name)
                step.update_step(f"reading image: {im_name}")

                sub_time_start = time.time()

                log_to_interface(master, f"Processed/Total: {count-1}/{tot_images}", verbose, True)
                
                log_to_interface(master, f"\nAttempting to process file:\n\t {fp}\n", verbose)

                step.update_step("setting up image for processing.")

                container = ImageContainer(
                    img_index=i,
                    src_path=im_path,
                    trg_path=(
                        export_config["single_export_location"]
                        if not export_config["export_to_original"]
                        else im_path
                    ),
                    img_name=im_name,
                    **export_config,
                )

                step.update_step("attempting to scale linearly.")
                container.check_all_values_equivalent()
                step.update_step("attempting to split color and alpha channels for separate processing.")
                container.split_image()
                step.update_step("attempting to correct gamma.")
                container.handle_gamma_correction(export_config["gamma_adjustment"])
                step.update_step("converting the data type before upscaling.")
                container.convert_datatype(input=True)
                step.update_step("attempting to upscale the image with the chosen model")


                scale_image(
                    master=master,
                    generator=generator,
                    export_config=export_config,
                    im_name=im_name,
                )  # recombines color and alpha (if any) channel into a single array
                step.update_step("attempting to reconvert the back to the chosen export color depth.")

                # pixel values adjustments based on export color depth, export color space and gamma correction settings
                container.convert_datatype(input=False)
                step.update_step("attempting to process export color mode.")

                # write color mode (RGB, RGBA, L, LA)
                # exporting images as .dds forced RGBA
                container.image = container.handle_write_channel_mode(container.image)
                step.update_step("applying the dds mip level workaround for the .dds image export format.")

                # dds mipmap fix
                if export_config["export_format"] == "dds":
                    container.apply_dds_mipmap_fix()

                # noise
                if (
                    (not export_config["noise_level"] == 0.0)
                    and (
                        not container.linear_upscale_all_channels  # if the entire image is a single value, no point in noisifying
                    )
                    and (
                        not container.upscale_factor == 0.5
                    )  # does not support adding noise while downscaling
                ):
                    log_to_interface(master, f"Processing noise for: {im_name}", verbose)
                    step.update_step("attempting to process color mode for noisy image.")
                    container.noisy_copy = container.handle_write_channel_mode(container.noisy_copy)

                    container.handle_noise()

                step.update_step("attempting reverse color channels for image writing.")

                # channel order for wand vs. open cv write functions
                container.handle_channel_order()

                step.update_step("attempting to save image.")

                # write
                log_to_interface(master, f"Saving: {im_name}", verbose)
                container.write_image(master=master, verbose=verbose)

                if master:
                    progress += step_size
                    prog_bar.set(value=progress)
                    write_log_to_file(
                        "INFO",
                        f"Processing time for image {im_name}: {round(time.time()-sub_time_start, 2)} seconds.",
                    )
                    if task.stopped():
                        break
                _, container, warn_mssg, confref.split_color, confref.split_alpha = (
                    False,
                    None,
                    False,
                    False,
                    False,
                )

            except:
                not_processed.append((im_name, im_path))
                write_log_to_file(
                    "ERROR",
                    f"Ran into an issue while {step}: {im_name} ",
                )
                warning_mssg = True if master else False
                continue
        tot_time = round(time.time() - start_time, 2)
        write_log_to_file(
            "INFO",
            f"Total time to upscale {count} image(s): {tot_time} seconds for an average of {round(tot_time/count,2)} seconds per image.",
        )
        not_processed = handle_unprocessed_images(not_processed)
        if not not_processed == "all_processed":
            write_log_to_file(
                "INFO",
                f"The following images were not written {not_processed}.",
            )

        # clear GPU memory after export loop finishes
        if export_config["device"] == "cuda":
            torch.cuda.empty_cache()

        # end export task (kill thread)
        task.stop()
        # closing the GUI master frame writes the information on the buffer to the log file due to the overridder .destroy() method
        # the CLI version requires the log file to be manually closed after the export loop
        # sleep before removing progress bar
        if master:
            time.sleep(0.5)

    # reset GUI printout text
    if master:
        master.print_export_logs(f"")
        master.print_image_index(f"")
        prog_bar.grid_forget()
        stop_export_button.grid_forget()

    # warn user with a prompt that some files were not processed if some files fail to export
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
    # replot export button for another export task if desired
    if master:
        master.export_sub_frame.export_button.grid(
            row=1, column=0, sticky="ew", padx=85, pady=10
        )


def export_images(
    master: Union[ExportFrame, None],
    export_config: Union[Dict[str, Union[str, int, bool]], None],
    export_indices: Union[List[int], None],
    prog_bar: Union[ctk.CTkProgressBar, None],
    stop_export_button: Union[ctk.CTkButton, None],
    verbose: bool,
    task: Union[ExportThread, None],
):
    # 1. Set up variables/objects
    try:
        if export_indices == "all":
            export_indices = list(range(0, len(im_cache[0])))
        warning_mssg = False
        process = True

        # 2. Determine whether to process image

        if export_config == None:
            write_log_to_file("ERROR", f"No export config found: {export_config}")
            write_log_to_file(
                "INFO",
                f"No processed \n: All images from this run have not been processed.",
            )
            warning_mssg, process = True, False

        process_export_location(export_config=export_config, master=master)
    except Exception as e:
        write_log_to_file(
            "ERROR",
            f"Processing export configuration and image source and export paths: \n {e}.",
        )

    # 3. Process image
    if process:
        step = ProcessingStep("setting up upscaling model.")
        try:
            not_processed = []
            total_images = len(export_indices)

            if not export_config["device"] == "cpu":
                # clean up unused objects, free up unused GPU memory cached by torch but does not release memory back to the OS, resets the peak memory usage tracker for the current session
                gc.collect()
                torch.cuda.empty_cache()
                torch.cuda.reset_max_memory_allocated()
            else:
                ExportConfig.split_large_image = False
                confref.split_color = False
                confref.split_alpha = False


            # 3. b) Setup UI and processing metrics

            cache_copy = deepcopy(im_cache)
            if master:
                prog_bar.grid(row=1, column=0, sticky="w", padx=7, pady=2)
                stop_export_button.grid(row=2, column=0, sticky="we", padx=7, pady=2)
                step_size = 1 / total_images

            start_time = time.time()
            count, progress = 0, 0
            if master:
                prog_bar.set(value=progress)

        except Exception as e:
            write_log_to_file(
                "ERROR",
                f"Ran into an issue while setting up the batch of images to process: \n {e}.",
            )

        for i in export_indices:
            try:
                count += 1
                im_name, im_path = cache_copy[0][i], cache_copy[1][i]
                fp = os.path.join(im_path, im_name)
                step.update_step(f"reading image: {im_name}")

                sub_time_start = time.time()

                log_to_interface(master, f"Processed/Total: {count-1}/{total_images}", verbose, True)
                
                log_to_interface(master, f"\nAttempting to process file:\n\t {fp}\n", verbose)

                # Setup image processing orchestrator
                container = Container(
                    img_index=i,
                    src_path=im_path,
                    trg_path=(
                        export_config["single_export_location"]
                        if not export_config["export_to_original"]
                        else im_path
                    ),
                    img_name=im_name,
                    processing_step=step,
                    **export_config,
                )
                # read image
                container.read_image()
                
                # preprocess image (color mode, space, depth, gamma, channel order, noise)
                container.preprocess_image()
                
                # process image (upscale/downscale)
                container.process_image()

                # postprocess image (color mode, space, depth, gamma, channel order, noise)
                container.postprocess_image()

                # write image (naming, format, compression, etc)
                container.write_image()

                if master:
                    progress += step_size
                    prog_bar.set(value=progress)
                    write_log_to_file(
                        "INFO",
                        f"Processing time for image {im_name}: {round(time.time()-sub_time_start, 2)} seconds.",
                    )
                    if task.stopped():
                        break
                container, warn_mssg, confref.split_color, confref.split_alpha = (
                    None,
                    False,
                    False,
                    False,
                )

            except Exception as e:
                
                not_processed.append((im_name, im_path))
                write_log_to_file(
                    "ERROR",
                    f"Ran into an issue while {step}: {im_name} \n\t {e}",
                )
                warning_mssg = True if master else False
                continue
        tot_time = round(time.time() - start_time, 2)
        write_log_to_file(
            "INFO",
            f"Total time to upscale {count} image(s): {tot_time} seconds for an average of {round(tot_time/count,2)} seconds per image.",
        )
        not_processed = handle_unprocessed_images(not_processed)
        if not not_processed == "all_processed":
            write_log_to_file(
                "INFO",
                f"The following images were not written {not_processed}.",
            )

        # clear GPU memory after export loop finishes
        if export_config["device"] == "cuda":
            torch.cuda.empty_cache()

        # end export task (kill thread)
        task.stop()
        # closing the GUI master frame writes the information on the buffer to the log file due to the overridder .destroy() method
        # the CLI version requires the log file to be manually closed after the export loop
        # sleep before removing progress bar
        if master:
            time.sleep(0.5)

    # reset GUI printout text
    if master:
        master.print_export_logs(f"")
        master.print_image_index(f"")
        prog_bar.grid_forget()
        stop_export_button.grid_forget()

    # warn user with a prompt that some files were not processed if some files fail to export
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
    # replot export button for another export task if desired
    if master:
        master.export_sub_frame.export_button.grid(
            row=1, column=0, sticky="ew", padx=85, pady=10
        )
