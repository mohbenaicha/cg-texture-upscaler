from typing import List
import sys
from tkinter import *
from functools import partial
import customtkinter as ctk
from gui.tooltips import tooltip_text as ttt
from gui.tooltips import Hovertip_Frame
import utils.ctk_fonts as fonts
from gui.frames.main_listbox_frame import TkListbox
from app_config.config import SearchConfig
from model.utils import write_log_to_file
from utils.events import *

log_file = write_log_to_file(None, None, None)

class SearchFilterFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master)
        self.lb_frame: TkListbox = kwargs.get("lb_frame", None)
        self.setup_frame_elements()
        self.create_key_bindings()
        self.plot_self()
        self.plot_frame_elements()

    def setup_frame_elements(self):
        self.label = ctk.CTkLabel(
            self, font=fonts.header_labels_font(), text="➋ Search Filters", width=10
        )

        self.and_filters_str: List[ctk.StringVar] = [
            ctk.StringVar(value="") for _ in range(SearchConfig.num_and_filters)
        ]
        self.or_filters_str: List[ctk.StringVar] = [
            ctk.StringVar(value="") for _ in range(SearchConfig.num_or_filters)
        ]
        self.and_filters: List[ctk.CTkEntry] = []
        self.or_filters: List[ctk.CTkEntry] = []
        self.and_label = ctk.CTkLabel(
            master=self,
            font=fonts.labels_font(),
            text="Search for files with all of the following :",
            width=10,
        )
        self.or_label = ctk.CTkLabel(
            master=self,
            font=fonts.labels_font(),
            text="Search for files with any of the following:",
            width=10,
        )
        self.and_label_set = [
            ctk.CTkLabel(master=self, font=fonts.options_font(), text="AND", width=10)
            for _ in range(SearchConfig.num_and_filters)
        ]
        self.or_label_set = [
            ctk.CTkLabel(master=self, font=fonts.options_font(), text="OR", width=10)
            for _ in range(SearchConfig.num_or_filters)
        ]

        for i in range(SearchConfig.num_and_filters):
            self.and_filters.append(
                ctk.CTkEntry(
                    self,
                    width=50,
                    font=fonts.text_font(),
                    textvariable=self.and_filters_str[i],
                )
            )

        for i in range(SearchConfig.num_or_filters):
            self.or_filters.append(
                ctk.CTkEntry(
                    self,
                    width=50,
                    font=fonts.text_font(),
                    textvariable=self.or_filters_str[i],
                )
            )

        self.button_sub_frame = ctk.CTkFrame(
            master=self, fg_color="transparent", bg_color="transparent", width=150
        )
        self.filter_curr_list_button = ctk.CTkButton(
            self.button_sub_frame,
            text="Apply to Current List",
            font=fonts.buttons_font(),
            command=lambda: SearchFilterFrame.apply_filter(self, None, "current_list"),
        )

        self.filter_curr_list_button_tt = Hovertip_Frame(
            anchor_widget=self.filter_curr_list_button,
            text=ttt.apply_to_current_list,
            hover_delay=GUIConfig.tooltip_hover_delay,
            bg_color=GUIConfig.tooltip_color,
            text_color=GUIConfig.tooltop_text_color,
        )

        self.filter_selected_dir_button = ctk.CTkButton(
            self.button_sub_frame,
            text="Apply to Selected Directory",
            font=fonts.buttons_font(),
            command=lambda: SearchFilterFrame.apply_filter(self, None, "chosen_dir"),
        )

        self.filter_selected_dir_button_tt = Hovertip_Frame(
            anchor_widget=self.filter_selected_dir_button,
            text=ttt.apply_to_chosen_dir,
            hover_delay=GUIConfig.tooltip_hover_delay,
            bg_color=GUIConfig.tooltip_color,
            text_color=GUIConfig.tooltop_text_color,
        )

        self.clearfilters_button = ctk.CTkButton(
            self.button_sub_frame,
            text="Clear all",
            font=fonts.buttons_font(),
            width=15,
            command=lambda: self.clear_all_fields(None),
        )
        self.clearfilters_button_tt = Hovertip_Frame(
            anchor_widget=self.clearfilters_button,
            text=ttt.clear_all_filters,
            hover_delay=GUIConfig.tooltip_hover_delay,
            bg_color=GUIConfig.tooltip_color,
            text_color=GUIConfig.tooltop_text_color,
        )

        self.error_printout_frame = ctk.CTkFrame(
            master=self,
            fg_color="transparent",
            bg_color="transparent",
            width=100,
            height=10,
        )
        self.error_printout_frame.error_label = ctk.CTkLabel(
            master=self.button_sub_frame,
            text=" ",
            text_color="red",
            width=50,
            height=15,
        )

    @classmethod
    def apply_filter(
        cls,
        obj,
        bind_value,
        source_list: str,
        and_filters: List[str] = [""],
        or_filters: List[str] = [""],
    ):
        if obj:
            and_filters: List[str] = [
                filter_txt.get() for filter_txt in obj.and_filters_str
            ]
            or_filters: List[str] = [
                filter_txt.get() for filter_txt in obj.or_filters_str
            ]

        ill_char_set: set[str] = set(SearchConfig.illegal_search_characters)
        filter_string: set[str] = set("".join(and_filters) + "".join(or_filters))
        bad_chars_found: set[str] = ill_char_set.intersection(filter_string)
        if any(bad_chars_found):
            # if illegal search characters are found, print warning to user
            if obj:
                print_to_frame(
                    obj.error_printout_frame,
                    grid=True,
                    string=f"*Illegal character(s):   " + " , ".join(bad_chars_found),
                    destroy=False,
                    font=fonts.error_font(),
                    text_color="red",
                    lbl_height=15,
                    lbl_width=50,
                    row=1,
                    column=1,
                )
            else:
                write_log_to_file(
                    "WARNING",
                    f"*Illegal character(s) found in filters:   "
                    + " , ".join(bad_chars_found),
                    log_file,
                )
                print(
                    f"*Illegal character(s) found in filters:   "
                    + " , ".join(bad_chars_found)
                )
                
                sys.exit(1)
        else:
            # if no illegal characters are found the AND and OR fields are checked against the chosen directory
            if obj:
                print_to_frame(
                    obj.error_printout_frame,
                    grid=True,
                    string="",
                    destroy=False,
                    font=fonts.error_font(),
                    text_color="red",
                    lbl_height=15,
                    lbl_width=50,
                    row=1,
                    column=1,
                )
            TkListbox.filter(
                obj.lb_frame if obj else None, and_filters, or_filters, source_list if obj else "chosen_directory"
            )

    def save_and_filters(self, value, idx):
        SearchConfig.last_and_filters[idx] = self.and_filters[idx].get()
        return

    def save_or_filters(self, value, idx):
        SearchConfig.last_or_filters[idx] = self.or_filters[idx].get()
        return

    def clear_all_fields(self, value):
        for and_filter, or_filter in zip(self.and_filters, self.or_filters):
            and_filter.delete(0, ctk.END)
            or_filter.delete(0, ctk.END)

    def plot_self(self):
        self.grid(row=1, column=1, padx=1, pady=5, sticky="nsw")
        self.label.grid(row=0, column=1, columnspan=8, sticky="nswe", padx=3, pady=5)

    def plot_frame_elements(self):
        self.or_label.grid(column=0, columnspan=7, sticky="w", row=3, padx=7, pady=5)
        self.and_label.grid(column=0, columnspan=7, sticky="w", row=1, padx=7, pady=5)

        # plot AND / OR boxes and labels
        for col, and_box in enumerate(self.and_filters):
            padx = 10 if col == 0 or col == 3 else 4
            and_box.grid(column=col * 2 + 1, sticky="we", row=2, padx=padx, pady=2)
            if col > 0:
                label = self.and_label_set.pop(0)
                label.grid(column=col * 2, sticky="we", row=2, padx=4, pady=2)

        for col, or_box in enumerate(self.or_filters):
            padx = 10 if col == 0 or col == 3 else 4
            or_box.grid(column=col * 2 + 1, sticky="we", row=4, padx=padx, pady=2)
            if col > 0:
                label = self.or_label_set.pop(0)
                label.grid(column=col * 2, sticky="we", row=4, padx=4, pady=2)

        self.button_sub_frame.grid(column=0, columnspan=8, row=5, padx=4, pady=4)
        self.filter_curr_list_button.grid(column=1, row=1, padx=4, pady=3)
        self.filter_selected_dir_button.grid(column=2, row=1, padx=4, pady=3)
        self.clearfilters_button.grid(column=1, columnspan=2, row=2, padx=4, pady=3)
        self.error_printout_frame.grid(column=1, columnspan=6, row=7, padx=5, pady=4)

    def create_key_bindings(self):
        [
            self.and_filters[i].bind(
                "<KeyRelease>", partial(self.save_and_filters, idx=i)
            )
            for i in range(4)
        ]
        [
            self.and_filters[i].bind(
                "<Return>", partial(self.apply_filter, source_list="current_list")
            )
            for i in range(4)
        ]

        [
            self.and_filters[i].bind(
                "<KeyPress-Shift_L><Return>",
                partial(self.apply_filter, source_list="chosen_dir"),
            )
            for i in range(4)
        ]

        [
            self.and_filters[i].bind("<Escape>", partial(self.clear_all_fields))
            for i in range(4)
        ]

        [
            self.or_filters[i].bind(
                "<KeyRelease>", partial(self.save_or_filters, idx=i)
            )
            for i in range(4)
        ]
        [
            self.or_filters[i].bind(
                "<Return>", partial(self.apply_filter, source_list="current_list")
            )
            for i in range(4)
        ]

        [
            self.or_filters[i].bind(
                "<KeyPress-Shift_L><Return>",
                partial(self.apply_filter, source_list="chosen_dir"),
            )
            for i in range(4)
        ]

        [
            self.or_filters[i].bind("<Escape>", partial(self.clear_all_fields))
            for i in range(4)
        ]
