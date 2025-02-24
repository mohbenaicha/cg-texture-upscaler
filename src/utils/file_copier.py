from copy import deepcopy
from typing import Union, List
import os
import shutil
from utils.logger import write_log_to_file
from utils import im_cache
from gui.message_box import CTkMessagebox


class FileCopier:
    @staticmethod
    def copy_files(im_cache = im_cache, export_indices: Union[List[int], None] = None, copy_location: str = ""):
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
                )
                warning_mssg = True

        if warning_mssg:
            CTkMessagebox(
                title="Warning Message!",
                message=f"Some files were not copied. Please refer to the latest log file.",
                icon="warning",
                option_1="Ok",
            )