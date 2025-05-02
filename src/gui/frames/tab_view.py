from customtkinter import CTkTabview
from app_config.config import GUIConfig
from gui.ctk_fonts import header_labels_font

class TabView(CTkTabview):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.add("General")
        self.add("Additional Settings")
        self.configure(height=GUIConfig.tab_view_height)
        self.configure(width=GUIConfig.tab_view_width)
        self._segmented_button.configure(font=header_labels_font())  # Adjust font size
        self.grid(row=0, column=0, padx=10, pady=5)