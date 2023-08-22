import customtkinter as ctk
from gui.tooltips import Hovertip_Frame
from gui.tooltips import tooltip_text as ttt
import utils.ctk_fonts as fonts
from app_config.config import GUIConfig
from gui.frames.search_filter_frame import SearchFilterFrame
from gui.frames.export_options_frame import ExportOptionsFrame
from gui.frames.export_frame import ExportFrame
from gui.frames.main_listbox_frame import TkListbox
from gui.frames.file_or_folder_frame import FileOrFolderFrame
from gui.frames.top_level_frames import SaveConfigWindow, LoadConfigWindow


class AppAndUIOptions(ctk.CTkFrame):
    def __init__(self, master: ctk.CTk, **kwargs):
        super().__init__(master)
        self.fof_frame: FileOrFolderFrame = kwargs.get("fof_frame")
        self.filter_frame: SearchFilterFrame = kwargs.get("filter_frame")
        self.expopts_frame: ExportOptionsFrame = kwargs.get("expopts_frame")
        self.export_frame: ExportFrame = kwargs.get("export_frame")
        self.configure(width=kwargs.get("width"))
        self.odd = False
        self.lb_frame: TkListbox = kwargs.get("lb_frame")
        self.save_toplevel_window: None | SaveConfigWindow = None
        self.load_toplevel_window: None | LoadConfigWindow = None
        self.setup_subframes()

    def setup_subframes(self):
        self.config_subframe = ctk.CTkFrame(
            master=self, fg_color="transparent", width=1, height=25
        )  # subframe to pack select file and folder buttons
        self.config_subframe.columnconfigure(1, weight=2)
        self.config_subframe.columnconfigure(2, weight=1)

        self.scale_subframe = ctk.CTkFrame(
            master=self, fg_color="transparent", width=1, height=25
        )  # subframe to pack select file and folder buttons
        self.theme_subframe = ctk.CTkFrame(
            master=self, fg_color="transparent", width=1, height=25
        )  # subframe to pack select file and folder buttons

        # configuration
        self.load_conf_button = ctk.CTkButton(
            self.config_subframe,
            text="Load Config",
            command=self.load_config_event,
            width=1,
            height=10,
            font=fonts.buttons_font(),
        )

        self.load_conf_button_tt = Hovertip_Frame(
            anchor_widget=self.load_conf_button,
            text=ttt.load_config,
            hover_delay=GUIConfig.tooltip_hover_delay,
            bg_color=GUIConfig.tooltip_color,
            text_color=GUIConfig.tooltop_text_color,
        )

        self.save_conf_button = ctk.CTkButton(
            self.config_subframe,
            text="Save Config",
            command=self.save_config_event,
            width=1,
            height=10,
            font=fonts.buttons_font(),
        )

        self.save_conf_button_tt = Hovertip_Frame(
            anchor_widget=self.save_conf_button,
            text=ttt.save_config,
            hover_delay=GUIConfig.tooltip_hover_delay,
            bg_color=GUIConfig.tooltip_color,
            text_color=GUIConfig.tooltop_text_color,
        )

        # scale
        self.scale_gui_label = ctk.CTkLabel(
            self.scale_subframe,
            text="GUI Scale",
            width=1,
            height=10,
            font=fonts.labels_font(),
        )
        self.gui_scale: float = 1
        self.increase_gui_scale_button = ctk.CTkButton(
            self.scale_subframe,
            text=" + ",
            width=1,
            command=self.up_scale_gui_event,
            font=fonts.labels_font(),
        )

        self.decrease_gui_scale_button_tt = Hovertip_Frame(
            anchor_widget=self.increase_gui_scale_button,
            text=ttt.increase_gui_scale,
            hover_delay=GUIConfig.tooltip_hover_delay,
            bg_color=GUIConfig.tooltip_color,
            text_color=GUIConfig.tooltop_text_color,
        )

        self.decrease_gui_scale_button = ctk.CTkButton(
            self.scale_subframe,
            text=" - ",
            width=1,
            command=self.down_scale_gui_event,
            font=fonts.labels_font(),
        )

        self.decrease_gui_scale_button_tt = Hovertip_Frame(
            anchor_widget=self.decrease_gui_scale_button,
            text=ttt.decrease_gui_scale,
            hover_delay=GUIConfig.tooltip_hover_delay,
            bg_color=GUIConfig.tooltip_color,
            text_color=GUIConfig.tooltop_text_color,
        )

        # theme
        self.theme_label = ctk.CTkLabel(
            self.theme_subframe,
            text="Appearnace",
            width=1,
            height=10,
            font=fonts.labels_font(),
        )

        self.theme_color = ctk.BooleanVar(value=False)
        self.theme_toggle_switch = ctk.CTkSwitch(
            self.theme_subframe,
            height=10,
            width=10,
            text="",
            command=self.change_theme_event,
            variable=self.theme_color,
        )

        self.theme_toggle_switch_tt = Hovertip_Frame(
            anchor_widget=self.theme_toggle_switch,
            text=ttt.theme,
            hover_delay=GUIConfig.tooltip_hover_delay,
            bg_color=GUIConfig.tooltip_color,
            text_color=GUIConfig.tooltop_text_color,
        )

        # experimental label
        self.expetimental_label = ctk.CTkLabel(
            self, text="(Experimental)", width=1, height=10, font=fonts.labels_font()
        )

        self.plot_self()

    def plot_self(self):
        self.grid(row=4, column=1, padx=5, pady=2, sticky="nesw")
        self.plot_frame_elements()

    def plot_frame_elements(self):
        self.config_subframe.grid(row=2, column=1, sticky="nesw", padx=20, pady=3)
        self.theme_subframe.grid(row=3, column=1, sticky="nesw", padx=5, pady=3)
        self.expetimental_label.grid(row=4, column=1, sticky="nsw", padx=30, pady=1)
        self.scale_subframe.grid(row=5, column=1, sticky="nesw", padx=5, pady=3)

        self.load_conf_button.grid(row=1, column=1, sticky="nesw", padx=5, pady=5)
        self.save_conf_button.grid(row=1, column=2, sticky="nesw", padx=5, pady=5)

        self.scale_gui_label.grid(row=1, column=1, sticky="ew", padx=25, pady=2)
        self.increase_gui_scale_button.grid(
            row=1, column=2, sticky="ew", padx=7, pady=2
        )
        self.decrease_gui_scale_button.grid(
            row=1, column=3, sticky="ew", padx=1, pady=2
        )

        self.theme_label.grid(row=1, column=1, sticky="ew", padx=25, pady=2)
        self.theme_toggle_switch.grid(row=1, column=2, sticky="ew", padx=1, pady=2)

    def load_config_event(self):
        if (
            self.load_toplevel_window is None
            or not self.load_toplevel_window.winfo_exists()
        ):
            self.load_toplevel_window = LoadConfigWindow(
                parent=self,
                fof_frame=self.fof_frame,
                filter_frame=self.filter_frame,
                exp_opts_frame=self.expopts_frame,
                export_frame=self.export_frame,
                lb_frame=self.lb_frame,
            )
            self.load_toplevel_window.attributes("-topmost", 1)
            self.load_toplevel_window.focus_set()
        else:
            self.load_toplevel_window.focus_set()

    def save_config_event(self):
        if (
            self.save_toplevel_window is None
            or not self.save_toplevel_window.winfo_exists()
        ):
            self.save_toplevel_window = SaveConfigWindow()
            self.save_toplevel_window.attributes("-topmost", 1)
            self.save_toplevel_window.focus_set()
        else:
            self.save_toplevel_window.focus_set()

    def change_theme_event(self):
        if self.theme_color.get() == False:
            ctk.set_appearance_mode("dark")
            self.theme_color.set(value=False)
            self.handle_listbox_theme(
                self.lb_frame,
                self.load_toplevel_window.listbox
                if self.load_toplevel_window != None
                else None,
                theme="dark",
            )
        else:
            ctk.set_appearance_mode("light")
            self.theme_color.set(value=True)
            self.handle_listbox_theme(
                self.lb_frame,
                self.load_toplevel_window.listbox
                if self.load_toplevel_window != None
                else None,
                theme="light",
            )

    def handle_listbox_theme(self, image_lb, config_win, theme):
        if theme == "dark":
            image_lb.listbox.configure(
                selectbackground="#4F4F4F",
                fg="#CDCDC0",
                bg=GUIConfig.dark_theme_color,
            )
            image_lb.configure(
                fg_color=GUIConfig.dark_theme_color, bg_color=GUIConfig.dark_theme_color
            )
            image_lb.listbox_scrollbar.configure(fg_color=GUIConfig.dark_theme_color)
            if config_win != None:
                config_win.listbox.configure(
                    selectbackground="#4F4F4F",
                    fg="#CDCDC0",
                    bg=GUIConfig.dark_theme_color,
                )
                config_win.configure(
                    fg_color=GUIConfig.dark_theme_color,
                    bg_color=GUIConfig.dark_theme_color,
                )
                config_win.listbox_scrollbar.configure(
                    fg_color=GUIConfig.dark_theme_color
                )
            GUIConfig.current_theme = "dark"

        elif theme == "light":
            image_lb.listbox.configure(
                selectbackground="#4F4F4F",
                bg=GUIConfig.light_theme_color,
                fg=GUIConfig.dark_theme_color,
            )
            image_lb.configure(
                fg_color=GUIConfig.light_theme_color,
                bg_color=GUIConfig.light_theme_color,
            )
            image_lb.listbox_scrollbar.configure(fg_color=GUIConfig.light_theme_color)

            if config_win != None:
                config_win.listbox.configure(
                    selectbackground="#4F4F4F",
                    bg=GUIConfig.light_theme_color,
                    fg=GUIConfig.dark_theme_color,
                )
                config_win.configure(
                    fg_color=GUIConfig.light_theme_color,
                    bg_color=GUIConfig.light_theme_color,
                )
                config_win.listbox_scrollbar.configure(
                    fg_color=GUIConfig.light_theme_color
                )
            GUIConfig.current_theme = "light"

    # TODO: experimental, needs a new algorithm to match customtkinter
    def scale_tk_listbox(self):
        self.lb_frame.listbox.configure(
            height=int(round(GUIConfig.main_listbox_height * self.gui_scale, 0))
            - (0 if self.odd else 1),
            width=int(round(GUIConfig.main_listbox_width * self.gui_scale, 0))
            - (0 if self.odd else 1),
        )
        if self.load_toplevel_window != None:
            self.load_toplevel_window.listbox.listbox.configure(
                height=int(round(10 * self.gui_scale, 0)) - 1,
                width=int(round(30 * self.gui_scale, 0)) - 1,
            )

    def up_scale_gui_event(self):
        if not self.gui_scale > 1.2:
            self.odd = not self.odd
            self.gui_scale *= 1.1
            ctk.set_window_scaling(self.gui_scale)
            ctk.set_widget_scaling(self.gui_scale)
            # TODO: incorporate into function
            self.scale_tk_listbox()

    def down_scale_gui_event(self):
        if not self.gui_scale < 0.75:
            self.odd = not self.odd
            self.gui_scale *= 0.901
            ctk.set_window_scaling(self.gui_scale)
            ctk.set_widget_scaling(self.gui_scale)
            self.scale_tk_listbox()
