import os
from typing import List, Dict, Tuple, Union
import customtkinter as ctk
from tkinter import filedialog
from app_config.config import (
    SearchConfig,
    GUIConfig,
    ExportConfig,
    PrePostProcessingConfig as ppconfig,
)


def select_fof_event(
    master_frame,
    lb_frame,
    root_dir: str,
    fof: bool,
    export: bool,
    update_config: bool = True,
):
    from gui.frames.main_listbox_frame import TkListbox
    selection, no_selection = archiveBrowse(
        master_frame, fof, root_dir, export, update_config
    )

    if lb_frame is not None:
        SearchConfig.file_or_folder = "folder" if fof == "folder" else "file"
        SearchConfig.last_used_dir_or_file = selection
        if (
            not no_selection
        ):  # do not populate if no selection as it could be a directory with a lot files
            if fof == "file":
                disable_UI_elements(master_frame.recursive_checkbox)
                TkListbox.populate(
                    lb_frame.selected_fof.get(), SearchConfig.recursive, add=True
                )
            else:
                enable_UI_elements(master_frame.recursive_checkbox)
                TkListbox.populate(
                    lb_frame, master_frame.selected_fof.get(), SearchConfig.recursive, add=False
                )
            SearchConfig.lb_populated_once = True


def archiveBrowse(
    root, fof: bool, initdir: str, export: bool, update_config: bool = False
):
    root.selected_fof.delete(0, ctk.END)

    if fof == "file":
        root.user_selection: str = filedialog.askopenfilename(
            initialdir=initdir, filetypes=SearchConfig.supported_file_types
        )
    else:
        root.user_selection: str = filedialog.askdirectory(
            initialdir=initdir
        )  # TODO: Add read from saved user config

    if root.user_selection != "":
        root.selected_fof.insert("0", root.user_selection)
        root.selected_fof.xview(len(root.selected_fof.get()))
        if not export:
            SearchConfig.last_used_dir_or_file = (
                root.user_selection
                if update_config
                else SearchConfig.last_used_dir_or_file
            )
        else:
            ExportConfig.single_export_location = (
                root.user_selection
                if update_config
                else ExportConfig.single_export_location
            )

    else:
        default_selection = os.getcwd()
        root.selected_fof.insert("0", default_selection)
        if not export:
            SearchConfig.last_used_dir_or_file = default_selection
        else:
            ExportConfig.single_export_location = default_selection

        return (
            default_selection,
            True,
        )  # defualt director, and true that the user did not select a file/folder

    return root.user_selection, False


def recursive_checkbox_event(
    parent_dir: ctk.CTkEntry, lb_frame: ctk.CTkFrame, recursive: ctk.BooleanVar
):
    SearchConfig.recursive = recursive.get()
    lb_frame.populate(parent_dir.get(), recursive.get(), add=False)


def print_to_frame(
    frame: ctk.CTkFrame, string: str, grid: bool, destroy: bool, **kwargs
):
    frame.error_label.configure(text="")
    if not destroy:
        frame.error_label = ctk.CTkLabel(
            master=frame,
            text=string,
            font=kwargs.get("font"),
            text_color=kwargs.get("text_color"),
            width=kwargs.get("lbl_width"),
            height=kwargs.get("lbl_height"),
        )
        if grid:
            frame.error_label.grid(
                row=kwargs.get("row"),
                column=kwargs.get("column"),
                columnspan=kwargs.get("columnspan"),
                padx=kwargs.get("padx"),
                pady=kwargs.get("pady"),
            )
        else:
            frame.error_label.pack(side=kwargs.get("side"))


def handle_following_menus(
    master_frame:  Union[ctk.CTkOptionMenu, None] = None, format: str = "dds"
):
    ExportConfig.active_compression = ppconfig.compression_map[format]
    master_frame.compression_subframe.menu.configure(
        values=list(ExportConfig.active_compression)
    )

    if ExportConfig.active_compression == ("undefined"):
        disable_UI_elements(master_frame.compression_subframe.menu_tt)
    if not ppconfig.supports_mipmaps[format]:
        disable_UI_elements(master_frame.additional_options_subframe.menu)


def disable_UI_elements(
    element:  Union[ctk.CTkCheckBox, ctk.CTkEntry, ctk.CTkOptionMenu, None] = None,
):
    # disable recursive checkbox
    element.configure(state="disabled")

    if isinstance(element, ctk.CTkCheckBox):
        element.deselect()

    if isinstance(element, ctk.CTkEntry):
        element.delete(0, ctk.END)


def enable_UI_elements(
    element:  Union[ctk.CTkCheckBox, ctk.CTkEntry, ctk.CTkOptionMenu, None] = None,
):
    element.configure(state="normal")
