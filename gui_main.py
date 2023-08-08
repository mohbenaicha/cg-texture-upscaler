from tkinter import *
import customtkinter as ctk
from gui.frames.master_frame import MasterFrame


def main():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    master_frame = MasterFrame()
    master_frame.iconbitmap('./media/upscaler.ico')
    master_frame.mainloop()


if __name__ == "__main__":
    main()
