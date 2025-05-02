from tkinter import EXTENDED
import customtkinter as ctk
from app_config.config import GUIConfig, TechnicalConfig
from gui.frames import *
from utils.events import select_fof_event

class MasterFrame(ctk.CTk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title(
            kwargs.get(
                "title",
                f"{TechnicalConfig.app_display_name} {TechnicalConfig.gui_version}",
            )
        )
        self.wm_attributes("-alpha", 0.99)
        self.w = kwargs.get("width", GUIConfig.master_default_width)
        self.h = kwargs.get("width", GUIConfig.master_default_height)
        self.geometry(f"{self.w}x{self.h}")
        self.maxsize(self.w, self.h)
        self.minsize(self.w, self.h)
        self.protocol("WM_DELETE_WINDOW", self.exit_and_close_log_file)
        self.tab_view = TabView(self, corner_radius=5)

        self.general_left_column = ctk.CTkFrame(
            master=self.tab_view.tab("General"),
            fg_color="transparent",
            bg_color="transparent",
            width=self.w // 2 - 10,
            height=self.h - 10,
        )
        self.general_right_column = ctk.CTkFrame(
            master=self.tab_view.tab("General"),
            fg_color="transparent",
            bg_color="transparent",
            width=self.w // 2 - 10,
            height=self.h - 10,
        )
        self.additional_main_column = ctk.CTkFrame(
            master=self.tab_view.tab("Additional Settings"),
            fg_color="transparent",
            bg_color="transparent",
            width=self.w - 20,
            height=self.h - 10,
        )

        self.general_left_column.grid(row=1, column=1, sticky="nsew", padx=5)
        self.general_right_column.grid(row=1, column=2, sticky="nsew", padx=5)
        self.additional_main_column.grid(
            row=1, column=1, sticky="nsew", padx=self.w // 4 - 54
        )

        self.export_options_frame = ExportOptionsFrame(
            master=self.general_left_column, width=self.w // 2
        )

        self.file_browser_lb = TkListbox(
            parent=self.general_right_column,
            selectmode=EXTENDED,
            fg="black",
            bg="black",
            width=120,
            height=40,
        )

        self.search_filters_frame = SearchFilterFrame(
            master=self.general_right_column, width=120, lb_frame=self.file_browser_lb
        )

        self.fof_frame = FileOrFolderFrame(
            master=self.general_left_column,
            lb_frame=self.file_browser_lb,
            width=self.w // 2,
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
            master=self.general_left_column,
            lb_frame=self.file_browser_lb,
            width=self.w // 2,
        )

        self.bind("<Control-e>", self.export_frame.export_event)

        self.additional_settings_frame = AdditionalOptionsFrame(
            master=self.additional_main_column, width=self.w - 100
        )

        self.app_and_ui_opts_frame = AppAndUIOptions(
            master=self.additional_main_column,
            fof_frame=self.fof_frame,
            expopts_frame=self.export_options_frame,
            export_frame=self.export_frame,
            filter_frame=self.search_filters_frame,
            lb_frame=self.file_browser_lb,
            addit_sett_frame=self.additional_settings_frame,
            width=self.w,
        )

        self.export_options_frame.addit_sett_subframe = self.additional_settings_frame
    def exit_and_close_log_file(self):
        self.destroy()
