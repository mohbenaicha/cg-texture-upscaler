import sys
from app_config.config import TechnicalConfig as tconf
from cx_Freeze import setup, Executable
sys.setrecursionlimit(5000)

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {
    "excludes": ["auto-py-to-exe", "pyinstaller"],
    "include_msvcr": True,
    "packages": [
    "torch",
    "torchvision", 
    "numpy", 
    "cv2",
    "unittest",
    "skimage",
    "customtkinter", 
    "wand", 
    "yaml", 
    "albumentations", 
    "PIL",
    ]
}

# base="Win32GUI" should be used only for Windows GUI app
base = "Win32GUI" if sys.platform == "win32" else None


setup(
    name=tconf.app_display_name,
    version=tconf.gui_version,
    author=tconf.app_author,
    description="",
    options={"build_exe": build_exe_options},
    executables=[Executable("main.py", base=base, icon="upscaler.ico")],
)