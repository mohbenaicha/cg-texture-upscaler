import sys
from typing import Dict, Union
from tkinter import *
import customtkinter as ctk
from gui.frames.master_frame import MasterFrame
from model import export_images
from gui.frames import ExportThread
from utils.cli_utils import clean_args, parser


def main(args: Union[Dict[str, int | str | float], None]):
    if len(sys.argv) > 1:
        export_config = clean_args(args)
        export_thread = ExportThread(
            target=export_images, args=(None, export_config, None, "all", None, None, export_config.get('verbose', False))
        )
        export_thread.start()

    else:
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        master_frame = MasterFrame()
        master_frame.iconbitmap("./media/upscaler.ico")
        master_frame.mainloop()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        args = parser.parse_args()
    else:
        args= None
    main(args)