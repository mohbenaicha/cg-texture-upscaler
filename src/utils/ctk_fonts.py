import customtkinter as ctk
from app_config.config import GUIConfig as GUIConfig


def text_font():
    return ctk.CTkFont(family="Gill Sans MT", size=GUIConfig.textbox_items_fontsize)


def options_font():
    return ctk.CTkFont(family="Gill Sans MT", size=GUIConfig.option_fontsize)


def buttons_font():
    return ctk.CTkFont(family="Gill Sans MT", size=GUIConfig.button_fontsize)


def export_buttons_font():
    return ctk.CTkFont(family="Gill Sans MT", size=GUIConfig.export_button_fontsize)


def list_font():
    return ctk.CTkFont(family="Gill Sans MT", size=GUIConfig.listbox_items_fontsize)


def header_labels_font():
    return ctk.CTkFont(family="Gill Sans MT", size=GUIConfig.header_labels_fontsize)


def labels_font():
    return ctk.CTkFont(family="Gill Sans MT", size=GUIConfig.labels_fontsize)


def image_label_font():
    return ctk.CTkFont(family="Gill Sans MT", size=GUIConfig.labels_fontsize)


def error_font():
    return ctk.CTkFont(family="Gill Sans MT", size=GUIConfig.textbox_items_fontsize)


def main_lb_items_font():
    return ctk.CTkFont(family="Gill Sans MT", size=GUIConfig.main_listbox_items_fontsize)