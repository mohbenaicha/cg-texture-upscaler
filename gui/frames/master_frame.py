from tkinter import EXTENDED
import sys
import customtkinter as ctk
from app_config.config import SearchConfig, GUIConfig
from gui.frames.search_filter_frame import SearchFilterFrame
from gui.frames.export_options_frame import ExportOptionsFrame
from gui.frames.app_and_ui_opts_frame import AppAndUIOptions
from gui.frames.export_frame import ExportFrame
from gui.frames.file_or_folder_frame import FileOrFolderFrame
from gui.frames.main_listbox_frame import TkListbox
from utils.events import select_fof_event


class MasterFrame(ctk.CTk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title(kwargs.get("title", "CG Texture Upscaler"))
        self.wm_attributes("-alpha", 0.99)
        self.w = kwargs.get("width", GUIConfig.master_default_width)
        self.h = kwargs.get("width", GUIConfig.master_default_height)
        self.geometry(f"{self.w}x{self.h}")
        self.maxsize(self.w, self.h)
        self.minsize(self.w, self.h)

        self.left_column = ctk.CTkFrame(
            master=self,
            fg_color="transparent",
            bg_color="transparent",
            width=self.w // 2 - 10,
            height=self.h - 10,
        )
        self.right_column = ctk.CTkFrame(
            master=self,
            fg_color="transparent",
            bg_color="transparent",
            width=self.w // 2 - 10,
            height=self.h - 10,
        )
        self.left_column.grid(row=1, column=1, sticky="nsew", padx=5)
        self.right_column.grid(row=1, column=2, sticky="nsew", padx=5)

        self.export_options_frame = ExportOptionsFrame(
            master=self.left_column, width=self.w // 2
        )

        self.file_browser_lb = TkListbox(
            parent=self.right_column,
            selectmode=EXTENDED,
            fg="black",
            bg="black",
            width=120,
            height=40,
        )

        self.search_filters_frame = SearchFilterFrame(
            master=self.right_column, width=120, lb_frame=self.file_browser_lb
        )

        self.fof_frame = FileOrFolderFrame(
            master=self.left_column, lb_frame=self.file_browser_lb, width=self.w // 2
        )
        self.bind(
            "<Control-o>",
            lambda _: select_fof_event(
                master_frame=self.fof_frame,
                lb_frame=self.file_browser_lb,
                root_dir=self.fof_frame.selection,
                fof="folder",
                export=False,
            ),
        )

        self.file_browser_lb.fof_frame = self.fof_frame
        self.file_browser_lb.filter_frame = self.search_filters_frame

        self.export_frame = ExportFrame(
            master=self.left_column, lb_frame=self.file_browser_lb, width=self.w // 2
        )

        self.bind(
            "<Control-e>", self.export_frame.export_event
        )
        self.app_and_ui_opts_frame = AppAndUIOptions(
            master=self.left_column,
            fof_frame=self.fof_frame,
            expopts_frame=self.export_options_frame,
            export_frame=self.export_frame,
            filter_frame=self.search_filters_frame,
            lb_frame=self.file_browser_lb,
            width=self.w // 2,
        )
