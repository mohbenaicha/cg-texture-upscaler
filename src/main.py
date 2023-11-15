import sys, os
from typing import Dict, Union
from tkinter import *
import customtkinter as ctk
from gui.frames.master_frame import MasterFrame
from utils.export_utils import export_images
from utils.cli_utils import parse_args, parser
from utils.logging import log_file, write_log_to_file
from gui.frames import ExportThread
from gui.message_box import CTkMessagebox




def main(args: Union[Dict[str, int | str | float], None]):
    ''' Main program driver that executes a GUI loop or initiates an export
    thread based on the user's parsed and cleaned command line parameters.'''
    if len(sys.argv) > 1:
        export_config = parse_args(args)
        export_thread = ExportThread(
            target=export_images, args=(None, export_config, None, "all", None, None, export_config.get('verbose', False))
        )
        export_thread.start()

    else:
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        master_frame = MasterFrame()
        try:
            master_frame.iconbitmap("./media/upscaler.ico")
        except:
            write_log_to_file("Error", "Failed to launch, missing or faulty media: upscaler.ico", log_file)
            warn = CTkMessagebox(
                title="Error!",
                message=f"Failed to launch, missing or faulty media: upscaler.ico",
                icon="warning",
                option_1="Ok"
            )
            if warn.get() == "Ok":
                sys.exit(1)
            else:
                sys.exit(1)

        master_frame.mainloop()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        args = parser.parse_args()
    else:
        args= None
    main(args)
