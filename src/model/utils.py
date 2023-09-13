import os
import shutil
from datetime import date, datetime
import time
import math
import customtkinter as ctk
from PIL import Image, UnidentifiedImageError, ImageFilter, ImageEnhance
from copy import deepcopy
import numpy as np
import torch

from gui.message_box import CTkMessagebox
from typing import List, Dict, Union
from wand.image import Image as wand_image
from utils.events import enable_UI_elements
from .rrdbnet_arch import Generator
from caches.cache import image_paths_cache as im_cache
from app_config.config import (PrePostProcessingConfig as ppconf, ExportConfig)

def pad_reflect(image, pad_size):
    imsize = image.shape
    height, width = imsize[:2]
    new_img = np.zeros([height + pad_size * 2, width + pad_size * 2, imsize[2]]).astype(
        np.uint8
    )
    new_img[pad_size:-pad_size, pad_size:-pad_size, :] = image

    new_img[0:pad_size, pad_size:-pad_size, :] = np.flip(
        image[0:pad_size, :, :], axis=0
    )  # top
    new_img[-pad_size:, pad_size:-pad_size, :] = np.flip(
        image[-pad_size:, :, :], axis=0
    )  # bottom
    new_img[:, 0:pad_size, :] = np.flip(
        new_img[:, pad_size : pad_size * 2, :], axis=1
    )  # left
    new_img[:, -pad_size:, :] = np.flip(
        new_img[:, -pad_size * 2 : -pad_size, :], axis=1
    )  # right

    return new_img


def unpad_image(image, pad_size):
    return image[pad_size:-pad_size, pad_size:-pad_size, :]


def write_log_to_file(log_type, message, log_file=None):
    if not log_file:
        if not os.path.exists("logs"):
            os.mkdir("logs")

        if not os.path.exists(
            os.path.join("logs", f"log-{date.today().strftime('%d-%m-%Y')}.txt")
        ):
            log_file = open(
                os.path.join("logs", f"log-{date.today().strftime('%d-%m-%Y')}.txt"),
                "w",
            )
        else:
            log_file = open(
                os.path.join("logs", f"log-{date.today().strftime('%d-%m-%Y')}.txt"),
                "a",
            )
        return log_file

    log_file.write(f"[{log_type}] - {datetime.now().strftime('%H:%M:%S')}: {message}\n")

    return log_file


# TODO: implement
def handle_alpha(rgb_img: Image, rgb_alpha, optimize, bl, br, co, file):
    not_impletement = True
    if not_impletement:
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


def calc_mipmaps(user_choice, image):
    if user_choice == "max":
        user_choice = float(1)
    else:
        user_choice = float(user_choice[:-1]) / 100
    limiting_dim = math.log2(min(image.size))
    return str(round(user_choice * limiting_dim, 0))


def handle_mipmaps(export_config, img):
    if export_config["format"] == "dds":
        if not export_config["mipmaps"] == "none":
            num_mipmaps = calc_mipmaps(export_config["mipmaps"], img)
            img.options["dds:mipmaps"] = num_mipmaps
        else:
            img.options["dds:mipmaps"] = "0"


def handle_naming(export_config, im_name, index):
    id = (str(index) + "_") if export_config["numbering"] else ""
    prefix = export_config["prefix"] + ("_" if export_config["prefix"] != "" else "")
    suffix = (("_" if export_config["suffix"] != "" else "")) + export_config["suffix"]
    format = export_config["format"]
    im_name = f"{id}{prefix}{im_name[:-4]}{suffix}.{format}"
    return im_name


def load_model(device, scale, load:bool=True):
    from model import RESRGAN

    model = RESRGAN(device=device, scale=scale)
    if load:
        model.load_weights(os.path.join(ExportConfig.weight_file, f"{scale}x.pth"))
    return model.gen


def handle_dimensions(img, im_name, log_file):
    shape: List[int] = list(img.size)
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
        img = img.resize(tuple(shape))
    return img


def export_images(
    master: ctk.CTkFrame = None,
    export_config: Union[Dict[str, Union[str, int, bool]], None] = None,
    gen: Union[Generator, None] = None,
    export_indices: Union[List[int], None] = None,
    prog_bar=None,
    stop_export_button=None,
    verbose=False,
    task=None,
):
    if export_indices == "all":
        export_indices = list(range(0, len(im_cache[0])))
    log_file = write_log_to_file(None, None, None)
    warning_mssg = False
    process = True
    # while not kill_thread:
    if export_config == None:
        write_log_to_file("ERROR", f"No export config found: {export_config}", log_file)
        warning_mssg = True
        process = False

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
    print("processing...")
    if process:
        cache_copy = deepcopy(im_cache)

        if master:
            prog_bar.grid(row=1, column=0, sticky="w", padx=7, pady=2)
            stop_export_button.grid(row=2, column=0, sticky="we", padx=7, pady=2)
            step_size = 1 / len(export_indices)

        start_time = time.time()
        count, alpha_count, progress = 0, 0, 0
        if master:
            prog_bar.set(value=progress)

        if export_config["scale"] != "none":
            try:
                generator = (
                    load_model(
                        device=export_config["device"],
                        scale=int(export_config["scale"][:1]),
                    )
                    if gen == None
                    else gen
                )
                generator.eval()
            except Exception as e:
                warning_mssg = True
                write_log_to_file(
                    "Error",
                    f"Failed to process selected image(s) due to: \n\t{e}\n",
                    log_file,
                )
                process = False  # no saved_model directory/generator weights found

        else:
            write_log_to_file(
                "INFO",
                f"Skipping upscaling, chosen scale factor: {export_config['scale']}",
                log_file,
            )
            generator = None

        if process:
            print("processing...")
            for i in export_indices:
                im_name, im_path = cache_copy[0][i], cache_copy[1][i]
                img = os.path.join(im_path, im_name)
                sub_time_start = time.time()
                count += 1

                try:
                    if not master and verbose:
                        print(f"\nAttempting to process file:\n\t {img}\n")
                    im_obj = Image.open(img)
                except Exception as e:
                    if type(e) == UnidentifiedImageError:
                        write_log_to_file(
                            "Error",
                            f"Could not process file {im_name} since it is not a recognized image format: \n (path: {img}).",
                            log_file,
                        )
                    else:
                        write_log_to_file(
                            "Error",
                            f"Could not process file {im_name} due to an unhandled exception: \n (path: {img}).",
                            log_file,
                        )
                    warning_mssg = True if master else False
                    continue

                im_obj = handle_dimensions(im_obj, im_name, log_file)

                if generator:
                    try:
                        if im_obj.mode in ("RGBA", "LA") or (
                            im_obj.mode == "P" and "transparency" in im_obj.info
                        ):
                            alpha_count += 1
                            alpha = im_obj.split()[-1].convert("RGB")
                            im_obj = im_obj.convert("RGB")

                            with torch.no_grad():
                                write_log_to_file(
                                    "INFO",
                                    f"Found an alpha channel for image: {im_name}, scaling RGBA channels.",
                                    log_file,
                                )
                                upscaled_img = generator(
                                    ppconf.test_transform(image=np.asarray(im_obj))[
                                        "image"
                                    ]
                                    .unsqueeze(0)
                                    .to(export_config["device"])
                                )[0]

                                upscaled_alpha = generator(
                                    ppconf.test_transform(image=np.asarray(alpha))[
                                        "image"
                                    ]
                                    .unsqueeze(0)
                                    .to(export_config["device"])
                                )[0]
                                alpha_to_greyscale = (
                                    upscaled_alpha[0] * (0.2989)
                                    + upscaled_alpha[1] * (0.5870)
                                    + upscaled_alpha[2] * (0.1140)
                                )
                                upscaled_img = torch.cat(
                                    [upscaled_img, alpha_to_greyscale.unsqueeze(0)],
                                    0,
                                )

                        else:
                            write_log_to_file(
                                "INFO",
                                f"Found no alpha channel for image: {im_name}, only scaling RGB channels.",
                                log_file,
                            )
                            with torch.no_grad():
                                upscaled_img = generator(
                                    ppconf.test_transform(
                                        image=np.asarray(im_obj.convert("RGB"))
                                    )["image"]
                                    .unsqueeze(0)
                                    .to(export_config["device"])
                                )[0]
                        img_arr = upscaled_img.permute(1, 2, 0).detach().cpu().numpy()

                    except Exception as e:
                        if type(e) == torch.cuda.OutOfMemoryError:
                            write_log_to_file(
                                "ERROR",
                                f"Could not process {img}. There isn't enough video memory to allocate for processing the image. Try a smaller scale, or scale using CPU as the device settings \n (path: {img}).",
                                log_file,
                            )
                        else:
                            write_log_to_file(
                                "ERROR",
                                f"Could not process {img}. The program ran into an unhandled error. \n (path: {img})."
                                f"ERROR: \n\n{e}\n\n",
                                log_file,
                            )
                        warning_mssg = True if master else False
                        continue
                else:
                    img_arr = np.asarray(im_obj)

                # a workaroud so wand's mip map generation doesn't eliminate RGB information on the mipmaps where alpha = 0 on the original full scale layer
                # adding a 1 to the pixel value seems incosequential for the opacity and RGB channels

                if export_config["mipmaps"] != "none":
                    img_arr = np.copy(img_arr)
                    img_arr[np.where(img_arr == 0)] += 1

                with wand_image.from_array(img_arr) as img:
                    img.format = export_config["format"]
                    img.compression = export_config["compression"] if not export_config["compression"] == "none" else "no"
                    handle_mipmaps(export_config, img)
                    im_name = handle_naming(export_config, im_name, i)

                    if export_config["export_to_original"]:
                        save_path = os.path.join(im_path, im_name)
                    else:
                        save_path = os.path.join(
                            export_config["single_export_location"], im_name
                        )
                    img.save(filename=save_path)
                    write_log_to_file(
                        "INFO", f"Saved {im_name} to {save_path}", log_file
                    )
                    # print(f"saved current {im_name} to {save_path}")
                    if not master and verbose:
                        print(f"\n[INFO] Saved {im_name} to {save_path}\n")
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

            tot_time = round(time.time() - start_time, 2)
            write_log_to_file(
                "INFO",
                f"Total time to upscale {count} image(s): {tot_time} seconds for an average of {round(tot_time/count,2)} seconds per image ({alpha_count} total image(s) had alpha channel information).",
                log_file,
            )
            task.stop()
            # sleep before removing progress bar
            time.sleep(0.5)
        if master:
            prog_bar.grid_forget()
            stop_export_button.grid_forget()

    if warning_mssg:
        warn_mssg = (
            f"Some files were not processed. Please refer to the latest log file. \n\nPlease ensure you have: \n\n"
            f" 1. You (or your anti-virus) haven't tampered with the saved_model directory if upscaling. \n "
            f" 2. Ensure the weight files 2x and/or 4x exist for the upscaling factor you wish to use, if upscaling. \n "
            f" 3. You aren't trying to process a file that is not an image. \n "
            f" 4. This application has read and write permissions from and/to the source/target directories. \n "
            f" 5. There is sufficient video memory and disk space to process and save the images, if upscaling. \n "
        )
        CTkMessagebox(
            title="Error Message!",
            width=400,
            message=warn_mssg,
            icon="warning",
            option_1="Ok",
        )
        if not master and verbose:
            print(warn_mssg)
    if master != None:
        enable_UI_elements(master.export_sub_frame.export_button)


def copy_files(export_indices: Union[List[int], None] = None, copy_location: str = ""):
    log_file = write_log_to_file(None, None, None)
    warning_mssg = False
    cache_copy = deepcopy(im_cache)
    for i in export_indices:
        im_name, im_path = cache_copy[0][i], cache_copy[1][i]
        source_img = os.path.join(im_path, im_name)
        target_img = os.path.join(copy_location, im_name)
        try:
            shutil.copyfile(source_img, target_img)
        except Exception as e:
            write_log_to_file(
                "Error",
                f"Ran into an error when attempting to copy file {im_name}\n  (path: {im_path})",
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
