from tkinter import *
from PIL import ImageTk, Image
import customtkinter as ctk
import gui.ctk_fonts as fonts
from gui.tooltips import Hovertip_Frame
from app_config.config import ExportConfig, ConfigReference, GUIConfig
from utils.events import *
import gui.tooltips.tooltip_text as ttt


class AdditionalOptionsFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        # options variable definitions
        self.height: int = kwargs.get("height")
        self.width: int = kwargs.get("width")
        self.color_mode = ctk.StringVar(value=ExportConfig.export_color_mode)
        self.color_space = ctk.StringVar(value=ExportConfig.color_space)
        self.color_depth = ctk.StringVar(value=ExportConfig.export_color_depth)
        self.device = ctk.StringVar(value=ExportConfig.device)
        self.upscale_precision = ctk.StringVar(value=ExportConfig.upscale_precision)
        self.export_color_depth = ctk.DoubleVar(value=ExportConfig.export_color_depth)
        self.split_large_image = ctk.BooleanVar(value=ExportConfig.split_large_image)
        self.patch_size = ctk.IntVar(value=ExportConfig.patch_size)
        self.gamma_adjustment = ctk.DoubleVar(value=ExportConfig.gamma_adjustment)
        self.broswermodeon = ctk.BooleanVar(value=GUIConfig.browser_mode_on)

        self.setup_frame()
        self.plot_self()
        self.plot_frame_elements()

    def setup_frame(self):
        self.setup_subframes()

    def setup_subframes(self):
        self.generalsettings_label_frame = ctk.CTkFrame(
            self, fg_color="transparent", height=5, width=150
        )
        self.color_depth_subframe = ctk.CTkFrame(
            self, fg_color="transparent", height=10, width=150
        )
        self.color_mode_subframe = ctk.CTkFrame(
            self, fg_color="transparent", height=10, width=150
        )
        self.color_space_subframe = ctk.CTkFrame(
            self, fg_color="transparent", height=10, width=150
        )
        self.gamma_adjustment_subframe = ctk.CTkFrame(
            self, fg_color="transparent", height=10, width=150
        )
        self.device_memory_settings_subframe = ctk.CTkFrame(
            self, fg_color="transparent", height=5, width=150
        )
        self.device_subframe = ctk.CTkFrame(
            self, fg_color="transparent", height=10, width=150
        )
        self.upscale_precision_subframe = ctk.CTkFrame(
            self, fg_color="transparent", height=10, width=150
        )
        self.split_large_images_subframe = ctk.CTkFrame(
            self, fg_color="transparent", height=10, width=150
        )
        self.patch_size_subframe = ctk.CTkFrame(
            self, fg_color="transparent", height=10, width=150
        )

        self.image_browser_subframe = ctk.CTkFrame(
            self, fg_color="transparent", height=10, width=150
        )
        self.setup_subframe_elements()

    def setup_subframe_elements(self):
        # heading labels
        self.generalsettings_label_frame.label = ctk.CTkLabel(
            self.generalsettings_label_frame,
            font=fonts.header_labels_font(),
            text="        General Settings",
            width=1,
        )
        self.device_memory_settings_subframe.label = ctk.CTkLabel(
            self.device_memory_settings_subframe,
            font=fonts.header_labels_font(),
            text="        Export Settings",
            width=1,
        )

        # color depth dropdown
        self.color_depth_subframe.label = ctk.CTkLabel(
            self.color_depth_subframe,
            font=fonts.options_font(),
            text="Export Color Depth (bpc)",
            height=20,
            width=60,
        )
        self.color_depth_subframe.menu = ctk.CTkOptionMenu(
            self.color_depth_subframe,
            values=ConfigReference.supported_color_depth,
            dynamic_resizing=False,
            command=self.set_color_depth,
            variable=self.color_depth,
            height=20,
            width=80,
            font=fonts.buttons_font(),
        )
        self.color_depth_subframe.menu.set(value=ExportConfig.export_color_depth)
        self.color_depth_subframe.menu_tt = Hovertip_Frame(
            anchor_widget=self.color_depth_subframe.label,
            text=ttt.color_depth,
            hover_delay=GUIConfig.tooltip_hover_delay,
            bg_color=GUIConfig.tooltip_color,
            text_color=GUIConfig.tooltop_text_color,
        )

        # color mode label/menu
        self.color_mode_subframe.label = ctk.CTkLabel(
            self.color_mode_subframe,
            font=fonts.options_font(),
            text="Export Color Mode",
            height=20,
            width=60,
        )
        self.color_mode_subframe.menu = ctk.CTkOptionMenu(
            self.color_mode_subframe,
            values=ConfigReference.color_modes,
            dynamic_resizing=False,
            command=self.set_color_mode,
            variable=self.color_mode,
            height=20,
            width=140,
            font=fonts.small_buttons_font(),
        )
        self.color_mode_subframe.menu.set(value=ExportConfig.export_color_mode)
        self.color_mode_subframe.menu_tt = Hovertip_Frame(
            anchor_widget=self.color_mode_subframe.label,
            text=ttt.color_mode,
            hover_delay=GUIConfig.tooltip_hover_delay,
            bg_color=GUIConfig.tooltip_color,
            text_color=GUIConfig.tooltop_text_color,
        )

        # color space label/menu
        self.color_space_subframe.label = ctk.CTkLabel(
            self.color_space_subframe,
            font=fonts.options_font(),
            text="Image Color Space",
            height=20,
            width=50,
        )
        self.color_space_subframe.menu = ctk.CTkOptionMenu(
            self.color_space_subframe,
            values=ConfigReference.supported_color_spaces,
            dynamic_resizing=False,
            command=self.set_color_space,
            variable=self.color_space,
            height=20,
            width=140,
            font=fonts.small_buttons_font(),
        )
        self.color_space_subframe.menu.set(value=ExportConfig.color_space)
        self.color_space_subframe.menu_tt = Hovertip_Frame(
            anchor_widget=self.color_space_subframe.label,
            text=ttt.color_space,
            hover_delay=GUIConfig.tooltip_hover_delay,
            bg_color=GUIConfig.tooltip_color,
            text_color=GUIConfig.tooltop_text_color,
        )

        # device label/menu
        self.device_subframe.label = ctk.CTkLabel(
            master=self.device_subframe,
            font=fonts.options_font(),
            anchor="w",
            text="Export Device",
            height=20,
            width=300,
        )
        self.device_subframe.menu = ctk.CTkOptionMenu(
            master=self.device_subframe,
            dynamic_resizing=False,
            values=ConfigReference.available_devices,
            command=self.set_device,
            variable=self.device,
            height=20,
            width=80,
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
        # upscale precision label/menu
        self.upscale_precision_subframe.label = ctk.CTkLabel(
            self.upscale_precision_subframe,
            font=fonts.options_font(),
            text="Upscale Precision",
            height=20,
            width=50,
        )
        self.upscale_precision_subframe.menu = ctk.CTkOptionMenu(
            master=self.upscale_precision_subframe,
            dynamic_resizing=False,
            values=list(confref.upscale_precision_levels['cuda'].keys()),
            command=self.set_upscale_precision,
            variable=self.upscale_precision,
            height=20,
            width=80,
            font=fonts.buttons_font(),
        )
        
        self.upscale_precision_subframe.menu_tt = Hovertip_Frame(
            anchor_widget=self.upscale_precision_subframe.label,
            text=ttt.upscale_precision,
            hover_delay=GUIConfig.tooltip_hover_delay,
            bg_color=GUIConfig.tooltip_color,
            text_color=GUIConfig.tooltop_text_color,
        )
        # padding size label/slider
        self.patch_size_subframe.label = ctk.CTkLabel(
            self.patch_size_subframe,
            font=fonts.options_font(),
            text=f"Split Size ({ConfigReference.split_sizes[ExportConfig.patch_size][0]})",
            height=20,
            width=50,
        )
        self.patch_size_subframe.slider = ctk.CTkSlider(
            master=self.patch_size_subframe,
            from_=1,
            to=4,
            number_of_steps=3,
            command=self.set_patch_size,
            variable=self.patch_size,
            height=20,
            width=100,
        )
        

        try:
            self.patch_size_subframe.menu_tt = Hovertip_Frame(
                anchor_widget=self.patch_size_subframe.label,
                text=ttt.pad_size,
                hover_delay=GUIConfig.tooltip_hover_delay,
                bg_color=GUIConfig.tooltip_color,
                text_color=GUIConfig.tooltop_text_color,
                image=ImageTk.PhotoImage(Image.open("media\\splitimagesize.jpg"))
                # PhotoImage(file=os.path.join("media", "splitimagesize.jpg"))
        
            )
        except:
            None
        # padding size label/slider
        self.gamma_adjustment_subframe.label = ctk.CTkLabel(
            self.gamma_adjustment_subframe,
            font=fonts.options_font(),
            text=f"Gamma Adjustment {round(ExportConfig.gamma_adjustment,1)}",
            height=20,
            width=50,
        )
        self.gamma_adjustment_subframe.slider = ctk.CTkSlider(
            master=self.gamma_adjustment_subframe,
            from_=0.1,
            to=5.0,
            number_of_steps=49,
            command=self.set_gamma_adjustment,
            variable=self.gamma_adjustment,
            height=20,
            width=100,
        )
        self.set_gamma_adjustment(ExportConfig.gamma_adjustment)

        self.gamma_adjustment_subframe.menu_tt = Hovertip_Frame(
            anchor_widget=self.gamma_adjustment_subframe.label,
            text=ttt.gamma_adjustment,
            hover_delay=GUIConfig.tooltip_hover_delay,
            bg_color=GUIConfig.tooltip_color,
            text_color=GUIConfig.tooltop_text_color,
        )
        # split large images label/checkbox
        self.split_large_images_subframe.label = ctk.CTkLabel(
            master=self.split_large_images_subframe,
            font=fonts.options_font(),
            text="Split and Recombine Large Images",
            height=20,
            width=50,
        )
        self.split_large_images_subframe.checkbox = ctk.CTkCheckBox(
            master=self.split_large_images_subframe,
            variable=self.split_large_image,
            command=lambda: self.set_splitlargeimages(self.split_large_image),
            text="",
            height=15,
            width=40,
            checkbox_height=18,
            checkbox_width=18,
            border_width=2,
        )
        self.split_large_images_subframe.checkbox.select() if ExportConfig.split_large_image else self.split_large_images_subframe.checkbox.deselect()
        self.split_large_images_subframe.checkbox_tt = Hovertip_Frame(
            anchor_widget=self.split_large_images_subframe.label,
            text=ttt.split_large_image,
            hover_delay=GUIConfig.tooltip_hover_delay,
            bg_color=GUIConfig.tooltip_color,
            text_color=GUIConfig.tooltop_text_color,
        )
        #
        self.image_browser_subframe.label = ctk.CTkLabel(
            master=self.image_browser_subframe,
            font=fonts.options_font(),
            text="Image Browser Mode",
            height=20,
            width=50,
        )
        self.image_browser_subframe.checkbox = ctk.CTkCheckBox(
            master=self.image_browser_subframe,
            variable=self.broswermodeon,
            command=lambda: self.set_browsermode(self.broswermodeon),
            text="",
            height=15,
            width=40,
            checkbox_height=18,
            checkbox_width=18,
            border_width=2,
        )
        self.image_browser_subframe.checkbox.select() if GUIConfig.browser_mode_on else self.split_large_images_subframe.checkbox.deselect()
        self.image_browser_subframe.checkbox_tt = Hovertip_Frame(
            anchor_widget=self.image_browser_subframe.label,
            text=ttt.browsermode,
            hover_delay=GUIConfig.tooltip_hover_delay,
            bg_color=GUIConfig.tooltip_color,
            text_color=GUIConfig.tooltop_text_color,
        )

    def set_device(self, value):
        ExportConfig.device = value
        if ExportConfig.device == "cpu":
            self.set_upscale_precision("high")
            disable_UI_elements(self.upscale_precision_subframe.menu)
        else:
            self.set_upscale_precision("normal")
            enable_UI_elements(self.upscale_precision_subframe.menu)

        print(ExportConfig.upscale_precision, ExportConfig.split_large_image, ExportConfig.patch_size)

    def set_color_mode(self, value):
        value = {"RGBA": "RGBA", "RGB":"RGB", "Greyscale+Alpha": "LA", "Greyscale": "L", "Indexed": "Indexed"}[value]
        ExportConfig.export_color_mode = value

    def set_color_space(self, value):
        ExportConfig.color_space = value

    def set_gamma_adjustment(self, value):
        ExportConfig.gamma_adjustment = round(value, 1)
        off = ExportConfig.gamma_adjustment == 1.0
        print_to_frame(
            self.gamma_adjustment_subframe.label,
            grid=False,
            side=LEFT,
            string=f"Gamma Adjustment {round(ExportConfig.gamma_adjustment,1)}"
            if not off
            else "Gamma Adjustment (Off)",
            error=False,
            font=fonts.labels_font(),
            text_color="white",
            lbl_height=15,
            lbl_width=50,
        )

    def set_upscale_precision(self, value):
        ExportConfig.upscale_precision = value
        if ExportConfig.upscale_precision == "high":
            # self.set_patch_size(1)
            try:
                self.upscale_precision_subframe.menu.set("high")
                self.split_large_images_subframe.grid_forget()
                self.patch_size_subframe.grid_forget()
                self.split_large_images_subframe.checkbox.pack_forget(side=RIGHT)
                self.split_large_images_subframe.label.pack_forget(side=LEFT)
                self.patch_size_subframe.label.pack_forget(side=LEFT)
                self.patch_size_subframe.slider.pack_forget(side=RIGHT)
                self.split_large_images_subframe.checkbox.deselect()
                self.set_splitlargeimages(value=False)
            except:
                pass
            
        else:
            try:
                self.split_large_images_subframe.grid(
                    row=9, column=0, padx=35, pady=5, sticky="new"
                )
                self.patch_size_subframe.grid(row=10, column=0, padx=35, pady=5, sticky="new")
                self.split_large_images_subframe.checkbox.pack(side=RIGHT)
                self.split_large_images_subframe.label.pack(side=LEFT)
                self.patch_size_subframe.label.pack(side=LEFT)
                self.patch_size_subframe.slider.pack(side=RIGHT)
                self.upscale_precision_subframe.menu.set("normal")
                self.split_large_images_subframe.checkbox.select()
                self.set_splitlargeimages(value=True)
                self.set_patch_size(ExportConfig.patch_size)
            except:
                pass


    def set_splitlargeimages(self, value):
        try:
            value = (
                value.get()
            )  # the value is a customtkinter object: customtkinter.BooleanVar
        except:
            pass  # the value is a python native datatype: bool
        ExportConfig.split_large_image = value
        print(ExportConfig.split_large_image)
        if not ExportConfig.split_large_image:
            print_to_frame(
            self.patch_size_subframe.label,
            grid=False,
            side=LEFT,
            string="Split Size (disabled)",
            error=False,
            font=fonts.labels_font(),
            text_color="white",
            lbl_height=15,
            lbl_width=50,
            )
            try:disable_UI_elements(self.patch_size_subframe.slider)
            except:pass
        else:
            self.set_patch_size(ExportConfig.patch_size)
            try:
                enable_UI_elements(self.patch_size_subframe.slider)
                print_to_frame(
                self.patch_size_subframe.label,
                grid=False,
                side=LEFT,
                string=f"Split Size ({ConfigReference.split_sizes[ExportConfig.patch_size][0]})",
                error=False,
                font=fonts.labels_font(),
                text_color="white",
                lbl_height=15,
                lbl_width=50,
                )
            except:
                pass

    def set_browsermode(self, value):
        try:
            value = (
                value.get()
            )  # the value is a customtkinter object: customtkinter.BooleanVar
        except:
            pass  # the value is a python native datatype: bool
        GUIConfig.browser_mode_on = value  # self.broswermodeon.get()

    def set_patch_size(self, value):
        ExportConfig.patch_size = str(int(value))
        try:
            print_to_frame(
                self.patch_size_subframe.label,
                grid=False,
                side=LEFT,
                string=f"Split Size ({ConfigReference.split_sizes[ExportConfig.patch_size][0]})",
                error=False,
                font=fonts.labels_font(),
                text_color="white",
                lbl_height=15,
                lbl_width=50,
            )
            self.patch_size_subframe.slider.set(int(ExportConfig.patch_size))
        except:
            pass
            

    def set_color_depth(self, value):
        ExportConfig.export_color_depth = value

    def set_mipmaps(self, value):
        ExportConfig.mipmaps = value.get()

    def plot_self(self):
        self.grid(column=1, row=0, padx=5, pady=10, sticky="new")

    def plot_color_mode_subframe_and_elements(self, menu_options: List[str], set_value: str):
        self.color_mode_subframe.grid_forget()
        self.color_mode_subframe.menu.pack_forget()
        self.color_mode_subframe.label.pack_forget()
        
        self.color_mode_subframe.grid(row=6, column=0, padx=35, pady=5, sticky="new")
        # additional options - mipmaps options menu
        self.color_mode_subframe.label.pack(side=LEFT)
        self.color_mode_subframe.menu.configure(values=menu_options)
        self.color_mode_subframe.menu.pack(side=RIGHT)
        self.color_mode_subframe.menu.set(value=set_value)
        self.color_mode.set(set_value)
        self.set_color_mode(set_value)

    def plot_color_depth_subframe_and_elements(self, menu_options: List[str], set_value: str):
        self.color_depth_subframe.grid(row=4, column=0, padx=35, pady=5, sticky="new")
        # additional options - mipmaps options menu
        self.color_depth_subframe.label.pack(side=LEFT)
        self.color_depth_subframe.menu.pack(side=RIGHT)
        self.color_depth_subframe.menu.configure(values=menu_options)
        self.set_color_depth(set_value)
        self.export_color_depth.set(set_value)
        self.color_depth_subframe.menu.set(set_value)

    def plot_frame_elements(self):
        # plot subframes
        self.generalsettings_label_frame.grid(
            row=0, column=0, padx=38, pady=5, sticky="new"
        )
        self.image_browser_subframe.grid(row=1, column=0, padx=35, pady=5, sticky="new")
        self.device_memory_settings_subframe.grid(
            row=2, column=0, padx=38, pady=5, sticky="new"
        )
        self.device_subframe.grid(row=3, column=0, padx=35, pady=5, sticky="new")
        self.plot_color_depth_subframe_and_elements(['8',], '8')
        self.plot_color_mode_subframe_and_elements(['RGBA', 'RGB', 'Greyscale'], 'RGBA')
        self.gamma_adjustment_subframe.grid(
            row=5, column=0, padx=35, pady=5, sticky="new"
        )
        self.color_mode_subframe.grid(row=6, column=0, padx=35, pady=5, sticky="new")
        self.color_space_subframe.grid(row=7, column=0, padx=35, pady=5, sticky="new")
        self.upscale_precision_subframe.grid(
            row=8, column=0, padx=35, pady=5, sticky="new"
        )
        self.split_large_images_subframe.grid(
            row=9, column=0, padx=35, pady=5, sticky="new"
        )
        self.patch_size_subframe.grid(row=10, column=0, padx=35, pady=5, sticky="new")

        # plot subframe elements

        # Title labels
        self.generalsettings_label_frame.label.grid(
            row=0, column=0, pady=10, padx=20, sticky="ew"
        )
        self.device_memory_settings_subframe.label.grid(
            row=0, column=0, pady=10, padx=20, sticky="ew"
        )

        # browser mode

        self.image_browser_subframe.label.pack(side=LEFT)
        self.image_browser_subframe.checkbox.pack(side=RIGHT)

        # color depth

        self.color_depth_subframe.label.pack(side=LEFT)
        self.color_depth_subframe.menu.pack(side=RIGHT)

        # color mode
        self.color_mode_subframe.label.pack(side=LEFT)
        self.color_mode_subframe.menu.pack(side=RIGHT)

        # scale dropdown
        self.color_space_subframe.label.pack(side=LEFT)
        self.color_space_subframe.menu.pack(side=RIGHT)

        # gamma adjustment slider
        self.gamma_adjustment_subframe.label.pack(side=LEFT)
        self.gamma_adjustment_subframe.slider.pack(side=RIGHT)
        # device
        self.device_subframe.label.pack(side=LEFT)
        self.device_subframe.menu.pack(side=RIGHT)

        # upscale precision
        self.upscale_precision_subframe.label.pack(side=LEFT)
        self.upscale_precision_subframe.menu.pack(side=RIGHT)

        # padding
        self.split_large_images_subframe.checkbox.pack(side=RIGHT)
        self.split_large_images_subframe.label.pack(side=LEFT)

        self.patch_size_subframe.label.pack(side=LEFT)
        self.patch_size_subframe.slider.pack(side=RIGHT)
        
        # setup device
        self.set_upscale_precision(ExportConfig.upscale_precision)
        self.set_patch_size(ExportConfig.patch_size)
        self.set_device("cpu")
