from tkinter import *
import customtkinter as ctk
from gui.tooltips import Hovertip_Frame
import gui.tooltips.tooltip_text as ttt
import utils.ctk_fonts as fonts
from gui.frames.main_listbox_frame import TkListbox
from app_config.config import SearchConfig, GUIConfig
from utils.events import *


class FileOrFolderFrame(ctk.CTkFrame):
    def __init__(self, master, width: int = 1, height: int = 100, **kwargs):
        super().__init__(master)
        self.lb_frame: TkListbox = kwargs.get("lb_frame")
        self.configure(width=width, height=height)
        self.setup_ui_elements()
        self.plot_self()
        self.plot_ui_elements()

    def setup_ui_elements(self):
        self.header_label = ctk.CTkLabel(
            self,
            font=fonts.header_labels_font(),
            width=1,
            text="➊ Source Image or Folder",
        )
        self.instruct_label = ctk.CTkLabel(
            self,
            font=fonts.labels_font(),
            width=1,
            text="Select a file or folder to process:",
        )

        self.selection = ctk.StringVar(
            value=SearchConfig.last_used_dir_or_file
            if SearchConfig.last_used_dir_or_file != ""
            else ""
        )  # TODO: read from config
        self.recursive = ctk.BooleanVar(value=False)  # TODO: read from config

        self.selected_fof = ctk.CTkEntry(
            self, width=250, font=fonts.text_font(), textvariable=self.selection
        )
        self.recursive_checkbox = ctk.CTkCheckBox(
            master=self,
            text="Recursive 🛑",
            font=fonts.options_font(),
            text_color="red",
            variable=self.recursive,
            border_width=2,
            checkbox_height=17,
            checkbox_width=17,
            onvalue=True,
            width=1,
            offvalue=False,
            command=self.recursive_checkbox_event,
        )

        self.recursive_checkbox_tt = Hovertip_Frame(
            anchor_widget=self.recursive_checkbox,
            text=ttt.recursive,
            hover_delay=GUIConfig.tooltip_hover_delay,
            bg_color=GUIConfig.tooltip_color,
            text_color=GUIConfig.tooltop_text_color,
        )

        self.sub_frame = ctk.CTkFrame(
            master=self,
            fg_color="transparent",
            bg_color="transparent",
            height=25,
            width=1,
        )  # subframe to pack select file and folder buttons
        self.sub_frame.select_file = ctk.CTkButton(
            self.sub_frame,
            text="File",
            font=fonts.buttons_font(),
            width=15,
            command=lambda: select_fof_event(
                master_frame=self,
                lb_frame=self.lb_frame,
                root_dir=self.selection,
                fof="file",
                export=False,
            ),
        )
        self.sub_frame.select_file_tt = Hovertip_Frame(
            anchor_widget=self.sub_frame.select_file,
            text=ttt.file,
            hover_delay=GUIConfig.tooltip_hover_delay,
            bg_color=GUIConfig.tooltip_color,
            text_color=GUIConfig.tooltop_text_color,
        )

        self.sub_frame.select_folder = ctk.CTkButton(
            self.sub_frame,
            text="Browse",
            font=fonts.buttons_font(),
            width=15,
            command=lambda: select_fof_event(
                master_frame=self,
                lb_frame=self.lb_frame,
                root_dir=self.selection,
                fof="folder",
                export=False,
            ),
        )

        self.sub_frame.select_folder_tt = Hovertip_Frame(
            anchor_widget=self.sub_frame.select_folder,
            text=ttt.folder,
            hover_delay=GUIConfig.tooltip_hover_delay,
            bg_color=GUIConfig.tooltip_color,
            text_color=GUIConfig.tooltop_text_color,
        )

    def plot_self(self):
        self.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)

    def plot_ui_elements(self):
        # placing labels
        self.header_label.grid(row=0, column=0, sticky="ew", padx=0, pady=7)
        self.instruct_label.grid(row=1, column=0, sticky="w", padx=7, pady=5)

        # placing entry field
        self.selected_fof.grid(row=2, column=0, sticky="we", padx=6, pady=5)

        # placing field subframe

        # placing buttons and subframe for buttons
        self.sub_frame.grid(row=3, column=0, sticky="ew", padx=1)
        # self.sub_frame.select_file.grid(row=0,column=0,sticky='we', padx=7,pady=5)
        self.sub_frame.select_folder.grid(row=0, column=0, sticky="we", padx=7, pady=5)

        # placing checkbox
        self.recursive_checkbox.grid(row=4, column=0, sticky="we", padx=10, pady=5)

    def recursive_checkbox_event(self):
        SearchConfig.recursive = self.recursive.get()
        TkListbox.populate(self.lb_frame, self.selection.get(), self.recursive.get(), add=False)