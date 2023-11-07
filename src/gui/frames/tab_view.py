from customtkinter import CTkTabview
from app_config.config import GUIConfig

class TabView(CTkTabview):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.add("General")
        self.add("Additional Settings")
        self.configure(height=GUIConfig.tab_view_height)
        self.configure(width=GUIConfig.tab_view_width)
        self.grid(row=0, column=0, padx=10, pady=5)