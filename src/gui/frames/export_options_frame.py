from tkinter import *
import customtkinter as ctk
import utils.ctk_fonts as fonts
from gui.tooltips import Hovertip_Frame
from gui.frames.main_listbox_frame import TkListbox
from app_config.config import ExportConfig, PrePostProcessingConfig, GUIConfig
from utils.events import *
import gui.tooltips.tooltip_text as ttt


class ExportOptionsFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        # options variable definitions
        self.lb_frame: TkListbox = kwargs.get("lb_frame")
        self.height: int = kwargs.get("height")
        self.width: int = kwargs.get("width")
        self.device = ctk.StringVar(value=ExportConfig.device)
        self.scale = ctk.StringVar(value=ExportConfig.scale)
        self.format = ctk.StringVar(value=ExportConfig.export_format)
        self.compression = ctk.StringVar(value=ExportConfig.compression)
        self.mipmaps = ctk.StringVar(value=ExportConfig.mipmaps)
        self.prefix = ctk.StringVar(value=ExportConfig.save_prefix)
        self.suffix = ctk.StringVar(value=ExportConfig.save_suffix)
        self.numbered = ctk.BooleanVar(value=ExportConfig.save_numbering)

        self.setup_frame()
        self.plot_self()
        self.plot_frame_elements()

    def setup_frame(self):
        self.setup_subframes()

    def setup_subframes(self):
        self.options_label_frame = ctk.CTkFrame(
            self, fg_color="transparent", height=5, width=150
        )
        self.device_subframe = ctk.CTkFrame(
            self, fg_color="transparent", height=10, width=150
        )
        self.scale_subframe = ctk.CTkFrame(
            self, fg_color="transparent", height=10, width=150
        )
        self.format_subframe = ctk.CTkFrame(
            self, fg_color="transparent", height=10, width=150
        )
        self.compression_subframe = ctk.CTkFrame(
            self, fg_color="transparent", height=10, width=150
        )
        self.additional_options_subframe = ctk.CTkFrame(
            self, fg_color="transparent", height=10, width=150
        )
        self.export_naming_subframe = ctk.CTkFrame(
            self, fg_color="transparent", height=10, width=150
        )
        self.export_numbering_subframe = ctk.CTkFrame(
            self, fg_color="transparent", height=10, width=150
        )
        self.export_prefix_subframe = ctk.CTkFrame(
            self, fg_color="transparent", height=10, width=150
        )
        self.export_suffix_subframe = ctk.CTkFrame(
            self, fg_color="transparent", height=10, width=150
        )

        self.setup_subframe_elements()

    def setup_subframe_elements(self):
        self.options_label_frame.label = ctk.CTkLabel(
            self.options_label_frame,
            font=fonts.header_labels_font(),
            text="➌ Export Options",
            width=1,
        )

        # scale dropdown
        self.device_subframe.label = ctk.CTkLabel(
            self.device_subframe,
            font=fonts.options_font(),
            text="Device   ",
            height=20,
            width=60,
        )
        self.device_subframe.menu = ctk.CTkOptionMenu(
            self.device_subframe,
            values=ExportConfig.available_devices,
            dynamic_resizing=False,
            command=self.set_device,
            variable=self.device,
            height=20,
            width=60,
            font=fonts.buttons_font(),
        )
        self.device_subframe.menu.set(value=ExportConfig.device)
        self.device_subframe.menu_tt = Hovertip_Frame(
            anchor_widget=self.device_subframe.label,
            text=ttt.device,
            hover_delay=GUIConfig.tooltip_hover_delay,
            bg_color=GUIConfig.tooltip_color,
            text_color=GUIConfig.tooltop_text_color,
        )

        # scale dropdown
        self.scale_subframe.label = ctk.CTkLabel(
            self.scale_subframe,
            font=fonts.options_font(),
            text="Upscale   ",
            height=20,
            width=50,
        )
        self.scale_subframe.menu = ctk.CTkOptionMenu(
            self.scale_subframe,
            values=PrePostProcessingConfig.available_scales,
            dynamic_resizing=False,
            command=self.set_scale,
            variable=self.scale,
            height=20,
            width=60,
            font=fonts.buttons_font(),
        )
        self.scale_subframe.menu.set(value=ExportConfig.scale)
        self.scale_subframe.menu_tt = Hovertip_Frame(
            anchor_widget=self.scale_subframe.label,
            text=ttt.scale,
            hover_delay=GUIConfig.tooltip_hover_delay,
            bg_color=GUIConfig.tooltip_color,
            text_color=GUIConfig.tooltop_text_color,
        )

        # format dropdown
        self.format_subframe.label = ctk.CTkLabel(
            master=self.format_subframe,
            font=fonts.options_font(),
            text="Export format  ",
            height=20,
            width=50,
        )
        self.format_subframe.menu = ctk.CTkOptionMenu(
            master=self.format_subframe,
            dynamic_resizing=False,
            values=PrePostProcessingConfig.available_export_formats,
            command=self.set_format,
            variable=self.format,
            height=20,
            width=60,
            font=fonts.buttons_font(),
        )
        self.format_subframe.menu.set(value=ExportConfig.export_format)
        self.format_subframe.menu_tt = Hovertip_Frame(
            anchor_widget=self.format_subframe.label,
            text=ttt.format,
            hover_delay=GUIConfig.tooltip_hover_delay,
            bg_color=GUIConfig.tooltip_color,
            text_color=GUIConfig.tooltop_text_color,
        )

        # compression buttons
        self.compression_subframe.label = ctk.CTkLabel(
            self.compression_subframe,
            font=fonts.options_font(),
            text="Compression ",
            height=20,
            width=50,
        )
        self.compression_subframe.menu = ctk.CTkOptionMenu(
            master=self.compression_subframe,
            dynamic_resizing=False,
            values=ExportConfig.active_compression,
            command=self.set_compression,
            variable=self.compression,
            height=20,
            width=60,
            font=fonts.buttons_font(),
        )
        self.set_compression(ExportConfig.compression)
        # self.compression_subframe.menu.set(value=ExportConfig.compression)
        self.compression_subframe.menu_tt = Hovertip_Frame(
            anchor_widget=self.compression_subframe.label,
            text=ttt.compression,
            hover_delay=GUIConfig.tooltip_hover_delay,
            bg_color=GUIConfig.tooltip_color,
            text_color=GUIConfig.tooltop_text_color,
        )

        # additional options - mipmaps entry field
        self.additional_options_subframe.label = ctk.CTkLabel(
            master=self.additional_options_subframe,
            font=fonts.options_font(),
            text="Mipmaps  ",
            height=20,
            width=50,
        )
        self.additional_options_subframe.menu = ctk.CTkOptionMenu(
            master=self.additional_options_subframe,
            dynamic_resizing=False,
            values=PrePostProcessingConfig.mipmap_levels,
            command=self.set_mipmaps,
            variable=self.mipmaps,
            height=20,
            width=60,
            font=fonts.buttons_font(),
        )
        self.additional_options_subframe.menu.set(value=ExportConfig.mipmaps)
        self.additional_options_subframe.menu_tt = Hovertip_Frame(
            anchor_widget=self.additional_options_subframe.label,
            text=ttt.mipmaps,
            hover_delay=GUIConfig.tooltip_hover_delay,
            bg_color=GUIConfig.tooltip_color,
            text_color=GUIConfig.tooltop_text_color,
        )

        # file naming fields
        self.export_numbering_subframe.numbered_label = ctk.CTkLabel(
            master=self.export_numbering_subframe,
            font=fonts.options_font(),
            text="Numbering",
            height=20,
            width=50,
        )
        self.export_numbering_subframe.numbered_checkbox = ctk.CTkCheckBox(
            master=self.export_numbering_subframe,
            variable=self.numbered,
            command=lambda: self.set_numbering(self.numbered),
            text="",
            height=15,
            width=40,
            checkbox_height=18,
            checkbox_width=18,
            border_width=2,
        )
        self.export_numbering_subframe.numbered_checkbox.select() if ExportConfig.save_numbering else self.export_numbering_subframe.numbered_checkbox.deselect()
        self.export_numbering_subframe.numbered_checkbox_tt = Hovertip_Frame(
            anchor_widget=self.export_numbering_subframe.numbered_label,
            text=ttt.numbered_checkbox,
            hover_delay=GUIConfig.tooltip_hover_delay,
            bg_color=GUIConfig.tooltip_color,
            text_color=GUIConfig.tooltop_text_color,
        )

        self.export_prefix_subframe.prefix_field_label = ctk.CTkLabel(
            master=self.export_prefix_subframe,
            font=fonts.options_font(),
            text="Prefix    ",
            height=20,
            width=50,
        )
        self.export_prefix_subframe.prefix_field = ctk.CTkEntry(
            master=self.export_prefix_subframe, height=20, width=60
        )
        self.export_prefix_subframe.prefix_field.insert(0, ExportConfig.save_prefix)
        self.export_prefix_subframe.prefix_field.bind("<KeyRelease>", self.set_prefix)
        self.export_prefix_subframe.prefix_tt = Hovertip_Frame(
            anchor_widget=self.export_prefix_subframe.prefix_field_label,
            text=ttt.prefix,
            hover_delay=GUIConfig.tooltip_hover_delay,
            bg_color=GUIConfig.tooltip_color,
            text_color=GUIConfig.tooltop_text_color,
        )

        self.export_suffix_subframe.suffix_field_label = ctk.CTkLabel(
            master=self.export_suffix_subframe,
            font=fonts.options_font(),
            text="Suffix    ",
            height=20,
            width=50,
        )
        self.export_suffix_subframe.suffix_field = ctk.CTkEntry(
            master=self.export_suffix_subframe, height=20, width=60
        )
        self.export_suffix_subframe.suffix_field.insert(0, ExportConfig.save_suffix)
        self.export_suffix_subframe.suffix_field.bind("<KeyRelease>", self.set_suffix)
        self.export_suffix_subframe.numbered_checkbox_tt = Hovertip_Frame(
            anchor_widget=self.export_suffix_subframe.suffix_field_label,
            text=ttt.suffix,
            hover_delay=GUIConfig.tooltip_hover_delay,
            bg_color=GUIConfig.tooltip_color,
            text_color=GUIConfig.tooltop_text_color,
        )

    def set_device(self, value):
        ExportConfig.device = value

    def set_scale(self, value):
        ExportConfig.scale = value

    def set_format(self, value):
        ExportConfig.export_format = value
        supported_compression = list(PrePostProcessingConfig.compression_map[value])
        self.compression_subframe.menu.configure(values=supported_compression)
        self.compression.set(value=supported_compression[0])
        self.compression_subframe.menu.set(value=supported_compression[0])

        if not PrePostProcessingConfig.supports_mipmaps[value]:
            self.mipmaps.set(value="none")
            disable_UI_elements(self.additional_options_subframe.menu)
        else:
            self.mipmaps.set(value=PrePostProcessingConfig.mipmap_levels[0])
            enable_UI_elements(self.additional_options_subframe.menu)

    def set_compression(self, value):
        ExportConfig.compression = value

    def set_mipmaps(self, value):
        ExportConfig.mipmaps = value

    def set_numbering(self, value):
        ExportConfig.save_numbering = self.numbered.get()

    def set_prefix(self, value):
        curr_entry = self.export_prefix_subframe.prefix_field.get()
        if not curr_entry == ExportConfig.save_prefix:
            legal_string = "".join(
                [
                    char
                    for char in curr_entry
                    if not char in SearchConfig.illegal_search_characters
                ]
            )
            self.export_prefix_subframe.prefix_field.delete(0, ctk.END)
            self.export_prefix_subframe.prefix_field.insert(0, legal_string)

            ExportConfig.save_prefix = legal_string  # self.prefix.get()

    def set_suffix(self, value):
        curr_entry = self.export_suffix_subframe.suffix_field.get()
        if not curr_entry == ExportConfig.save_suffix:
            legal_string = "".join(
                [
                    char
                    for char in curr_entry
                    if not char in SearchConfig.illegal_search_characters
                ]
            )

            self.export_suffix_subframe.suffix_field.delete(0, ctk.END)
            self.export_suffix_subframe.suffix_field.insert(0, legal_string)

            ExportConfig.save_suffix = legal_string  # self.suffix.get()

    def get_export_list(self):
        return self.lb_frame.listbox.getselected()

    def plot_self(self):
        self.grid(column=1, row=2, padx=5, pady=10, sticky="new")

    def plot_frame_elements(self):
        # plot subframes
        self.options_label_frame.grid(row=0, column=0, padx=38, pady=5, sticky="new")
        self.device_subframe.grid(row=1, column=0, padx=35, pady=5, sticky="new")
        self.scale_subframe.grid(row=2, column=0, padx=35, pady=5, sticky="new")
        self.format_subframe.grid(row=3, column=0, padx=35, pady=5, sticky="new")
        self.compression_subframe.grid(row=4, column=0, padx=35, pady=5, sticky="new")
        self.additional_options_subframe.grid(
            row=5, column=0, padx=35, pady=5, sticky="new"
        )
        self.export_numbering_subframe.grid(
            row=6, column=0, padx=35, pady=5, sticky="new"
        )
        self.export_prefix_subframe.grid(row=7, column=0, padx=35, pady=5, sticky="new")
        self.export_suffix_subframe.grid(row=8, column=0, padx=35, pady=9, sticky="new")

        # plot subframe elements
        self.options_label_frame.label.grid(row=0, column=0, padx=20, sticky="ew")

        # device dropdown
        self.device_subframe.label.pack(side=LEFT)
        self.device_subframe.menu.pack(side=RIGHT)

        # scale dropdown
        self.scale_subframe.label.pack(side=LEFT)
        self.scale_subframe.menu.pack(side=RIGHT)

        # format dropdown
        self.format_subframe.label.pack(side=LEFT)
        self.format_subframe.menu.pack(side=RIGHT)

        # compression dropdown
        self.compression_subframe.label.pack(side=LEFT)
        self.compression_subframe.menu.pack(side=RIGHT)

        # additional options - mipmaps options menu
        self.additional_options_subframe.label.pack(side=LEFT)
        self.additional_options_subframe.menu.pack(side=RIGHT)

        # file naming fields
        self.export_prefix_subframe.prefix_field_label.pack(
            side=LEFT
        )  # .grid(row=0, column=0, padx=2, pady=2,sticky='w')
        self.export_prefix_subframe.prefix_field.pack(
            side=RIGHT
        )  # .grid(row=0, column=0, padx=2, pady=2,sticky='e')
        self.export_suffix_subframe.suffix_field_label.pack(
            side=LEFT
        )  # .grid(row=1, column=0, padx=2, pady=2,sticky='w')
        self.export_suffix_subframe.suffix_field.pack(
            side=RIGHT
        )  # .grid(row=1, column=0, padx=2, pady=2,sticky='e')
        self.export_numbering_subframe.numbered_label.pack(
            side=LEFT
        )  # .grid(row=2, column=0, padx=2, pady=2,stick='w')
        self.export_numbering_subframe.numbered_checkbox.pack(
            side=RIGHT
        )  # .grid(row=2, column=0, padx=2, pady=2,sticky='e')
