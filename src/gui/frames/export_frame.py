import os
from typing import Union
import customtkinter as ctk
from PIL import Image as pil_image
import threading
from ..message_box import CTkMessagebox
import utils.ctk_fonts as fonts
from gui.tooltips import Hovertip_Frame
import gui.tooltips.tooltip_text as ttt
from gui.frames.main_listbox_frame import TkListbox
from app_config.config import ExportConfig
from model.utils import export_images, write_log_to_file
from utils.events import (
    enable_UI_elements,
    disable_UI_elements,
    select_fof_event,
    GUIConfig,
)
from utils.validation_utils import validate_export_config


class ExportFrame(ctk.CTkFrame):
    def __init__(self, master, width: int = 1, height: int = 100, **kwargs):
        super().__init__(master)
        self.lb_frame: Union[TkListbox, None] = kwargs.get("lb_frame", None)
        # self.eo_frame:  Union[ExportOptionsFrame, None] = kwargs.get('eo_frame', None)
        self.configure(width=width, height=height)
        self.setup_ui_elements()
        self.plot_self()
        self.plot_ui_elements()

    def setup_ui_elements(self):
        self.header_label = ctk.CTkLabel(
            self, font=fonts.header_labels_font(), width=1, text="➍ Export"
        )

        self.instruct_label = ctk.CTkLabel(
            self, font=fonts.labels_font(), width=1, text="Export to a single location:"
        )

        self.selected_export_location = ctk.StringVar(
            value=ExportConfig.single_export_location
            if ExportConfig.single_export_location != None
            else ""
        )  # TODO: read from config
        self.export_to_original = ctk.BooleanVar(value=False)  # TODO: read from config
        self.fof_subframe = ctk.CTkFrame(
            master=self,
            fg_color="transparent",
            bg_color="transparent",
            width=1,
            height=25,
        )  # subframe to pack select file and folder buttons
        self.selected_fof = ctk.CTkEntry(
            self.fof_subframe,
            font=fonts.text_font(),
            width=250,
            textvariable=self.selected_export_location,
        )
        self.selected_fof.bind("<KeyRelease>", self.set_export_location)

        self.save_in_original_checkbox = ctk.CTkCheckBox(
            master=self,
            text="Save in original location",
            font=fonts.options_font(),
            variable=self.export_to_original,
            border_width=2,
            checkbox_height=15,
            width=1,
            height=15,
            checkbox_width=15,
            onvalue=True,
            offvalue=False,
            command=self.set_export_type,
        )
        self.save_in_original_checkbox_tt = Hovertip_Frame(
            anchor_widget=self.save_in_original_checkbox,
            text=ttt.original_dir,
            hover_delay=GUIConfig.tooltip_hover_delay,
            bg_color=GUIConfig.tooltip_color,
            text_color=GUIConfig.tooltop_text_color,
        )

        self.export_sub_frame = ctk.CTkFrame(
            master=self,
            fg_color="transparent",
            bg_color="transparent",
            width=1,
            height=25,
        )  # subframe to pack select file and folder buttons
        self.export_sub_frame.browse_button = ctk.CTkButton(
            self.export_sub_frame,
            text="Browse",
            font=fonts.buttons_font(),
            width=1,
            command=lambda: select_fof_event(
                master_frame=self,
                lb_frame=None,
                root_dir=self.selected_export_location,
                fof="folder",
                export=True,
            ),
        )
        self.export_sub_frame.browse_button_tt = Hovertip_Frame(
            anchor_widget=self.export_sub_frame.browse_button,
            text=ttt.browse,
            hover_delay=GUIConfig.tooltip_hover_delay,
            bg_color=GUIConfig.tooltip_color,
            text_color=GUIConfig.tooltop_text_color,
        )

        self.export_sub_frame.export_button = ctk.CTkButton(
            self.export_sub_frame,
            text="Export",
            font=fonts.export_buttons_font(),
            width=1,
            fg_color="grey",
            text_color=GUIConfig.light_theme_color,
            command=lambda: self.export_event(None),
        )

        self.export_sub_frame.export_button_tt = Hovertip_Frame(
            anchor_widget=self.export_sub_frame.export_button,
            text=ttt.export,
            hover_delay=GUIConfig.tooltip_hover_delay,
            bg_color=GUIConfig.tooltip_color,
            text_color=GUIConfig.tooltop_text_color,
        )

        self.progbar_subframe = ctk.CTkFrame(
            master=self,
            width=10,
            height=5,
            fg_color="transparent",
            bg_color="transparent",
        )
        self.progbar = ctk.CTkProgressBar(
            self.progbar_subframe,
            width=230,
            height=15,
            border_color="white",
            progress_color=(GUIConfig.dark_theme_color, GUIConfig.light_theme_color),
            bg_color="transparent",
            mode="determinate",
        )
        self.cancel_img = pil_image.open("media/cancel.png")
        self.stop_export_button = ctk.CTkButton(
            self.progbar_subframe,
            text="",
            bg_color="transparent",
            fg_color="transparent",
            width=1,
            height=1,
            image=ctk.CTkImage(
                light_image=self.cancel_img, dark_image=self.cancel_img, size=(20, 20)
            ),
            command=lambda: self.kill_export_thread(None),
        )

    def plot_self(self):
        self.grid(row=3, column=1, padx=5, pady=5, sticky="nesw")

    def plot_ui_elements(self):
        # placing labels
        self.header_label.grid(row=0, column=0, sticky="w", padx=95, pady=5)
        self.instruct_label.grid(row=2, column=0, sticky="w", padx=7, pady=1)

        # placing entry field
        self.fof_subframe.grid(row=3, column=0, sticky="ew", padx=1, pady=5)
        self.selected_fof.grid(row=1, column=1, sticky="w", padx=6, pady=1)

        # placing field subframe

        # placing buttons and subframe for buttons
        self.export_sub_frame.grid(row=4, column=0, sticky="w", padx=1, pady=1)
        self.export_sub_frame.browse_button.grid(
            row=0, column=0, sticky="w", padx=6, pady=1
        )
        self.export_sub_frame.export_button.grid(
            row=1, column=0, sticky="ew", padx=85, pady=10
        )
        # placing checkbox
        self.save_in_original_checkbox.grid(
            row=1, column=0, sticky="w", padx=7, pady=10
        )
        self.progbar_subframe.grid(row=5, column=0, sticky="w", padx=7, pady=2)

    def set_export_location(self, value):
        ExportConfig.single_export_location = self.selected_fof.get()
    
    @classmethod
    def parse_export_config(cls, config_cls):
        valid_config, error = validate_export_config(export_config=config_cls)
        if error:    
            return False
        else:
            return {
                "device": valid_config.get("device", None),
                "scale": valid_config.get("scale", None),
                "format": valid_config.get("export_format", None),
                "compression": valid_config.get("compression", None),
                "mipmaps": valid_config.get("mipmaps", None),
                "prefix": valid_config.get("save_prefix", None),
                "suffix": valid_config.get("save_suffix", None),
                "numbering": valid_config.get("save_numbering", None),
                "export_to_original": valid_config.get("save_in_existing_location", None),
                "single_export_location": valid_config.get("single_export_location", None),
                "weight_file": valid_config.get("weight_file", None),
                "noise_level": valid_config.get("noise_level", None),
            }

    def set_export_type(self):
        if self.export_to_original.get():
            ExportConfig.save_in_existing_location = True

            self.selected_fof.delete(0, ctk.END)
            disable_UI_elements(self.selected_fof)
            disable_UI_elements(self.export_sub_frame.browse_button)

        else:
            ExportConfig.save_in_existing_location = False
            enable_UI_elements(self.selected_fof)
            enable_UI_elements(self.export_sub_frame.browse_button)

    def export_event(self, value):
        log_file = write_log_to_file(None, None, None)
        exp_ids = self.lb_frame.curselection()
        if len(exp_ids) > 0:
            export_config = ExportFrame.parse_export_config(ExportConfig)

            if not export_config:
                write_log_to_file("Error", "Could not validate export config.", log_file)
                CTkMessagebox(
                title="Error Message!",
                message=f"Failed to process current configuration.",
                icon="warning",
                option_1="Ok",
            )
            
            else:
                self.export_thread = ExportThread(
                    target=export_images,
                    args=(
                        self,
                        export_config,
                        None,
                        exp_ids,
                        self.progbar,
                        self.stop_export_button,
                        False,
                    ),
                )
                disable_UI_elements(self.export_sub_frame.export_button)
                self.export_thread.daemon = True  # so the thread can be stopped likewise if the master frame is force-closed
                self.export_thread.start()
        else:
            CTkMessagebox(
                title="Warning Message!",
                message=f"No images selected for export!",
                icon="warning",
                option_1="Ok",
            )

    def kill_export_thread(self, value):
        self.export_thread.stop()


class ExportThread(threading.Thread):
    """
    Thread class with a _stop() method.
    The thread itself has to check
    regularly for the stopped() condition.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        self._stop = threading.Event()
        self._task = kwargs.get("target")
        self._args = kwargs.get("args")

    # function using _stop function
    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()

    def run(self):
        self._task(*self._args, task=self)
