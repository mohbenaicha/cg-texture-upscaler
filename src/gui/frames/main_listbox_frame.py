import os
import tkinter as tk
import customtkinter as ctk
from PIL import Image
from threading import Thread
from typing import List, Tuple, Union
from gui.tooltips import tooltip_text as ttt
from gui.tooltips import Hovertip_Frame
from ..message_box import CTkMessagebox
from gui.frames.top_level_frames import ImageWindow, GoToWindow, CopyFilesWindow
from app_config.config import SearchConfig, GUIConfig
from model.utils import write_log_to_file
from utils.events import print_to_frame
from utils.ctk_fonts import error_font, buttons_font  # , main_lb_items_font
from caches.cache import image_paths_cache as imcache


class TkListbox(ctk.CTkFrame):
    def __init__(self, parent, *args, **kwargs):
        ctk.CTkFrame.__init__(self, parent)

        self.fof_frame = None
        self.filter_frame = None
        self.warn = None  # flag to indicate presence of warning windows to limit them to 1 instance at a time
        self.setup_frame_elements(*args, **kwargs)
        self.plot_self()
        self.plot_frame_elements()

    def setup_frame_elements(self, *args, **kwargs):
        # set up listbox and and scrollbar
        self.listbox = tk.Listbox(self, *args, **kwargs)
        self.listbox_scrollbar = ctk.CTkScrollbar(
            master=self,
            orientation="vertical",
            fg_color="#2E2E2E",
            command=self.listbox.yview,
        )
        self.create_right_click_menu()

        # configure and bind to actions
        self.configure(bg_color="#2E2E2E")
        self.listbox.configure(
            yscrollcommand=self.listbox_scrollbar.set,
            activestyle="none",
            selectbackground="#4F4F4F",
            bd=0,
            # font=main_lb_items_font(),
            bg="#2E2E2E",
            fg="#CDCDC0",
            width=GUIConfig.main_listbox_width,
            height=GUIConfig.main_listbox_height,
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=0,
        )
        self.listbox_scrollbar.configure(width=25)

        self.listbox.bind("<Enter>", self.enter)
        self.listbox.bind("<Leave>", self.leave)
        self.listbox.bind("<Button-3>", self.popup)  # Button-2 on Aqua
        self.listbox.bind("<Escape>", self.deselect_all)  # Button-2 on Aqua
        self.listbox.bind("<Return>", self.preview_image)  # Button-2 on Aqua
        self.listbox.bind("<KeyPress-Shift_L><Delete>", self.delete_unselected)
        self.listbox.bind("<Delete>", self.delete_selected)
        self.listbox.bind("<F5>", self.refresh)
        self.listbox.bind("<KeyPress-Shift_L><O>", self.open_using_default_program)
        self.listbox.bind("<Control-f>", self.go_to_command)
        self.listbox.bind("<Control-c>", self.copy_selected)

        if SearchConfig.last_used_dir_or_file:
            TkListbox.populate(
                self, SearchConfig.last_used_dir_or_file, SearchConfig.recursive
            )

        # button subframe and buttons setup
        self.button_frame = ctk.CTkFrame(
            master=self, fg_color="transparent", bg_color="transparent"
        )

        self.select_all_button = ctk.CTkButton(
            self.button_frame,
            font=buttons_font(),
            width=30,
            height=30,
            text="Select All",
            command=self.select_all,
        )

        self.select_all_button_tt = Hovertip_Frame(
            anchor_widget=self.select_all_button,
            text=ttt.select_all,
            hover_delay=GUIConfig.tooltip_hover_delay,
            bg_color=GUIConfig.tooltip_color,
            text_color=GUIConfig.tooltop_text_color,
        )

        self.clearselection_button = ctk.CTkButton(
            self.button_frame,
            font=buttons_font(),
            width=30,
            height=30,
            text="Deselect All",
            command=lambda: self.deselect_all(None),
        )

        self.clearselection_button_tt = Hovertip_Frame(
            anchor_widget=self.clearselection_button,
            text=ttt.deselect_all,
            hover_delay=GUIConfig.tooltip_hover_delay,
            bg_color=GUIConfig.tooltip_color,
            text_color=GUIConfig.tooltop_text_color,
        )

        self.clearall_button = ctk.CTkButton(
            self.button_frame,
            font=buttons_font(),
            width=30,
            height=30,
            text="Clear All",
            command=lambda: self.delete(0, tk.END),
        )

        self.clearall_button_tt = Hovertip_Frame(
            anchor_widget=self.clearall_button,
            text=ttt.clear_all,
            hover_delay=GUIConfig.tooltip_hover_delay,
            bg_color=GUIConfig.tooltip_color,
            text_color=GUIConfig.tooltop_text_color,
        )

        self.removeselection_button = ctk.CTkButton(
            self.button_frame,
            font=buttons_font(),
            width=30,
            height=30,
            text="Remove Selected",
            command=lambda: self.delete_selected(None),
        )

        self.removeselection_button_tt = Hovertip_Frame(
            anchor_widget=self.removeselection_button,
            text=ttt.remove_selected,
            hover_delay=GUIConfig.tooltip_hover_delay,
            bg_color=GUIConfig.tooltip_color,
            text_color=GUIConfig.tooltop_text_color,
        )

        self.removeunselected_button = ctk.CTkButton(
            self.button_frame,
            font=buttons_font(),
            width=30,
            height=30,
            text="Remove Unselected",
            command=lambda: self.delete_unselected(None),
        )

        self.removeunselected_button_tt = Hovertip_Frame(
            anchor_widget=self.removeunselected_button,
            text=ttt.remove_unselected,
            hover_delay=GUIConfig.tooltip_hover_delay,
            bg_color=GUIConfig.tooltip_color,
            text_color=GUIConfig.tooltop_text_color,
        )

        self.refresh_button = ctk.CTkButton(
            self.button_frame,
            font=buttons_font(),
            width=30,
            height=30,
            text="Refresh All",
            command=lambda: self.refresh(None),
        )

        self.removeunselected_button_tt = Hovertip_Frame(
            anchor_widget=self.refresh_button,
            text=ttt.refresh,
            hover_delay=GUIConfig.tooltip_hover_delay,
            bg_color=GUIConfig.tooltip_color,
            text_color=GUIConfig.tooltop_text_color,
        )

        self.button_frame.error_label = ctk.CTkLabel(
            master=self.button_frame, text=" ", text_color="red", height=15
        )

        # plot ui elements

        self.plot_self()
        self.plot_frame_elements()

    def configure_listbox_variable(self, **kwargs):
        self.listvariable(kwargs.get("listvariable", None))

    def plot_self(self):
        self.grid(row=2, column=1, padx=5, pady=5, sticky="nsw")

    def plot_frame_elements(self):
        self.listbox.grid(column=1, columnspan=4, row=1, sticky="nsw")
        self.listbox_scrollbar.grid(column=5, row=1, sticky="nsw")

        # plot button subframe and buttons
        self.button_frame.grid(column=1, row=2, columnspan=5)
        self.clearall_button.grid(column=1, row=1, padx=2, pady=2)
        self.select_all_button.grid(column=2, row=1, padx=2, pady=2)
        self.clearselection_button.grid(column=3, row=1, padx=2, pady=2)
        self.refresh_button.grid(column=4, row=1, padx=2, pady=2)
        self.removeselection_button.grid(column=1, row=2, columnspan=2, padx=2, pady=2)
        self.removeunselected_button.grid(column=3, row=2, columnspan=2, padx=2, pady=2)
        self.button_frame.error_label.grid(
            column=1, columnspan=5, row=3, padx=5, pady=4
        )

    def listvariable(self, item_list):
        if item_list != None:
            for item in item_list:
                self.listbox.insert(tk.END, item)

    def setexportselection(self, exportselection):
        self.listbox.configure(exportselection=exportselection)

    def setbackground(self, bg):
        if bg != None:
            self.listbox.configure(bg=bg)

    def setforeground(self, fg):
        if fg != None:
            self.listbox.configure(fg=fg)

    def sethighlight(self, highlightcolor):
        if highlightcolor != None:
            self.listbox.configure(highlightcolor=highlightcolor)

    def setselectbackground(self, selectbackground):
        if selectbackground != None:
            self.listbox.configure(selectbackground=selectbackground)

    def enter(self, event):
        self.listbox.config(cursor="hand2")

    def leave(self, event):
        self.listbox.config(cursor="")

    def insert(self, location, item):
        self.listbox.insert(location, item)

    def curselection(self):
        return self.listbox.curselection()

    def delete(self, first, last=None):
        self.listbox.delete(first, last)

    def remove_items(self, clear_cache=True):
        self.listbox.delete(0, tk.END)
        if clear_cache:
            imcache[0].clear()
            imcache[0].clear()
        GUIConfig.lb_cleared = True

    def delete_selected(self, value):
        selected_item = self.listbox.curselection()
        idx_count = 0
        for item in selected_item:
            self.listbox.delete(item - idx_count)
            imcache[0].pop(item - idx_count)
            imcache[1].pop(item - idx_count)
            idx_count += 1

    def delete_unselected(self, value):
        selected_indexes = self.listbox.curselection()
        no_selected_indexes = len(selected_indexes)

        selected_image_names = [self.listbox.get(i, None) for i in selected_indexes]
        self.remove_items(clear_cache=False)
        self.listvariable(selected_image_names)
        counter = 0

        for img_idx in range(len(imcache[0])):
            try:
                if img_idx != selected_indexes[counter]:
                    imcache[0].pop(counter)
                    imcache[1].pop(counter)
                else:
                    counter += 1
            except IndexError:
                imcache[0].pop(counter)
                imcache[1].pop(counter)

    def select_all(self):
        self.listbox.select_set(0, tk.END)

    def deselect_all(self, value):
        self.listbox.select_clear(0, tk.END)

    @classmethod
    def handle_recursive_dir_walk(
        cls,
        obj,
        parent: Union[str, None] = None,
        imcache: Union[Tuple[List[str], List[str]], None] = None,
        update_lb: bool = True,
    ):
        for element in os.walk(parent):
            imcache[0].extend(element[2])
            imcache[1].extend([element[0]] * len(element[2]))

        if update_lb and obj:
            obj.remove_items(clear_cache=False)
            obj.configure_listbox_variable(listvariable=imcache[0])
        # if not obj:
        #     return imcache

    @classmethod
    def handle_single_dir(
        cls,
        obj,
        parent: Union[str, None] = None,
        imcache: Union[Tuple[List[str], List[str]], None] = None,
        update_lb: bool = True,
    ):
        for file in os.listdir(parent):
            if os.path.isfile(os.path.join(parent, file)):
                imcache[0].append(file)
                imcache[1].append(parent)

        if update_lb and obj:
            obj.remove_items(clear_cache=False)
            obj.configure_listbox_variable(listvariable=imcache[0])

    @classmethod
    def handle_single_file(
        cls,
        obj,
        parent: Union[str, None] = None,
        imcache: Union[Tuple[List[str], List[str]], None] = None,
        update_lb: bool = True,
    ):
        components = parent.split("/")
        fp, fn = "\\".join(components[:-1]), components[-1:][0]
        imcache[0].append(fn)
        imcache[1].append(fp)
        if update_lb and obj:
            obj.configure_listbox_variable(listvariable=imcache[0])

    @classmethod
    def populate(cls, obj, parent, recursive, add=False, thread=True):
        def populate_task():
            imcache[0].clear()
            imcache[1].clear()

            if os.path.isdir(parent):
                if recursive:
                    TkListbox.handle_recursive_dir_walk(
                        obj, parent, imcache, update_lb=True  # False
                    )
                else:
                    TkListbox.handle_single_dir(
                        obj, parent, imcache, update_lb=True
                    )  # False)
            else:  # otherwise, we're dealing with a file
                TkListbox.handle_single_file(
                    obj, parent, imcache, update_lb=True
                )  # False)

        if thread:
            Thread(target=populate_task).start()
        else:
            image_map = populate_task()
            return image_map

    def add_files(self):
        raise NotImplementedError

    @classmethod
    def filter(
        cls, obj, and_filters: List[str], or_filters: List[str], source_list: str
    ):
        and_filters: List[str] = [filter for filter in and_filters if len(filter) > 0]
        or_filters: List[str] = [filter for filter in or_filters if len(filter) > 0]
        len_and, len_or = len(and_filters), len(or_filters)

        if not source_list == "current_list":
            imcache[0].clear()
            imcache[1].clear()
            if SearchConfig.last_used_dir_or_file != "":
                if SearchConfig.recursive:
                    TkListbox.handle_recursive_dir_walk(
                        obj if obj else None,
                        SearchConfig.last_used_dir_or_file,
                        imcache,
                        update_lb=False if not obj else True,
                    )
                else:
                    TkListbox.handle_single_dir(
                        obj if obj else None,
                        SearchConfig.last_used_dir_or_file,
                        imcache,
                        update_lb=False if not obj else True,
                    )

        keep_idx = 0
        remaining = len(imcache[0])
        while remaining > keep_idx:
            file = imcache[0][keep_idx]
            and_true = all([filter_txt in file for filter_txt in and_filters])
            or_true = any([filter_txt in file for filter_txt in or_filters])

            if (
                (and_true and not len_and == 0)
                or (or_true and not or_true == 0)
                or (len_and == 0 and len_or == 0)
            ):
                keep_idx += 1
            else:
                remaining -= 1
                del imcache[0][keep_idx]
                del imcache[1][keep_idx]

        if obj:
            obj.remove_items(None)
            obj.configure_listbox_variable(listvariable=imcache[0])

    def refresh(self, value):
        if SearchConfig.last_used_dir_or_file:
            # using bruteforce to reread the directory
            print_to_frame(
                frame=self.button_frame,
                grid=True,
                lbl_width=50,
                lbl_height=15,
                string="",
                error=True,
                columnspan=4,
            )
            TkListbox.populate(
                obj=self,
                parent=SearchConfig.last_used_dir_or_file,
                recursive=SearchConfig.recursive,
                add=False,
            )
        else:
            print_to_frame(
                frame=self.button_frame,
                grid=True,
                string="No file or directory selected",
                error=False,
                font=error_font(),
                text_color="red",
                lbl_width=50,
                lbl_height=15,
                column=1,
                columnspan=4,
                row=3,
                padx=5,
                pady=4,
            )

    # right-click menu commands
    def create_right_click_menu(self):
        self.listbox.popup_menu = tk.Menu(
            self.listbox,
            tearoff=0,
            background="#2E2E2E",
            foreground="#CDCDC0",
            relief=None,
        )
        self.listbox.popup_menu.add_command(
            label="Preview Selected (Enter)",
            command=lambda: self.preview_image(None),
            foreground="white",
        )
        self.listbox.popup_menu.add_command(
            label="Open Selected File Location",
            command=self.open_file_in_location,
            foreground="white",
        )
        self.listbox.popup_menu.add_command(
            label="Open Selected Using Default Program (Shift + O)",
            foreground="white",
            command=lambda: self.open_using_default_program(None),
        )
        self.listbox.popup_menu.add_command(
            label="Find (CTRL + F)",
            command=lambda: self.go_to_command(None),
            foreground="white",
        )

        self.listbox.popup_menu.add_command(
            label="Copy selected file(s) to (CTRL + C)",
            command=lambda: self.copy_selected(None),
            foreground="white",
        )

    def popup(self, event):
        try:
            self.listbox.popup_menu.tk_popup(event.x_root, event.y_root, 0)
        finally:
            self.listbox.popup_menu.grab_release()

    def open_using_default_program(self, value):
        selection = self.curselection()
        len_selection = len(self.curselection())
        open = False

        if len_selection == 1:
            open = True
        elif len_selection > 1:
            warn = CTkMessagebox(
                title="Warning!",
                message=f"You are about to open {len(selection)} image(s). Proceed?",
                icon="warning",
                option_1="Yes",
                option_2="Cancel",
            )
            if warn.get() == "Yes":
                open = True
            else:
                pass
        if open:
            for idx in selection:
                pth = imcache[1][idx]
                file_path = os.path.join(pth, imcache[0][idx])
                os.startfile(file_path)

    def open_file_in_location(self):
        selection = self.curselection()
        len_selection = len(self.curselection())
        open = False

        if len_selection == 1:
            open = True
        elif len_selection > 1:
            warn = CTkMessagebox(
                title="Warning!",
                message=f"You are about to open the location(s) of ({len(selection)}) image(s). Proceed?",
                icon="warning",
                option_1="Yes",
                option_2="Cancel",
            )
            if warn.get() == "Yes":
                open = True
            else:
                pass
        if open:
            for idx in selection:
                pth = imcache[1][idx]
                pth = os.path.realpath(pth)
                os.startfile(pth)

    def preview_image(self, value):
        log_file = write_log_to_file(None, None, None)
        selection = self.curselection()
        len_selection = len(self.curselection())
        open = False

        if len_selection == 1:
            open = True
        elif len_selection > 1:
            if self.warn == None or not self.warn.winfo_exists():
                self.warn = CTkMessagebox(
                    title="Warning Message!",
                    message=f"You are about to preview ({len(selection)}) image(s). Proceed?",
                    icon="warning",
                    option_1="Yes",
                    option_2="Cancel",
                )
                if self.warn.get() == "Yes":
                    open = True
                else:
                    pass
        if open:
            for idx in selection:
                try:
                    image_to_open = os.path.join(imcache[1][idx], imcache[0][idx])
                    raw_img = Image.open(image_to_open)
                except Exception as e:
                    CTkMessagebox(
                        title="Warning Message!",
                        message=f"Could not open image! Please see logs.",
                        icon="warning",
                        option_1="Ok",
                    )
                    write_log_to_file(
                        "Error",
                        f"Could not open {imcache[0][idx]} due to the following error: {e}. \n (path: {image_to_open})",
                        log_file,
                    )
                    continue

                w, h = raw_img.size
                im_h = max(min(h, 512), 256)
                im_w = max(min(w, 512), 256)
                ctk_img = ctk.CTkImage(
                    light_image=raw_img, dark_image=raw_img, size=(im_w, im_h)
                )
                self.toplevel_window = ImageWindow(
                    im_name=image_to_open,
                    image=ctk_img,
                    orig_size=((h, w)),
                    width=im_w,
                    height=im_h,
                    mode=raw_img.mode,
                )  # create window if its None or destroyed

                self.toplevel_window.attributes("-topmost", 1)
                self.toplevel_window.focus()

    def go_to_command(self, value):
        self.toplevel_window = GoToWindow(main_lb=self)
        self.toplevel_window.attributes("-topmost", 1)
        self.toplevel_window.focus()

    def copy_selected(self, value):
        if len(self.curselection()) == 0:
            self.warn = CTkMessagebox(
                title="Warning Message!",
                message=f"You must select the file(s) that you wish to copy from the listbox!",
                icon="warning",
                option_1="Ok",
            )
        self.toplevel_window = CopyFilesWindow(main_lb=self)
        self.toplevel_window.attributes("-topmost", 1)
        self.toplevel_window.focus()
