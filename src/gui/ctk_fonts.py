import customtkinter as ctk
from app_config.config import GUIConfig as GUIConfig

text_font = lambda: ctk.CTkFont(family="Gill Sans MT", size=GUIConfig.textbox_items_fontsize)
options_font = lambda: ctk.CTkFont(family="Gill Sans MT", size=GUIConfig.option_fontsize)
smaller_options_font = lambda: ctk.CTkFont(family="Gill Sans MT", size=GUIConfig.smaller_option_fontsize)
buttons_font = lambda: ctk.CTkFont(family="Gill Sans MT", size=GUIConfig.button_fontsize)
small_buttons_font = lambda: ctk.CTkFont(family="Gill Sans MT", size=GUIConfig.small_button_fontsize)
export_buttons_font = lambda: ctk.CTkFont(family="Gill Sans MT", size=GUIConfig.export_button_fontsize)
list_font = lambda: ctk.CTkFont(family="Gill Sans MT", size=GUIConfig.listbox_items_fontsize)
header_labels_font = lambda: ctk.CTkFont(family="Gill Sans MT", size=GUIConfig.header_labels_fontsize)
labels_font = lambda: ctk.CTkFont(family="Gill Sans MT", size=GUIConfig.labels_fontsize)
image_label_font = lambda: ctk.CTkFont(family="Gill Sans MT", size=GUIConfig.labels_fontsize)
error_font = lambda: ctk.CTkFont(family="Gill Sans MT", size=GUIConfig.textbox_items_fontsize)
main_lb_items_font = lambda: ctk.CTkFont(family="Gill Sans MT", size=GUIConfig.main_listbox_items_fontsize)
