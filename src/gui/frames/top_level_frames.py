from __future__ import annotations
import os
import yaml
import tkinter as tk
import customtkinter as ctk
import utils.ctk_fonts as fonts
from ..message_box import CTkMessagebox
from utils.events import select_fof_event
from model.utils import copy_files
from app_config.config import *
from caches.cache import image_paths_cache as cache_copy
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gui.frames.export_frame import ExportFrame
    from gui.frames.main_listbox_frame import TkListbox
    from gui.frames.export_options_frame import ExportOptionsFrame
    from gui.frames.file_or_folder_frame import FileOrFolderFrame
    from gui.frames.app_and_ui_opts_frame import AppAndUIOptions
    from gui.frames.search_filter_frame import SearchFilterFrame


class ImageWindow(ctk.CTkToplevel):
    def __init__(self, im_name, image, *args, **kwargs):
        super().__init__(*args)
        self.channels = kwargs.get("mode")
        self.width = kwargs.get("width")
        self.height = kwargs.get("height")
        self.orig_dims = kwargs.get("orig_size")
        self.geometry(f"{self.width+10}x{self.height+80}")
        im_file = im_name.split("\\")[-1:][0]

        self.title(f"{im_file}")
        self.image = ctk.CTkLabel(self, image=image, text="")
        self.txt = ctk.CTkLabel(
            self,
            text=f"Name: {im_file}\nResolution: ({self.orig_dims[1]}x{self.orig_dims[0]})\nPreview resolution: ({self.width}x{self.height})\nChannels: {self.channels}\n{im_name}",
            justify="left",
            width=1,
            height=1,
        )
        self.txt.grid(row=1, column=1, padx=5, pady=1, sticky="nw")
        self.image.grid(row=2, column=1, padx=5, pady=1, sticky="nw")
        self.bind("<Escape>", self.destroy_binding)

    def open_toplevel(self):
        if self.toplevel_window is None or not self.toplevel_window.winfo_exists():
            self.toplevel_window = ImageWindow(self)
            self.toplevel_window.focus()
        else:
            self.toplevel_window.focus()

    def destroy_binding(self, value):
        super().destroy()


class SaveConfigWindow(ctk.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry = "200x400"
        self.title("Save Configuration")

        self.label = ctk.CTkLabel(self, text="Enter a name for your configuration:")
        self.entry_frame = ctk.CTkFrame(
            self, height=20, width=300, fg_color="transparent", bg_color="transparent"
        )
        self.entry_value = ctk.StringVar(value="")
        self.entryfield = ctk.CTkEntry(
            self.entry_frame,
            placeholder_text="MyConfig",
            height=20,
            width=300,
            textvariable=self.entry_value,
        )
        self.entryfield.bind("<KeyRelease>", self.set_conf_file_name)

        self.button_frame = ctk.CTkFrame(
            self, height=5, width=100, fg_color="transparent", bg_color="transparent"
        )
        self.confirm = ctk.CTkButton(
            self.button_frame,
            text="Save",
            font=fonts.buttons_font(),
            width=20,
            height=10,
            command=lambda: self.confirm_button_event(None),
        )
        self.bind("<Return>", self.confirm_button_event)
        self.cancel = ctk.CTkButton(
            self.button_frame,
            text="Cancel",
            width=20,
            font=fonts.buttons_font(),
            height=10,
            command=lambda: self.cancel_button_event(None),
        )
        self.bind("<Escape>", self.cancel_button_event)
        self.plot_elements()

    def plot_elements(self):
        self.label.grid(row=1, column=1, padx=5, pady=5)
        self.entry_frame.grid(row=2, column=1, padx=5, pady=2)
        self.entryfield.grid(row=1, column=1, padx=5, pady=2)
        self.button_frame.grid(row=3, column=1, padx=5, pady=5)
        self.confirm.grid(row=1, column=1, padx=5, pady=5)
        self.cancel.grid(row=1, column=2, padx=5, pady=5)

    def write_to_yaml(self, fn):
        conf = {
            "last_search_fof": SearchConfig.last_used_dir_or_file
            if not SearchConfig.last_used_dir_or_file == None
            else "",
            "recursive": SearchConfig.recursive,
            "and_filters": SearchConfig.last_and_filters,
            "or_filters": SearchConfig.last_or_filters,
            "device": ExportConfig.device,
            "scale": ExportConfig.scale,
            "format": ExportConfig.export_format,
            "compression": ExportConfig.compression,
            "mipmaps": ExportConfig.mipmaps,
            "numbering": ExportConfig.save_numbering,
            "prefix": ExportConfig.save_prefix,
            "suffix": ExportConfig.save_suffix,
            "save_in_original": ExportConfig.save_in_existing_location,
            "single_export_loc": ExportConfig.single_export_location
            if not ExportConfig.single_export_location == None
            else "",
        }
        if not os.path.exists('user_config'):
            os.mkdir('user_config')
        with open(os.path.join("user_config", f"{fn}.cfg"), "w") as yamlfile:
            yaml.dump(conf, yamlfile)
        yamlfile.close()

    def set_conf_file_name(self, value):
        SearchConfig.go_to_file_name = self.entry_value.get()

    def confirm_button_event(self, value):
        save = True
        if SearchConfig.go_to_file_name == "" or any(
            [
                i in SearchConfig.illegal_search_characters
                for i in SearchConfig.go_to_file_name
            ]
        ):
            CTkMessagebox(
                title="Error!",
                message=f"Invalid name entered. Must have atleast one character and none of the following symbols: {SearchConfig.illegal_search_characters}",
                icon="warning",
                option_1="Ok",
            )
            save = False

        if save:
            self.write_to_yaml(SearchConfig.go_to_file_name)

    def cancel_button_event(self, value):
        self.destroy()


class LoadConfigWindow(ctk.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.geometry = "200x400"
        self.title("Save Config")
        self.parent: AppAndUIOptions = kwargs.get("parent")
        self.fof_frame: FileOrFolderFrame = kwargs.get("fof_frame")
        self.filter_frame: SearchFilterFrame = kwargs.get("filter_frame")
        self.exp_opts_frame: ExportOptionsFrame = kwargs.get("exp_opts_frame")
        self.lb_frame: TkListbox = kwargs.get("lb_frame")  # image file populate listbox
        self.export_frame: ExportFrame = kwargs.get("export_frame")

        self.label = ctk.CTkLabel(self, text="Select a configuration to load:")
        self.listbox_frame = ctk.CTkFrame(
            self, height=10, width=50
        )  # config file populate listbox
        self.listbox = LoadConfigListBox(
            self.listbox_frame,
            selectmode=tk.EXTENDED,
            # opening config window according to current scale; TODO: experimental features that needs revision
            height=int(round(10 * self.parent.gui_scale, 0)) - 1,
            width=int(round(30 * self.parent.gui_scale, 0)) - 1,
        )
        self.button_frame = ctk.CTkFrame(
            self, height=10, width=10, fg_color="transparent", bg_color="transparent"
        )
        self.confirm_config_button = ctk.CTkButton(
            self.button_frame,
            text="Load",
            font=fonts.buttons_font(),
            width=10,
            height=10,
            command=lambda: self.confirm_button_event(None),
        )
        self.delete_config_button = ctk.CTkButton(
            self.button_frame,
            text="Delete",
            font=fonts.buttons_font(),
            width=20,
            height=10,
            command=lambda: self.delete_config(None),
        )

        self.refresh_config_button = ctk.CTkButton(
            self.button_frame,
            text="Refersh",
            font=fonts.buttons_font(),
            width=20,
            height=10,
            command=lambda: self.refresh_config_list(None),
        )

        # binding confirm and close commands to keyboard keys
        self.bind("<Return>", self.confirm_button_event)
        self.bind("<Escape>", self.cancel_button_event)
        self.bind("<Delete>", self.delete_config)
        self.bind("<F5>", self.refresh_config_list)

        self.plot_elements()
        self.populate_lb()

    def plot_elements(self):
        self.label.grid(row=1, column=1, padx=5, pady=5)
        self.listbox_frame.grid(row=2, column=1, padx=5, pady=2)
        self.button_frame.grid(row=3, column=1, padx=5, pady=5)
        self.confirm_config_button.grid(row=1, column=1, padx=5, pady=5)
        self.delete_config_button.grid(row=1, column=2, padx=5, pady=5)
        self.refresh_config_button.grid(row=1, column=3, padx=5, pady=5)

    def populate_lb(self):
        if not os.path.exists('user_config'):
            os.mkdir('user_config')
        config_files = [file[:-4] for file in os.listdir("user_config")]
        self.listbox.configure_listbox(listvariable=config_files)

    def load_config(self):
        selection = self.listbox.listbox.curselection()
        if len(selection) != 1:
            self.parsed_conf = None
        else:
            selection = os.path.join(
                "user_config", (self.listbox.listbox.get(selection) + ".cfg")
            )
            with open(selection, "r") as conf_file:
                parsed_conf = yaml.load(conf_file, Loader=yaml.FullLoader)
                conf_file.close()
            self.parsed_conf = parsed_conf
        return self.parsed_conf

    def delete_config(self, value):
        selection = self.listbox.listbox.curselection()
        if len(selection) == 0:
            pass
        else:
            for item in selection:
                item = os.path.join(
                    "user_config", (self.listbox.listbox.get(item) + ".cfg")
                )
                os.remove(item)

            self.listbox.remove_items(None)
            config_files = [file[:-4] for file in os.listdir("user_config")]
            self.listbox.configure_listbox(listvariable=config_files)

    def refresh_config_list(self, value):
        config_files = [file[:-4] for file in os.listdir("user_config")]
        self.listbox.remove_items(None)
        self.listbox.configure_listbox(listvariable=config_files)

    # TODO: the following list of methods could be better written inline with SOLID
    # Methods to load and update UI elements
    def set_fof(self):
        self.fof_frame.recursive_checkbox.select() if self.parsed_conf[
            "recursive"
        ] else self.fof_frame.recursive_checkbox.deselect()
        self.fof_frame.selected_fof.delete("0", ctk.END)
        SearchConfig.recursive = self.parsed_conf["recursive"]

        self.fof_frame.selected_fof.insert("0", self.parsed_conf["last_search_fof"])
        self.fof_frame.recursive_checkbox_event()
        SearchConfig.last_used_dir_or_file = self.parsed_conf["last_search_fof"]

    def set_filter_frame(self):
        for i, entry in enumerate(self.filter_frame.and_filters):
            entry.delete("0", ctk.END)
            entry.insert("0", self.parsed_conf["and_filters"][i])
            SearchConfig.last_and_filters[i] = self.parsed_conf["and_filters"][i]
        for i, entry in enumerate(self.filter_frame.or_filters):
            entry.delete("0", ctk.END)
            entry.insert("0", self.parsed_conf["or_filters"][i])
            SearchConfig.last_or_filters[i] = self.parsed_conf["or_filters"][i]

    def set_export_options_frame(self):
        self.exp_opts_frame.device_subframe.menu.set(value=self.parsed_conf["device"])
        self.exp_opts_frame.set_device(value=self.parsed_conf["device"])

        self.exp_opts_frame.scale_subframe.menu.set(value=self.parsed_conf["scale"])
        self.exp_opts_frame.set_scale(value=self.parsed_conf["scale"])

        self.exp_opts_frame.format_subframe.menu.set(value=self.parsed_conf["format"])
        self.exp_opts_frame.set_format(value=self.parsed_conf["format"])

        self.exp_opts_frame.set_compression(value=self.parsed_conf["compression"])
        self.exp_opts_frame.compression_subframe.menu.set(
            value=self.parsed_conf["compression"]
        )

        self.exp_opts_frame.additional_options_subframe.menu.set(
            value=self.parsed_conf["mipmaps"]
        )
        self.exp_opts_frame.set_mipmaps(value=self.parsed_conf["mipmaps"])

        self.exp_opts_frame.export_numbering_subframe.numbered_checkbox.select() if self.parsed_conf[
            "numbering"
        ] else self.exp_opts_frame.export_numbering_subframe.numbered_checkbox.deselect()
        self.exp_opts_frame.set_numbering(value=self.parsed_conf["numbering"])

        self.exp_opts_frame.export_prefix_subframe.prefix_field.delete("0", ctk.END)
        self.exp_opts_frame.export_prefix_subframe.prefix_field.insert(
            "0", self.parsed_conf["prefix"]
        )
        self.exp_opts_frame.set_prefix(value=self.parsed_conf["prefix"])

        self.exp_opts_frame.export_suffix_subframe.suffix_field.delete("0", ctk.END)
        self.exp_opts_frame.export_suffix_subframe.suffix_field.insert(
            "0", self.parsed_conf["suffix"]
        )
        self.exp_opts_frame.set_suffix(value=self.parsed_conf["suffix"])

    def set_export_frame(self):
        self.export_frame.save_in_original_checkbox.select() if self.parsed_conf[
            "save_in_original"
        ] else self.export_frame.save_in_original_checkbox.deselect()
        self.export_frame.export_to_original.set(
            value=self.parsed_conf["save_in_original"]
        )
        self.export_frame.set_export_type()
        ExportConfig.save_in_existing_location = self.parsed_conf["save_in_original"]

        self.export_frame.selected_fof.delete("0", ctk.END)
        self.export_frame.selected_fof.insert(
            "0", self.parsed_conf["single_export_loc"]
        )
        self.export_frame.selected_export_location.set(
            value=self.parsed_conf["single_export_loc"]
        )
        ExportConfig.single_export_location = self.parsed_conf["single_export_loc"]

    def confirm_button_event(self, value):
        self.parsed_conf = self.load_config()
        if self.parsed_conf:
            self.set_fof()
            self.set_filter_frame()
            self.set_export_options_frame()
            self.set_export_frame()
            self.lb_frame.remove_items(None)

    def cancel_button_event(self, value):
        self.destroy()

    def destroy(self):
        self.parent.load_toplevel_window = None
        super().destroy()


class LoadConfigListBox(ctk.CTkFrame):
    def __init__(self, parent, *args, **kwargs):
        ctk.CTkFrame.__init__(self, parent)
        self.listbox = tk.Listbox(self, font=fonts.list_font(), *args, **kwargs)
        self.listbox_scrollbar = ctk.CTkScrollbar(
            master=self,
            orientation="vertical",
            fg_color="#2E2E2E",
            width=25,
            command=self.listbox.yview,
        )

        # TODO: remove repetitive statements
        self.listbox.configure(
            yscrollcommand=self.listbox_scrollbar.set,
            activestyle="none",
            selectbackground="#4F4F4F",
            bd=0,
            bg="#2E2E2E",
            fg="#CDCDC0",
            relief=ctk.FLAT,
            borderwidth=0,
            highlightthickness=0,
        )
        self.configure(bg_color="#2E2E2E")

        if GUIConfig.current_theme == "dark":
            self.listbox.configure(
                selectbackground="#4F4F4F",
                fg=GUIConfig.light_theme_color,
                bg=GUIConfig.dark_theme_color,
            )
            self.configure(fg_color=GUIConfig.dark_theme_color)
            self.listbox_scrollbar.configure(fg_color=GUIConfig.dark_theme_color)
        else:
            self.listbox.configure(
                selectbackground="#4F4F4F",
                bg=GUIConfig.light_theme_color,
                fg=GUIConfig.dark_theme_color,
            )
            self.configure(
                fg_color=GUIConfig.light_theme_color,
                bg_color=GUIConfig.light_theme_color,
            )
            self.listbox_scrollbar.configure(fg_color=GUIConfig.light_theme_color)

        self.listbox.bind("<Enter>", self.enter)
        self.listbox.bind("<Leave>", self.leave)
        self.plot_elements()

    def plot_elements(self):
        self.grid(row=1, column=2)
        self.listbox.grid(row=1, column=1, sticky="ns")
        self.listbox_scrollbar.grid(row=1, column=2, sticky="ns")

    def configure_listbox(self, **kwargs):
        self.listvariable(kwargs.get("listvariable", None))

    def listvariable(self, item_list):
        if item_list != None:
            for item in item_list:
                self.listbox.insert(tk.END, item)

    def setforeground(self, fg):
        if fg != None:
            self.listbox.configure(fg=fg)

    def remove_items(self, value):
        self.listbox.delete(0, tk.END)

    def sethighlight(self, highlightcolor):
        if highlightcolor != None:
            self.listbox.configure(highlightcolor=highlightcolor)

    def setselectbackground(self, selectbackground):
        if selectbackground != None:
            self.listbox.configure(selectbackground=selectbackground)

    def setexportselection(self, exportselection):
        self.listbox.configure(exportselection=exportselection)

    def setbackground(self, bg):
        if bg != None:
            self.listbox.configure(bg=bg)

    def enter(self, event):
        self.listbox.config(cursor="hand2")

    def leave(self, event):
        self.listbox.config(cursor="")


class GoToWindow(ctk.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.geometry = "200x400"
        self.title("Find file")
        self.main_lb = kwargs.get("main_lb")
        self.label = ctk.CTkLabel(
            self,
            text="Find and select items with the following characters:",
            text_color="red",
        )
        self.entry_frame = ctk.CTkFrame(
            self, height=20, width=300, fg_color="transparent", bg_color="transparent"
        )
        self.entry_value = ctk.StringVar(value="")
        self.entryfield = ctk.CTkEntry(
            self.entry_frame,
            placeholder_text="",
            height=20,
            width=300,
            textvariable=self.entry_value,
        )
        self.entryfield.bind("<KeyRelease>", self.set_go_to_file_idx)

        self.button_frame = ctk.CTkFrame(
            self, height=5, width=100, fg_color="transparent", bg_color="transparent"
        )
        self.confirm = ctk.CTkButton(
            self.button_frame,
            text="Search",
            font=fonts.buttons_font(),
            width=20,
            height=10,
            command=lambda: self.confirm_button_event(None),
        )
        self.bind("<Return>", self.confirm_button_event)
        self.cancel = ctk.CTkButton(
            self.button_frame,
            text="Cancel",
            width=20,
            font=fonts.buttons_font(),
            height=10,
            command=lambda: self.cancel_button_event(None),
        )
        self.bind("<Escape>", self.cancel_button_event)
        self.plot_elements()

    def plot_elements(self):
        self.label.grid(row=1, column=1, padx=5, pady=5)
        self.entry_frame.grid(row=2, column=1, padx=5, pady=2)
        self.entryfield.grid(row=1, column=1, padx=5, pady=2)
        self.button_frame.grid(row=3, column=1, padx=5, pady=5)
        self.confirm.grid(row=1, column=1, padx=5, pady=5)
        self.cancel.grid(row=1, column=2, padx=5, pady=5)

    def set_go_to_file_idx(self, value):
        SearchConfig.go_to_file_name = self.entry_value.get()

    def confirm_button_event(self, value):
        proceed = True
        found_first = False
        if SearchConfig.go_to_file_name == "" or any(
            [
                i in SearchConfig.illegal_search_characters
                for i in SearchConfig.go_to_file_name
            ]
        ):
            CTkMessagebox(
                title="Error!",
                message=f"Invalid name entered. Must have atleast one character and none of the following symbols: {SearchConfig.illegal_search_characters}",
                icon="warning",
                option_1="Ok",
            )
            proceed = False

        if proceed:
            for i, img in enumerate(cache_copy[0]):
                if SearchConfig.go_to_file_name == img:
                    self.main_lb.listbox.select_set(i)
                    if not found_first:
                        self.main_lb.listbox.yview(i)
                    found_first = True

            if not found_first:
                for i, img in enumerate(cache_copy[0]):
                    if SearchConfig.go_to_file_name in img:
                        self.main_lb.listbox.select_set(i)
                        if not found_first:
                            self.main_lb.listbox.yview(i)
                        found_first = True

    def cancel_button_event(self, value):
        self.destroy()


class CopyFilesWindow(ctk.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.geometry = "200x400"
        self.title("Copy Files")
        self.main_lb = kwargs.get("main_lb")
        self.label = ctk.CTkLabel(
            self, text="Select a directory to which to copy the selected files:"
        )
        self.entry_frame = ctk.CTkFrame(
            self, height=20, width=300, fg_color="transparent", bg_color="transparent"
        )
        self.entry_value = ctk.StringVar(value="")
        self.selected_fof = ctk.CTkEntry(
            self.entry_frame,
            placeholder_text="",
            height=20,
            width=300,
            textvariable=self.entry_value,
        )
        # self.selected_fof.bind("<KeyRelease>", self.set_copy_location)

        self.button_frame = ctk.CTkFrame(
            self, height=5, width=100, fg_color="transparent", bg_color="transparent"
        )
        self.confirm = ctk.CTkButton(
            self.button_frame,
            text="Confirm",
            font=fonts.buttons_font(),
            width=20,
            height=10,
            command=lambda: self.confirm_button_event(None),
        )
        self.bind("<Return>", self.confirm_button_event)

        self.browse = ctk.CTkButton(
            self.button_frame,
            text="Browse",
            font=fonts.buttons_font(),
            width=20,
            height=10,
            command=lambda: select_fof_event(
                master_frame=self,
                lb_frame=None,
                root_dir=self.entry_value,
                fof="folder",
                export=True,
                update_config=False,
            ),
        )

        self.cancel = ctk.CTkButton(
            self.button_frame,
            text="Cancel",
            width=20,
            font=fonts.buttons_font(),
            height=10,
            command=lambda: self.cancel_button_event(None),
        )
        self.bind("<Escape>", self.cancel_button_event)
        self.plot_elements()

    def plot_elements(self):
        self.label.grid(row=1, column=1, padx=5, pady=5)
        self.entry_frame.grid(row=2, column=1, padx=5, pady=2)
        self.selected_fof.grid(row=1, column=1, padx=5, pady=2)
        self.button_frame.grid(row=3, column=1, padx=5, pady=5)
        self.confirm.grid(row=1, column=1, padx=5, pady=5)
        self.browse.grid(row=1, column=2, padx=5, pady=5)
        self.cancel.grid(row=1, column=3, padx=5, pady=5)

    # def set_copy_location(self, value):
    # ExportConfig.copy_location = self.entry_value.get()

    def confirm_button_event(self, value):
        # self.entryfield.set(value=ExportConfig.copy_location)
        proceed = True
        illegal_symbols = SearchConfig.illegal_search_characters - {":", "\\", "/"}
        if self.selected_fof.get() == "" or any(
            [i in illegal_symbols for i in self.selected_fof.get()]
        ):
            CTkMessagebox(
                title="Error!",
                message=f"Invalid path entered. Must have atleast one character and none of the following symbols: {illegal_symbols}",
                icon="warning",
                option_1="Ok",
            )
            proceed = False

        if proceed:
            copy_files(self.main_lb.curselection(), self.selected_fof.get())

    def cancel_button_event(self, value):
        self.destroy()
