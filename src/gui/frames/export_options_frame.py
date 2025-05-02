from typing import TYPE_CHECKING
from tkinter import *
import customtkinter as ctk
import math
import gui.ctk_fonts as fonts
from gui.tooltips import Hovertip_Frame
from app_config.config import ExportConfig, ConfigReference, GUIConfig
from utils.events import *
import gui.tooltips.tooltip_text as ttt

if TYPE_CHECKING:
    from gui.frames import TkListbox, AdditionalOptionsFrame


class ExportOptionsFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        # options variable definitions
        self.lb_frame: TkListbox = kwargs.get("lb_frame")
        self.addit_sett_subframe: AdditionalOptionsFrame = kwargs.get(
            "addit_sett_subframe"
        )
        self.height: int = kwargs.get("height")
        self.width: int = kwargs.get("width")
        self.scale = ctk.StringVar(value=ExportConfig.scale)
        self.format = ctk.StringVar(value=ExportConfig.export_format)
        self.cat_compression_value = ctk.StringVar(value=ExportConfig.compression)
        self.num_compression_value = ctk.IntVar(value=0)
        self.noise = ctk.DoubleVar(value=ExportConfig.noise_level)
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
        self.format_specific = ctk.CTkFrame(
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
        self.denoise_subframe = ctk.CTkFrame(
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
        self.scale_subframe.label = ctk.CTkLabel(
            self.scale_subframe,
            font=fonts.options_font(),
            text="Upscale   ",
            anchor="w",
            height=20,
            width=180,
        )
        self.scale_subframe.menu = ctk.CTkOptionMenu(
            self.scale_subframe,
            values=ConfigReference.available_scales,
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
            values=ConfigReference.available_export_formats,
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
            text="Compression",
            height=20,
            width=50,
        )
        self.compression_subframe.menu = ctk.CTkOptionMenu(
            master=self.compression_subframe,
            dynamic_resizing=False,
            values=ExportConfig.active_compression,
            command=self.set_compression,
            variable=self.cat_compression_value,
            height=20,
            width=60,
            font=fonts.buttons_font(),
        )

        self.compression_subframe.menu.configure(
            values=confref.discrete_compression_map["tga"]
        )
        self.compression_subframe.menu.set(confref.discrete_compression_map["tga"][0])
        self.set_compression("none")

        # self.compression_subframe.menu.set(value=ExportConfig.compression)
        self.compression_subframe.menu_tt = Hovertip_Frame(
            anchor_widget=self.compression_subframe.label,
            text=ttt.compression,
            hover_delay=GUIConfig.tooltip_hover_delay,
            bg_color=GUIConfig.tooltip_color,
            text_color=GUIConfig.tooltop_text_color,
        )

        # denoise slider
        self.denoise_subframe.label = ctk.CTkLabel(
            self.denoise_subframe,
            font=fonts.options_font(),
            text=f"Noise {round(ExportConfig.noise_level,1)}",
            height=20,
            width=50,
        )
        self.denoise_subframe.slider = ctk.CTkSlider(
            master=self.denoise_subframe,
            from_=0.0,
            to=1.0,
            number_of_steps=100,
            command=self.set_noise,
            variable=self.noise,
            height=20,
            width=100,
        )
        self.set_noise(ExportConfig.noise_level)

        # png compression label/slider
        self.compression_subframe.png_label = ctk.CTkLabel(
            self.compression_subframe,
            font=fonts.options_font(),
            text=f"Compression ({ExportConfig.compression}) ",
            height=20,
            width=50,
        )
        self.compression_subframe.png_slider = ctk.CTkSlider(
            master=self.compression_subframe,
            from_=0,
            to=9,
            number_of_steps=10,
            command=self.set_compression,
            variable=self.num_compression_value,
            height=20,
            width=100,
        )
        self.compression_subframe.menu_tt = Hovertip_Frame(
            anchor_widget=self.compression_subframe.label,
            text=ttt.png_compression,
            hover_delay=GUIConfig.tooltip_hover_delay,
            bg_color=GUIConfig.tooltip_color,
            text_color=GUIConfig.tooltop_text_color,
        )
        # jpg compression label/slider
        self.compression_subframe.jpg_label = ctk.CTkLabel(
            self.compression_subframe,
            font=fonts.options_font(),
            text=f"Quality ({ExportConfig.compression})",
            height=20,
            width=50,
        )
        self.compression_subframe.jpg_slider = ctk.CTkSlider(
            master=self.compression_subframe,
            from_=0,
            to=100,
            number_of_steps=100,
            command=self.set_compression,
            variable=self.num_compression_value,
            height=20,
            width=100,
        )
        self.compression_subframe.menu_tt = Hovertip_Frame(
            anchor_widget=self.compression_subframe.label,
            text=ttt.jpg_compression,
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
            values=ConfigReference.mipmap_levels,
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

    def set_scale(self, value):
        ExportConfig.scale = value

    def set_format(self, value):
        ExportConfig.export_format = value

        # compression
        self.compression_subframe.grid_remove()

        if value in confref.available_export_formats[:4]:
            self.plot_compression_frame_and_elements()
            self.compression_subframe.menu.configure(
                values=confref.discrete_compression_map[value]
            )
            # self.compression_subframe.menu.set("none")
            self.set_compression(confref.discrete_compression_map[value][0])

        elif value == "png":  # png
            self.plot_png_compression_frame_and_elements(0)
            self.set_compression(0)
        else:  # jpg
            self.set_compression(100)
            self.plot_jpg_compression_frame_and_elements(100)

        # mipmaps
        if not value == "dds":
            ExportConfig.mipmaps = "none"
            self.additional_options_subframe.grid_remove()
        else:
            self.mipmaps.set(value="none")
            self.plot_additional_options_subframe_and_elements()
            self.additional_options_subframe.menu.configure(
                values=confref.mipmap_levels
            )
            # self.set_mipmaps('none')
            self.additional_options_subframe.menu.set("none")

        # color_depth
        if value in ["tga", "dds", "bmp", "jpg"]:
            menu_options, set_value = [
                "8",
            ], "8"
        elif value in ["png"]:
            menu_options, set_value = ["8", "16"], "8"
        else:
            menu_options, set_value = ["16", "32"], "32"
        self.addit_sett_subframe.plot_color_depth_subframe_and_elements(
            menu_options, set_value
        )

        # color_mode
        if value == "dds":
            modes = ["RGBA"]
        elif value == "jpg":
            modes = ["RGB", "Greyscale"]
        elif value == "bmp":
            modes = ["RGBA", "RGB"]
        else:
            modes = ["RGBA", "RGB", "Greyscale"]

        self.addit_sett_subframe.plot_color_mode_subframe_and_elements(modes, modes[0])

    def set_compression(self, value):
        # supported compression algos based on export format

        # handling UI for "range" compression that has ordinal categories (png) or a large discrete range (jpg quality)
        # the same is not required for compression algos that are nominal categories (dds, exr, bmp, tga)
        if ExportConfig.export_format in list(confref.range_compression_map.keys()):
            type = "{0} ({1})".format(
                "Quality" if ExportConfig.export_format == "jpg" else "Compression",
                int(round(value, 0)),
            )
            print_to_frame(
                self.compression_subframe.png_label
                if ExportConfig.export_format == "png"
                else self.compression_subframe.jpg_label,
                grid=False,
                side=LEFT,
                string=type,
                error=False,
                font=fonts.labels_font(),
                text_color="white",
                lbl_height=15,
                lbl_width=50,
            )
            value = int(round(value, 0))
            self.compression_subframe.png_slider.set(value)
            self.compression_subframe.jpg_slider.set(value)

        ExportConfig.compression = value
        self.compression_subframe.menu.set(value)

        if ExportConfig.export_format == "dds":
            if ExportConfig.compression == "none" and ExportConfig.mipmaps == "none":
                modes = ["RGBA", "RGB"]
            else:
                modes = ["RGBA"]
        elif ExportConfig.export_format == "bmp":
            if ExportConfig.compression == "rle":
                modes = ["Indexed"]
            else:
                modes = ["RGBA", "RGB"]
        else:
            modes = "skip"

        if not modes == "skip":
            self.addit_sett_subframe.plot_color_mode_subframe_and_elements(
                modes, modes[0]
            )

    def set_noise(self, value):
        print_to_frame(
            self.denoise_subframe.label,
            grid=False,
            side=LEFT,
            string=f"Noise ({round(value, 2)})",
            error=False,
            font=fonts.labels_font(),
            text_color="white",
            lbl_height=15,
            lbl_width=50,
        )
        if not value == 0:
            ExportConfig.noise_level = round(
               (1 - ((1-value)/5))**2, 2
            )
        else:
            ExportConfig.noise_level = 0.0

    def set_mipmaps(self, value):
        ExportConfig.mipmaps = value
        if ExportConfig.export_format == "dds":
            if ExportConfig.mipmaps == "none" and ExportConfig.compression == "none":
                modes, set_value = ["RGBA", "RGB"], "RGBA"
            else:
                modes, set_value = ["RGBA"], "RGBA"

            self.addit_sett_subframe.plot_color_mode_subframe_and_elements(
                modes, set_value
            )

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

            ExportConfig.save_suffix = legal_string

    def get_export_list(self):
        return self.lb_frame.listbox.getselected()

    def plot_self(self):
        self.grid(column=1, row=2, padx=5, pady=10, sticky="new")

    def plot_frame_elements(self):
        # plot subframes

        # label
        self.options_label_frame.grid(row=0, column=0, padx=38, pady=5, sticky="new")
        # scale
        self.scale_subframe.grid(row=1, column=0, padx=35, pady=5, sticky="new")
        # format
        self.format_subframe.grid(row=2, column=0, padx=35, pady=5, sticky="new")
        # compression
        self.plot_compression_frame_and_elements()
        # noise
        self.denoise_subframe.grid(row=5, column=0, padx=35, pady=5, sticky="new")
        # naming
        self.export_numbering_subframe.grid(
            row=6, column=0, padx=35, pady=5, sticky="new"
        )
        self.export_prefix_subframe.grid(row=7, column=0, padx=35, pady=5, sticky="new")
        self.export_suffix_subframe.grid(row=8, column=0, padx=35, pady=9, sticky="new")

        # plot subframe elements
        self.options_label_frame.label.grid(row=0, column=0, padx=20, sticky="ew")

        # scale dropdown
        self.scale_subframe.label.pack(side=LEFT)
        self.scale_subframe.menu.pack(side=RIGHT)

        # format dropdown
        self.format_subframe.label.pack(side=LEFT)
        self.format_subframe.menu.pack(side=RIGHT)

        # denoise slider
        self.denoise_subframe.label.pack(side=LEFT)
        self.denoise_subframe.slider.pack(side=RIGHT)

        # file naming fields
        self.export_prefix_subframe.prefix_field_label.pack(side=LEFT)
        self.export_prefix_subframe.prefix_field.pack(side=RIGHT)
        self.export_suffix_subframe.suffix_field_label.pack(side=LEFT)
        self.export_suffix_subframe.suffix_field.pack(side=RIGHT)
        self.export_numbering_subframe.numbered_label.pack(side=LEFT)
        self.export_numbering_subframe.numbered_checkbox.pack(side=RIGHT)

    def plot_jpg_compression_frame_and_elements(self, value):
        self.compression_subframe.menu.pack_forget()
        self.compression_subframe.label.pack_forget()
        self.compression_subframe.png_label.pack_forget()
        self.compression_subframe.png_slider.pack_forget()

        self.compression_subframe.grid(row=3, column=0, padx=35, pady=5, sticky="new")
        self.compression_subframe.jpg_label.pack(side=LEFT)
        self.compression_subframe.jpg_slider.pack(side=RIGHT)
        self.compression_subframe.jpg_slider.set(value)

    def plot_png_compression_frame_and_elements(self, value):
        # compression dropdown
        self.compression_subframe.menu.pack_forget()
        self.compression_subframe.label.pack_forget()
        self.compression_subframe.jpg_label.pack_forget()
        self.compression_subframe.jpg_slider.pack_forget()

        self.compression_subframe.grid(row=3, column=0, padx=35, pady=5, sticky="new")
        self.compression_subframe.png_label.pack(side=LEFT)
        self.compression_subframe.png_slider.pack(side=RIGHT)
        self.compression_subframe.png_slider.set(value)

    def plot_compression_frame_and_elements(self):
        # compression dropdown
        self.compression_subframe.jpg_label.pack_forget()
        self.compression_subframe.jpg_slider.pack_forget()
        self.compression_subframe.png_label.pack_forget()
        self.compression_subframe.png_slider.pack_forget()

        self.compression_subframe.grid(row=3, column=0, padx=35, pady=5, sticky="new")
        self.compression_subframe.label.pack(side=LEFT)
        self.compression_subframe.menu.pack(side=RIGHT)

    def plot_additional_options_subframe_and_elements(self):
        self.additional_options_subframe.grid(
            row=4, column=0, padx=35, pady=5, sticky="new"
        )
        # additional options - mipmaps options menu
        self.additional_options_subframe.label.pack(side=LEFT)
        self.additional_options_subframe.menu.pack(side=RIGHT)
        self.additional_options_subframe.menu.configure(values=confref.mipmap_levels)
        self.additional_options_subframe.menu.set("none")
