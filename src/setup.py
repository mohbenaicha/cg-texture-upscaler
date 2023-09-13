import sys
from cx_Freeze import setup, Executable

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
    name="CG Texture Studio",
    version="Nill",
    author="Adam Kosha",
    description="",
    options={"build_exe": build_exe_options},
    executables=[Executable("main.py", base=base, icon="upscaler.ico")],
)